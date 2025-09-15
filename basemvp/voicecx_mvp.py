import os
import json
import datetime
import sounddevice as sd
import wave
import subprocess
import requests

# ========= CONFIG =========
CUSTOMER_ID = "1234"
AUDIO_FILE = f"call_{CUSTOMER_ID}.wav"
OLLAMA_API = "http://localhost:11434/api/generate"  # if using Ollama locally
MISTRAL_API = (
    "https://api.mistral.ai/v1/chat/completions"  # replace with actual endpoint
)
USE_OLLAMA = True  # set False to use Mistral API
MODEL = "mistral"  # or any local Ollama model (e.g. "llama2")
MODEL_OLLAMA = "llama3.2:1b"


# ========= STEP 1: Record Call =========
def record_audio(filename, duration=10, samplerate=16000, device=None):
    print(f"[INFO] Recording audio for {duration} seconds...")
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16",
        device=device,  # force the correct device
    )
    sd.wait()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())
    print(f"[INFO] Audio saved: {filename}")
    return filename


def transcribe_whisper(audio_file):
    print("[INFO] Running Whisper transcription...")
    result = subprocess.run(
        [
            "whisper-cli.exe",
            "-m",
            "whisper.cpp/ggml-tiny.en.bin",  # use tiny.en for now
            "-f",
            audio_file,
            "--no-timestamps",  # no timestamps
            "--print-progress",
            "false",  # disable progress bar/logs
        ],
        capture_output=True,
        text=True,
    )

    if result.stderr:
        print("[ERROR from Whisper]", result.stderr)

    # Filter lines: keep only transcript text (skip logs)
    lines = []
    for line in result.stdout.splitlines():
        if line.strip() and not line.startswith(
            ("whisper_", "system_info", "main:", "[")
        ):
            lines.append(line.strip())

    transcript = " ".join(lines)
    print("[INFO] Transcript generated.")
    return transcript


# ========= STEP 3: Analyze Transcript =========
def analyze_with_llm(transcript):
    prompt = f"""
    You are a CX analysis agent. Given this transcript, extract:
    1. Overall sentiment (positive, neutral, negative).
    2. Main pain points (list).
    3. Was the customer’s requirement fulfilled? (yes/no + reason).
    4. Short summary.

    Transcript:
    {transcript}
    """

    if USE_OLLAMA:
        response = requests.post(
            OLLAMA_API, json={"model": MODEL_OLLAMA, "prompt": prompt}, stream=True
        )

        output_chunks = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output_chunks.append(data["response"])
            except json.JSONDecodeError:
                continue
        output = "".join(output_chunks)

    else:
        headers = {"Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}"}
        response = requests.post(
            MISTRAL_API,
            headers=headers,
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}]},
        )
        output = response.json()["choices"][0]["message"]["content"]

    return output.strip()


# ========= STEP 4: Save Results =========
def save_results(customer_id, transcript, analysis):
    data = {
        "customer_id": customer_id,
        "timestamp": str(datetime.datetime.now()),
        "transcript": transcript,
        "analysis": analysis,
    }
    out_file = f"analysis_{customer_id}.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Results saved: {out_file}")


# ========= MAIN PIPELINE =========
if __name__ == "__main__":
    audio = record_audio(
        AUDIO_FILE, duration=10, device=1
    )  # replace 2 with your mic index
    transcript = transcribe_whisper(audio)
    analysis = analyze_with_llm(transcript)
    save_results(CUSTOMER_ID, transcript, analysis)

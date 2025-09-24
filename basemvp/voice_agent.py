import os
import sounddevice as sd
import wave
import subprocess
import requests
import json
import pyttsx3

# --- Optional: cloud Ollama ---
try:
    from ollama import Client
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    Client = None


# ====== CONFIG ======
AUDIO_FILE = "customer_input.wav"
SAMPLE_RATE = 16000  # safer for whisper.cpp

WHISPER_EXE = r"D:\Project\VoiceCX\voicecx-insights\basemvp\whisper.cpp\build\bin\Release\whisper-cli.exe"
# MODEL_FILE = r"D:\Project\VoiceCX\voicecx-insights\basemvp\whisper.cpp\ggml-tiny.en.bin"
MODEL_FILE = r"D:\Project\VoiceCX\voicecx-insights\basemvp\whisper.cpp\ggml-base.en.bin"


# --- Choose mode ---
USE_LOCAL_OLLAMA = False  # Local Ollama server at http://localhost:11434
USE_CLOUD_OLLAMA = True  # Ollama Cloud API

# Local Ollama
OLLAMA_API = "http://localhost:11434/api/generate"
MODEL_OLLAMA = "llama3.2:1b"

# Cloud Ollama
OLLAMA_KEY = os.getenv("OLLAMA_KEY")
client = None
if USE_CLOUD_OLLAMA and Client is not None and OLLAMA_KEY:
    client = Client(host="https://ollama.com", headers={"Authorization": OLLAMA_KEY})


# ====== TEXT TO SPEECH ======
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# ====== RECORD CUSTOMER VOICE ======
def record_audio(filename, duration=5):
    print(f"[INFO] Listening for {duration} seconds...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return filename


# ====== TRANSCRIBE WITH WHISPER.CPP ======
def transcribe_whisper(audio_file):
    print("[INFO] Running Whisper transcription...")

    audio_path = os.path.abspath(audio_file)
    result = subprocess.run(
        [WHISPER_EXE, "-m", MODEL_FILE, "-f", audio_path, "--no-timestamps"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    raw_output = (result.stdout + "\n" + result.stderr).strip()
    print("[DEBUG] Raw Whisper Output:\n", raw_output[:500])

    if not raw_output:
        raise RuntimeError("Whisper produced no output. Check audio format.")

    # Extract transcript lines
    lines = []
    for line in raw_output.splitlines():
        if line.strip() and not line.startswith(
            ("whisper_", "system_info", "main:", "whisper_print_timings")
        ):
            lines.append(line.strip())

    transcript = " ".join(lines)
    print("[INFO] Transcript generated:", transcript[:200], "...")
    return transcript


# ====== LLM AGENT RESPONSE ======
def get_agent_reply(transcript, context=""):
    prompt = f"""
    You are a polite customer service agent.
    Previous context: {context}
    Customer said: {transcript}
    Respond with a short, helpful reply.
    """

    try:
        # --- Local Ollama ---
        if USE_LOCAL_OLLAMA:
            with requests.post(
                OLLAMA_API,
                json={"model": MODEL_OLLAMA, "prompt": prompt},
                stream=True,
            ) as resp:
                resp.raise_for_status()
                chunks = []
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        if "response" in data:
                            chunks.append(data["response"])
                    except json.JSONDecodeError:
                        continue
                return "".join(chunks).strip()

        # --- Cloud Ollama ---
        elif USE_CLOUD_OLLAMA and client:
            messages = [{"role": "user", "content": prompt}]
            response_text = []
            for part in client.chat("gpt-oss:120b", messages=messages, stream=True):
                response_text.append(part["message"]["content"])
            return "".join(response_text).strip()

        else:
            return "No LLM backend is configured."

    except Exception as e:
        print("[ERROR in LLM call]", e)
        return "Sorry, I could not generate a reply right now."


# ====== MAIN LOOP ======
def run_agent():
    print("🤖 Voice Agent Started. Press Ctrl+C to stop.")
    context = "Initial greeting"
    speak_text("Hello, I am your customer support assistant. How are you today?")

    for i in range(3):  # max 3 exchanges
        audio = record_audio(AUDIO_FILE, duration=6)
        customer_text = transcribe_whisper(audio)
        print(f"👤 Customer: {customer_text}")

        agent_reply = get_agent_reply(customer_text, context)
        print(f"🤖 Agent: {agent_reply}")
        speak_text(agent_reply)

        context += f"\nCustomer: {customer_text}\nAgent: {agent_reply}"

    speak_text("Thank you for your time. Goodbye.")


if __name__ == "__main__":
    run_agent()

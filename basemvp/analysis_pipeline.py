import os
import sounddevice as sd
import wave
import subprocess
import requests
import json
import pyttsx3
import uuid
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client

# ====== CONFIG ======
AUDIO_FILE = "customer_input.wav"
SAMPLE_RATE = 16000

WHISPER_EXE = r"D:\Project\VoiceCX\voicecx-insights\basemvp\whisper.cpp\build\bin\Release\whisper-cli.exe"
MODEL_FILE = r"D:\Project\VoiceCX\voicecx-insights\basemvp\whisper.cpp\ggml-base.en.bin"

# Load API key
load_dotenv()
OLLAMA_KEY = os.getenv("OLLAMA_KEY")
if not OLLAMA_KEY:
    raise RuntimeError("❌ Missing OLLAMA_KEY in .env")

# Cloud Ollama client
client = Client(host="https://ollama.com", headers={"Authorization": OLLAMA_KEY})

MODEL_AGENT = "gpt-oss:120b"  # for replies
MODEL_ANALYSIS = "gpt-oss:120b"  # for structured analysis


# ====== TEXT TO SPEECH ======
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# ====== RECORD AUDIO ======
def record_audio(filename, duration=5):
    print(f"[INFO] Listening for {duration} seconds...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
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
    if not raw_output:
        raise RuntimeError("Whisper produced no output. Check audio format.")

    lines = []
    for line in raw_output.splitlines():
        if line.strip() and not line.startswith(
            ("whisper_", "system_info", "main:", "whisper_print_timings")
        ):
            lines.append(line.strip())

    transcript = " ".join(lines)
    print("[INFO] Transcript generated:", transcript[:200], "...")
    return transcript


# ====== CLOUD LLM REPLY ======
def get_agent_reply(transcript, context=""):
    prompt = f"""
    You are a polite customer service agent.
    Previous context: {context}
    Customer said: {transcript}
    Respond with a short, helpful reply.
    """

    response_text = []
    for part in client.chat(
        MODEL_AGENT, messages=[{"role": "user", "content": prompt}], stream=True
    ):
        response_text.append(part["message"]["content"])
    return "".join(response_text).strip()


# ====== ANALYSIS PIPELINE ======
def analyze_transcript(transcript, customer_id="C101", campaign="Test Campaign"):
    call_id = f"CALL_{uuid.uuid4().hex[:8]}"

    prompt = f"""
    You are a JSON generator.
    Do not explain. Do not write markdown. 
    Respond ONLY with a single valid JSON object matching this schema:

    {{
      "call_id": "string",
      "customer_id": "string",
      "campaign": "string",
      "timestamp": "string (ISO 8601)",
      "transcript": "string",
      "analysis": {{
        "sentiment": "happy|neutral|angry|doubtful|confused|sad",
        "intents": ["list of strings"],
        "entities": ["list of strings"],
        "pain_points": ["list of strings"],
        "outcome": "fulfilled|unfulfilled|unclear",
        "churn_score": float
      }}
    }}

    Fill in the fields based on this transcript:
    {transcript}
    """

    response_text = []
    for part in client.chat(
        MODEL_ANALYSIS,
        messages=[{"role": "user", "content": prompt}],
        options={"stop": ["```", "</s>"]},  # cut off junk
        stream=True,
    ):
        response_text.append(part["message"]["content"])

    raw_output = "".join(response_text).strip()
    print("[DEBUG] Raw analysis output:", raw_output[:300])  # optional debug

    # --- Try parsing JSON ---
    try:
        analysis_json = json.loads(raw_output)
    except json.JSONDecodeError:
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1:
            try:
                analysis_json = json.loads(raw_output[start : end + 1])
            except Exception:
                print("[ERROR] Could not parse extracted block.")
                analysis_json = {}
        else:
            print("[ERROR] No JSON found at all.")
            analysis_json = {}

    # --- Ensure required fields exist ---
    analysis_json.setdefault("call_id", call_id)
    analysis_json.setdefault("customer_id", customer_id)
    analysis_json.setdefault("campaign", campaign)
    analysis_json.setdefault("timestamp", datetime.now().isoformat())
    analysis_json.setdefault("transcript", transcript)
    analysis_json.setdefault(
        "analysis",
        {
            "sentiment": "unclear",
            "intents": [],
            "entities": [],
            "pain_points": [],
            "outcome": "unclear",
            "churn_score": 0.0,
        },
    )

    # Save result
    out_file = f"analysis_{call_id}.json"
    with open(out_file, "w") as f:
        json.dump(analysis_json, f, indent=2)

    return analysis_json


# ====== MAIN LOOP ======
def run_agent(customer_id="C555", campaign="Delivery Feedback"):
    print("🤖 Voice Agent Started (Cloud Ollama). Press Ctrl+C to stop.")
    context = "Initial greeting"
    speak_text("Hello, I am your customer support assistant. How are you today?")

    full_transcript = []

    for i in range(2):  # demo: 2 exchanges
        audio = record_audio(AUDIO_FILE, duration=6)
        try:
            customer_text = transcribe_whisper(audio)
        except Exception as e:
            print("[ERROR in transcription]", e)
            customer_text = ""

        print(f"👤 Customer: {customer_text}")
        full_transcript.append(f"Customer: {customer_text}")

        agent_reply = get_agent_reply(customer_text, context)
        print(f"🤖 Agent: {agent_reply}")
        speak_text(agent_reply)

        full_transcript.append(f"Agent: {agent_reply}")
        context += f"\nCustomer: {customer_text}\nAgent: {agent_reply}"

    speak_text("Thank you for your time. Goodbye.")

    # ===== Structured Analysis =====
    transcript_text = " ".join(full_transcript)
    analysis = analyze_transcript(
        transcript_text, customer_id=customer_id, campaign=campaign
    )
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    run_agent()

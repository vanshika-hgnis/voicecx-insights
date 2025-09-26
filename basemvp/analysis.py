import requests
import json

OLLAMA_API = "http://localhost:11434/api/generate"


def analyze_transcript(transcript, call_id="CALL_001", customer_id="C101"):
    prompt = f"""
    Analyze the following customer call transcript.

    Tasks:
    1. Sentiment (choose: happy, neutral, angry, doubtful, confused, sad).
    2. Intents (complaint, refund, cancel, support, feedback).
    3. Entities (e.g., delivery, billing, product).
    4. Pain points (list main problems).
    5. Outcome: fulfilled / unfulfilled / unclear.
    6. Churn risk score (0.0–1.0, higher = more likely to leave).

    Transcript:
    {transcript}
    """

    response = requests.post(
        OLLAMA_API, json={"model": "gemma3:4b", "prompt": prompt}, stream=False
    )

    analysis_text = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    analysis_text += data["response"]
            except json.JSONDecodeError:
                continue  # ignore malformed chunks

    result = {
        "call_id": call_id,
        "customer_id": customer_id,
        "transcript": transcript,
        "analysis": analysis_text.strip(),
    }

    out_file = f"analysis_{call_id}.json"
    with open(out_file, "w") as f:
        json.dump(result, f, indent=2)

    return result


# Example usage
transcript = (
    "I am very upset because my delivery was late and I still didn’t get my refund."
)
res = analyze_transcript(transcript)
print(json.dumps(res, indent=2))

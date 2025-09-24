from ollama import Client
import os
from load_dotenv import load_dotenv

load_dotenv()
OLLAMA_KEY = os.getenv("OLLAMA_KEY")
client = Client(host="https://ollama.com", headers={"Authorization": OLLAMA_KEY})

messages = [
    {
        "role": "user",
        "content": "Why is the sky blue?",
    },
]

for part in client.chat("gpt-oss:120b", messages=messages, stream=True):
    print(part["message"]["content"], end="", flush=True)

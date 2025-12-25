import os
from twilio.rest import Client

from dotenv import load_dotenv


load_dotenv()


account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
print(auth_token)
client = Client(account_sid, auth_token)

TWILIO_NUMBER = "+1 989 349 8847"  # your Twilio number
# https://3c5e11444269.ngrok-free.app
SURVEY_URL = "https://3c5e11444269.ngrok-free.app/voice/survey/start"
STATUS_URL = "https://3c5e11444269.ngrok-free.app/voice/status-callback"

phone_numbers = ["+919631744818", "+919304836199"]


for phone in phone_numbers:
    call = client.calls.create(
        from_=TWILIO_NUMBER,
        to=phone,
        url=SURVEY_URL,
        status_callback=STATUS_URL,
        status_callback_event=["completed", "answered", "ringing"],
    )

    print("Call triggered:", phone, call.sid)

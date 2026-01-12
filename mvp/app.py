from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

TWILIO_NUMBER = "+1 989 349 8847"


@app.route("/admin/calls/start", methods=["POST"])
def start_calls():

    phones_raw = request.form.get("phones", "")
    phones = [p.strip() for p in phones_raw.splitlines() if p.strip()]

    if not phones:
        return "No phone numbers provided", 400

    base_url = request.host_url.rstrip("/")

    survey_url = f"{base_url}/voice/survey/start"
    status_url = f"{base_url}/voice/status-callback"

    results = []

    for phone in phones:
        try:
            call = client.calls.create(
                from_=TWILIO_NUMBER,
                to=phone,
                url=survey_url,
                status_callback=status_url,
                status_callback_event=["answered", "completed"],
            )
            results.append((phone, call.sid))
        except Exception as e:
            results.append((phone, str(e)))

    html = "<h3>Call Trigger Results</h3><ul>"
    for phone, result in results:
        html += f"<li>{phone} → {result}</li>"
    html += "</ul><a href='/admin/calls'>Back</a>"

    return html

# VoiceCX Insights

“We catch customer pain in real-time before they churn.”

VoiceCX Insights is an **AI-powered Voice of Customer (VoC) platform** designed to analyze customer sentiment from voice interactions and provide actionable insights via an interactive dashboard.

MVP goal

“Call numbers → ask 2–3 questions → capture keypad responses → save to DB”

Technology choices

Twilio Voice

Webhook (Node.js / Express OR Python Flask)

SQLite / simple JSON / MySQL

numbers.py
|
call_trigger.py ---> Twilio Calls API
|
v
/voice (Flask)
|
/q1 -> /q2
|
SQLite (responses + call status)
^
/call-status (callback)

# Set up

Minimal end-to-end test (recommended)

1. Start the server

From the project root (where this file exists):

env\Scripts\activate
python app.py

Expected:

Running on http://127.0.0.1:5000

Health check in browser:

http://127.0.0.1:5000/

You must see:

Survey Voice Webhook Running

2. Start ngrok (required for Twilio)

In a new terminal:

ngrok http 5000

Copy the HTTPS URL, for example:

https://abc123.ngrok-free.app

3. Configure Twilio phone number

Twilio Console → Phone Number → Voice

Incoming Call

POST https://abc123.ngrok-free.app/voice/survey/start

Status Callback

POST https://abc123.ngrok-free.app/voice/status-callback

Save.

4. Ensure at least one survey question exists

Open in browser:

http://127.0.0.1:5000/admin/questions

Add a question like:

How was your experience today?

If no questions exist, the call will end immediately.

5. Call the Twilio number

What should happen:

Call connects

Question is spoken

Beep

You speak

Next question (if exists)

Final goodbye

6. Verify data was saved

Run this in a Python shell:

import sqlite3
conn = sqlite3.connect("survey.db")
c = conn.cursor()
c.execute("SELECT call_sid, question, recording_url, transcription FROM survey_responses")
for r in c.fetchall():
print(r)
conn.close()

You should see rows.

Isolated testing (no Twilio call)
A. Test webhook manually (server only)
curl -X POST http://127.0.0.1:5000/voice/survey/start

You should receive XML (TwiML) in response.

B. Test transcription handler manually
curl -X POST http://127.0.0.1:5000/voice/survey/transcription ^
-d "CallSid=TEST123" ^
-d "RecordingUrl=https://test.url" ^
-d "TranscriptionText=Hello this is a test"

Then check DB.

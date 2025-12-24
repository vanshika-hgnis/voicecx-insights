# VoiceCX Insights

“We catch customer pain in real-time before they churn.”

VoiceCX Insights is an **AI-powered Voice of Customer (VoC) platform** designed to analyze customer sentiment from voice interactions and provide actionable insights via an interactive dashboard.

MVP goal

“Call numbers → ask 2–3 questions → capture keypad responses → save to DB”

Technology choices

Twilio Voice

Webhook (Node.js / Express OR Python Flask)

SQLite / simple JSON / MySQL

DTMF input (Press 1, 2, 3)

Phone Number List
|
v
Twilio Outbound Call
|
v
Twilio hits your Webhook
|
v
Ask Question (TwiML)
|
v
User presses key
|
v
Save response to DB
|
v
Next Question / End Call

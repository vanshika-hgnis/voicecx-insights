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

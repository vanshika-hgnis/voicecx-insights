Below is a clean, production-grade **README.md** tailored to your current codebase, covering **setup**, **end-to-end workflow**, **testing**, and **future roadmap**, without meta commentary.

---

# Voice Survey Automation (Flask + Twilio)

Automated outbound voice survey system using **Flask**, **Twilio Voice**, and **SQLite**.
Supports question-by-question voice recording, call logging, transcription storage, and a lightweight admin UI.

---

## Stack Overview

- **Backend**: Python, Flask
- **Telephony**: Twilio Voice API
- **Database**: SQLite
- **Tunneling (local dev)**: ngrok
- **ORM**: Raw SQLite (no ORM)
- **Transcription**: Twilio (current), pluggable for offline/background engines

---

## Repository Structure

```
surveyautomation/
├── app.py              # Flask app, Twilio webhooks, admin UI
├── dialer.py           # Outbound call trigger script
├── init_db.py          # Database schema initialization
├── survey.db           # SQLite database (generated)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── .gitignore
└── env/                # Python virtual environment
```

---

## Environment Variables

Create a `.env` file in the root directory:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxx
```

---

## Installation & Setup

### 1. Clone and Create Virtual Environment

```bash
git clone <repo-url>
cd surveyautomation
python -m venv env
env\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
python init_db.py
```

Creates:

- `survey_questions`
- `survey_responses`
- `call_logs`

---

## Running the Application

### 1. Start Flask Server

```bash
python app.py
```

Runs on:

```
http://localhost:5000
```

### 2. Expose via ngrok

```bash
ngrok http 5000
```

Copy the generated HTTPS URL.

---

## Configure Dialer

Update **dialer.py**:

```python
SURVEY_URL = "https://<ngrok-id>.ngrok-free.app/voice/survey/start"
STATUS_URL = "https://<ngrok-id>.ngrok-free.app/voice/status-callback"
```

Set:

```python
TWILIO_NUMBER = "+1XXXXXXXXXX"
phone_numbers = ["+91XXXXXXXXXX"]
```

---

## Trigger Survey Calls

```bash
python dialer.py
```

Each number receives:

1. Call initiation
2. First survey question
3. Voice recording per question
4. Automatic progression
5. Call termination after last question

---

## Survey Flow (Runtime)

1. **dialer.py**

   - Triggers outbound calls

2. **/voice/survey/start**

   - Fetches first active question

3. **VoiceResponse.Record**

   - Records user response

4. **/voice/survey/voice-answer**

   - Saves recording URL

5. **ask_next_question**

   - Loops until no questions remain

6. **/voice/survey/transcription**

   - Stores Twilio transcription (optional)

---

## Admin Interface

### View & Add Questions

```
GET  /admin/questions
POST /admin/questions/add
```

Supports:

- Adding new survey questions
- Activating/deactivating questions (via DB)

---

## Database Schema (Current)

### survey_questions

- id
- question_text
- expected_input
- is_active

### survey_responses

- call_sid
- phone
- question
- answer / recording_url
- created_at

### call_logs

- call_sid
- phone
- status
- recording_url
- transcription

---

## Testing Checklist

- Flask server reachable via ngrok
- Twilio webhook URLs accessible
- Call connects and plays first question
- Voice recorded per question
- Responses saved in `survey.db`
- Admin UI lists questions correctly
- Status callbacks logged

---

## Known Design Decisions

- SQLite chosen for simplicity and portability
- No ORM for full control over schema
- Twilio transcription enabled but optional
- Relative URLs used for webhook portability

---

## Future Enhancements Roadmap

### Phase 1 – Recording Management

- Admin UI for:

  - Playback
  - Download
  - Call-wise grouping

- Secure access control

### Phase 2 – Offline Transcription

- Background worker for:

  - Whisper / Vosk
  - Batch processing

- Remove dependency on Twilio transcription

### Phase 3 – Analytics & Reporting

- Per-question completion rates
- Average response length
- Call success/failure dashboard
- CSV / Excel export

### Phase 4 – Input Modes

- Mixed DTMF + Voice flows
- Question-level input configuration
- Retry and timeout handling

### Phase 5 – Production Hardening

- PostgreSQL migration
- Auth middleware for admin routes
- Dockerization
- Retry-safe webhook handling
- Queue-based async processing

---

## Health Check

```
GET /
```

Response:

```
Survey Voice Webhook Running
```

---

## License

Internal / Prototype
Production licensing to be defined.

---

# USAGE

Step 1: Start Backend
python app.py

Flask server starts on port 5000.

Step 2: Expose with ngrok
ngrok http 5000

Twilio requires public HTTPS URLs.

Step 3: Trigger Calls
python dialer.py

For each phone number:

Twilio places call

Hits survey start webhook

Step 4: Live Call Flow

User receives call

Question spoken

User answers by voice

Recording saved

Next question asked

Loop until finished

Call ends

Step 5: Data Storage

During call:

survey_responses populated

call_logs updated

Transcriptions optionally saved

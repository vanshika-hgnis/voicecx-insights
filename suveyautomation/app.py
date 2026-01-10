from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather, Record
import sqlite3
from flask import send_file
import os
from io import BytesIO
import requests


app = Flask(__name__)


def ask_next_question(prev_qid):

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, question_text
        FROM survey_questions
        WHERE id > ?
        AND is_active = 1
        ORDER BY id ASC LIMIT 1
        """,
        (prev_qid,),
    )
    q = c.fetchone()
    conn.close()

    vr = VoiceResponse()

    if not q:
        vr.say("Thank you. Your feedback has been recorded. Goodbye.")
        vr.hangup()
        return Response(str(vr), mimetype="text/xml")

    next_id, text = q

    vr.say(text)

    vr.record(
        play_beep=True,
        max_length=60,
        action=f"/voice/survey/voice-answer?question_id={next_id}",
        method="POST",
        transcribe=True,
        transcribe_callback="/voice/survey/transcription",
    )

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/survey/transcription", methods=["POST"])
def transcription_handler():

    call_sid = request.form.get("CallSid")
    transcription_text = request.form.get("TranscriptionText")
    recording_url = request.form.get("RecordingUrl")

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        UPDATE survey_responses
        SET transcription = ?
        WHERE call_sid = ?
        AND recording_url = ?
        """,
        (transcription_text, call_sid, recording_url),
    )
    conn.commit()
    conn.close()

    return "OK", 200


@app.route("/voice/status-callback", methods=["POST"])
def call_status():
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    status = request.form.get("CallStatus")

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO call_logs(call_sid, phone, status)
        VALUES (?, ?, ?)
        """,
        (call_sid, phone, status),
    )
    conn.commit()
    conn.close()

    return "OK", 200


def save_response(call_sid, phone, question, answer):
    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO survey_responses(call_sid, phone, question, answer)
        VALUES (?, ?, ?, ?)
    """,
        (call_sid, phone, question, answer),
    )
    conn.commit()
    conn.close()


def log_call_status(call_sid, phone, status):
    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO call_logs(call_sid, phone, status)
        VALUES (?, ?, ?)
    """,
        (call_sid, phone, status),
    )
    conn.commit()
    conn.close()


@app.route("/voice/survey/start", methods=["POST"])
def survey_start():

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, question_text
        FROM survey_questions
        WHERE is_active = 1
        ORDER BY id ASC LIMIT 1
    """
    )
    q = c.fetchone()
    conn.close()

    question_id, text = q

    vr = VoiceResponse()

    vr.say(text)

    vr.record(
        play_beep=True,
        max_length=60,
        action=f"/voice/survey/voice-answer?question_id={question_id}",
        method="POST",
        transcribe=True,
        transcribe_callback="/voice/survey/transcription",
    )

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/survey/voice-answer", methods=["POST"])
def voice_answer():

    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    recording_url = request.form.get("RecordingUrl")
    question_id = request.args.get("question_id")

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO survey_responses(call_sid, phone, question, recording_url)
        VALUES (?, ?, ?, ?)
        """,
        (call_sid, phone, f"Q{question_id}", recording_url),
    )
    conn.commit()
    conn.close()

    return ask_next_question(question_id)


@app.route("/voice/survey/answer", methods=["GET", "POST"])
def save_answer():
    form = request.values
    print("ANSWER HOOK HIT:", dict(request.form))

    call_sid = form.get("CallSid")
    phone = form.get("To")
    answer = form.get("Digits")
    question_id = request.args.get("question_id")

    if answer is None or answer == "":
        print("No digits received — ignoring")
        return "OK", 200

    # Convert to integer to avoid lexicographical ordering
    qid = int(question_id)

    # --- Save response immediately ---
    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO survey_responses(call_sid, phone, question, answer)
        VALUES (?, ?, ?, ?)
        """,
        (call_sid, phone, f"Q{qid}", answer),
    )
    conn.commit()
    conn.close()

    print(f"SAVED → Q{qid} = {answer}")

    # --- Load next question ---
    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        SELECT id, question_text
        FROM survey_questions
        WHERE id > ?
        AND is_active = 1
        ORDER BY id ASC
        LIMIT 1
        """,
        (qid,),
    )
    q = c.fetchone()
    conn.close()

    vr = VoiceResponse()

    # --- End of survey ---
    if not q:
        vr.say("Thank you for your feedback. Goodbye.")
        vr.hangup()
        return Response(str(vr), mimetype="text/xml")

    next_id, text = q

    base = request.host_url.rstrip("/")

    gather = Gather(
        num_digits=1,
        input="dtmf",
        method="POST",
        action=f"{base}/voice/survey/answer?question_id={next_id}",
    )

    gather.say(text)
    vr.append(gather)

    return Response(str(vr), mimetype="text/xml")


@app.route("/")
def health():
    return "Survey Voice Webhook Running"


@app.route("/recording/play/<path:recording_sid>")
def play_recording(recording_sid):

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Recordings/{recording_sid}"

    r = requests.get(url, auth=(account_sid, auth_token))

    if r.status_code != 200:
        return f"Error fetching recording: {r.text}", 500

    return send_file(
        BytesIO(r.content), mimetype="audio/wav", download_name=f"{recording_sid}.wav"
    )


@app.route("/voice/record-only", methods=["GET", "POST"])
def record_only():
    """
    Simple flow:
    - Say a short intro
    - Start recording after beep
    - On finish, Twilio hits /voice/recording-done
    """

    vr = VoiceResponse()

    vr.say(
        "Thank you for taking this automated feedback call. "
        "Your voice will be recorded after the beep. "
        "Please share your feedback and then you may hang up."
    )

    vr.record(
        max_length=90,
        play_beep=True,
        action="/voice/recording-done",  # relative URL is OK with ngrok
        method="POST",
        transcribe=True,
        transcribe_callback="/voice/transcription-complete",
    )

    # If user never records, Twilio will still continue here after timeout
    vr.say("We did not receive any message. Goodbye.")
    vr.hangup()

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/recording-done", methods=["POST"])
def recording_done():
    """
    Called after the Record verb completes.
    We get RecordingUrl + CallSid here.
    """

    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    recording_url = request.form.get("RecordingUrl")

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        UPDATE call_logs
        SET recording_url = ?
        WHERE call_sid = ?
        """,
        (recording_url, call_sid),
    )
    conn.commit()
    conn.close()

    vr = VoiceResponse()
    vr.say("Thank you. Your feedback has been recorded. Goodbye.")
    vr.hangup()

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/transcription-complete", methods=["POST"])
def transcription_complete():
    """
    If Twilio transcription is enabled, this will receive TranscriptionText.
    """

    call_sid = request.form.get("CallSid")
    transcription_text = request.form.get("TranscriptionText")

    if not call_sid:
        return "OK", 200  # nothing to do

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute(
        """
        UPDATE call_logs
        SET transcription = ?
        WHERE call_sid = ?
        """,
        (transcription_text, call_sid),
    )
    conn.commit()
    conn.close()

    return "OK", 200


### UI


@app.route("/admin/questions")
def admin_questions():
    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute("SELECT id, question_text FROM survey_questions WHERE is_active=1")
    rows = c.fetchall()
    conn.close()

    html = "<h3>Survey Questions</h3>"

    for r in rows:
        html += f"<p>{r[0]} — {r[1]}</p>"

    html += """
    <form method='POST' action='/admin/questions/add'>
        <input name='text' placeholder='Enter question text' />
        <button type='submit'>Add</button>
    </form>
    """

    return html


@app.route("/admin/questions/add", methods=["POST"])
def add_question():
    q = request.form.get("text")

    conn = sqlite3.connect("survey.db")
    c = conn.cursor()
    c.execute("INSERT INTO survey_questions(question_text) VALUES (?)", (q,))
    conn.commit()
    conn.close()

    return "Question added. <a href='/admin/questions'>Back</a>"


if __name__ == "__main__":
    app.run(port=5000, debug=True)

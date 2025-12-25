from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import sqlite3

app = Flask(__name__)


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
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")

    vr = VoiceResponse()

    gather = Gather(
        num_digits=1, action="/voice/survey/q1-response", method="POST", input="dtmf"
    )

    gather.say(
        "Thank you for your time. "
        "Are you satisfied with our service? "
        "Press 1 for Yes. Press 2 for No."
    )

    vr.append(gather)

    vr.say("We did not receive input. Goodbye.")
    vr.hangup()

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/survey/q1-response", methods=["POST"])
def handle_q1():
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    digit = request.form.get("Digits")

    save_response(call_sid, phone, "Q1_Satisfaction", digit)

    vr = VoiceResponse()

    if digit == "1":
        gather = Gather(
            num_digits=1, action="/voice/survey/q2-yes", method="POST", input="dtmf"
        )
        gather.say("Thank you. " "Please rate our service from 1 to 5.")
        vr.append(gather)

    elif digit == "2":
        gather = Gather(
            num_digits=1, action="/voice/survey/q2-no", method="POST", input="dtmf"
        )
        gather.say(
            "We are sorry for your experience. "
            "Press 1 for quality issue. "
            "Press 2 for service delay. "
            "Press 3 for other reason."
        )
        vr.append(gather)

    else:
        vr.say("Invalid input. Goodbye.")

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/survey/q2-yes", methods=["POST"])
def handle_q2_yes():
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    digit = request.form.get("Digits")

    save_response(call_sid, phone, "Q2_Rating_YesFlow", digit)

    vr = VoiceResponse()
    vr.say("Thank you for your valuable feedback.")
    vr.hangup()

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/survey/q2-no", methods=["POST"])
def handle_q2_no():
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    digit = request.form.get("Digits")

    save_response(call_sid, phone, "Q2_Complaint_NoFlow", digit)

    vr = VoiceResponse()
    vr.say("Thank you. Our support team will review your response.")
    vr.hangup()

    return Response(str(vr), mimetype="text/xml")


@app.route("/voice/status-callback", methods=["POST"])
def call_status():
    call_sid = request.form.get("CallSid")
    phone = request.form.get("To")
    status = request.form.get("CallStatus")

    log_call_status(call_sid, phone, status)

    return "OK", 200


@app.route("/")
def health():
    return "Survey Voice Webhook Running"


if __name__ == "__main__":
    app.run(port=5000, debug=True)

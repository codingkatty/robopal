import imaplib
import smtplib
import os
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
from flask import Flask, request, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)

IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL = os.environ.get('EMAIL')
PASSWORD = os.environ.get('PASSWORD')

genai.configure(api_key=os.environ.get('API_KEY'))
model = genai.GenerativeModel("gemini-1.5-flash")

def check_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')

        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()
        print(email_ids)

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    email_from = msg['from']
                    email_subject = msg['subject']

                    send_reply(email_from, email_subject, msg)

        mail.logout()
    except Exception as e:
        print(f"Error checking emails: {e}")

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()

def send_reply(to_email, subject, msg):
    try:
        msg_reply = MIMEMultipart()
        msg_reply['From'] = EMAIL
        msg_reply['To'] = to_email
        msg_reply['Subject'] = 'Re: ' + subject

        email_body = get_email_body(msg)
        response = model.generate_content(
            "Write a reply to the following email as a friend. You're Sarah, a friendly and charming girl. Here's the email:\n" + email_body
        )

        reply_body = response.text
        msg_reply.attach(MIMEText(reply_body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        text = msg_reply.as_string()
        server.sendmail(EMAIL, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Error sending reply: {e}")

@app.route('/welcome', methods=['POST'])
def send_welcome_email():
    data = request.get_json()
    to_email = data.get('to_email')
    subject = data.get('subject', 'No Subject')
    message = data.get('message', '')

    if not to_email:
        return jsonify({'error': 'Recipient email is required'}), 400

    send_email(to_email, subject, message)
    return jsonify({'message': 'Email sent successfully'}), 200

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_emails, trigger="interval", minutes=2)
    scheduler.start()
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
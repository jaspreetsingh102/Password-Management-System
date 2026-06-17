"""
Simple SMTP Email Sender Module
Easy to use - just call send_email with recipient, subject, and message
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string


def generate_verification_code(length=6):
    """Generate a random 6-digit code"""
    return ''.join(random.choices(string.digits, k=length))


def send_email(to_email, subject, body,
               smtp_server="smtp.gmail.com",
               smtp_port=587,
               sender_email="jaspreetsingh88995@gmail.com",
               sender_password="nrds jhpi fsht ufnr"):

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        server.login(sender_email, sender_password)

        server.sendmail(sender_email, to_email, msg.as_string())

        server.quit()

        return True

    except Exception as e:
        print("Email Error:", e)
        return False


def send_verification_code(to_email, code,
                           smtp_server='smtp.gmail.com',
                           smtp_port=587,
                           sender_email='jaspreetsingh88995@gmail.com',
                           sender_password='nrds jhpi fsht ufnr'):
    """
    Send a verification code email
    """

    subject = "🔐 Passman Verification Code"

    body = f"""Your Passman verification code is:

{code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Passman Team
"""

    return send_email(to_email, subject, body,
                      smtp_server, smtp_port,
                      sender_email, sender_password)


if __name__ == "__main__":
    code = generate_verification_code()
    print(f"Generated code: {code}")
    print("Email module ready!")
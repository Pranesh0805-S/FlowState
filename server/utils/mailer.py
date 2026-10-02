import os
import smtplib
from email.message import EmailMessage
from typing import Tuple


def send_otp_email(email: str, otp_code: str) -> Tuple[bool, str]:
    sender = os.getenv("PRODUCTIVITY_SMTP_EMAIL", "")
    app_password = os.getenv("PRODUCTIVITY_SMTP_APP_PASSWORD", "")
    host = os.getenv("PRODUCTIVITY_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("PRODUCTIVITY_SMTP_PORT", "587"))

    if not sender or not app_password:
        return False, "SMTP credentials not configured"

    msg = EmailMessage()
    msg["Subject"] = "Your Flowstate verification code"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(
        f"Your OTP is: {otp_code}\n\nThis code expires in 5 minutes.\nIf you did not request this, ignore this email."
    )

    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(sender, app_password)
            smtp.send_message(msg)
        return True, ""
    except Exception as e:
        return False, str(e)

"""Send OTP email through Resend's HTTPS API, with local SMTP as a dev fallback."""
import json
import os
import smtplib
from email.message import EmailMessage
from typing import Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _send_via_resend(email: str, otp_code: str, api_key: str, sender: str) -> Tuple[bool, str]:
    body = {
        "from": sender,
        "to": [email],
        "subject": "Your Flowstate verification code",
        "text": f"Your OTP is: {otp_code}\n\nThis code expires in 5 minutes. If you did not request this, ignore this email.",
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            if 200 <= response.status < 300:
                return True, ""
            return False, f"Resend API returned HTTP {response.status}"
    except HTTPError as exc:
        return False, f"Resend API returned HTTP {exc.code}: {exc.read(1000).decode('utf-8', 'replace')}"
    except (URLError, TimeoutError) as exc:
        return False, f"Resend request failed: {exc}"


def send_otp_email(email: str, otp_code: str) -> Tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RESEND_FROM_EMAIL", "").strip()
    if api_key and sender:
        return _send_via_resend(email, otp_code, api_key, sender)

    # SMTP is kept as an optional local-development fallback. Render Free blocks
    # outbound SMTP ports, so hosted deployments should configure Resend above.
    smtp_sender = os.getenv("PRODUCTIVITY_SMTP_EMAIL", "")
    app_password = os.getenv("PRODUCTIVITY_SMTP_APP_PASSWORD", "")
    host = os.getenv("PRODUCTIVITY_SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("PRODUCTIVITY_SMTP_PORT", "587"))
    if not smtp_sender or not app_password:
        return False, "Email provider is not configured (set RESEND_API_KEY and RESEND_FROM_EMAIL)"

    msg = EmailMessage()
    msg["Subject"] = "Your Flowstate verification code"
    msg["From"] = smtp_sender
    msg["To"] = email
    msg.set_content(f"Your OTP is: {otp_code}\n\nThis code expires in 5 minutes. If you did not request this, ignore this email.")
    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(smtp_sender, app_password)
            smtp.send_message(msg)
        return True, ""
    except Exception as exc:
        return False, str(exc)

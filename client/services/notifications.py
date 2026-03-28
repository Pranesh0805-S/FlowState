"""
Notification service — desktop (plyer) + email (smtplib).
"""

import smtplib
import threading
from email.mime.text import MIMEText

# ─── App name shown in desktop notifications ───────────────────────────────
APP_NAME = "Productivity Automation System"

# ─── CONFIGURE YOUR SENDER EMAIL HERE ─────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_app_email@gmail.com"   # ← change this
SENDER_PASSWORD = "your_app_password"        # ← use Gmail App Password
# ──────────────────────────────────────────────────────────────────────────


class NotificationService:
    """Static helper for desktop + email notifications."""

    @staticmethod
    def desktop(title: str, message: str):
        """Show a desktop notification using plyer (non-blocking)."""
        def _send():
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name=APP_NAME,   # ← shows "Productivity Automation System"
                    timeout=5,
                )
            except Exception as e:
                print(f"[Desktop notification error] {e}")

        threading.Thread(target=_send, daemon=True).start()

    @staticmethod
    def email(
        to: str,
        subject: str,
        body: str,
        smtp_host: str = SMTP_HOST,
        smtp_port: int = SMTP_PORT,
        sender_email: str = SENDER_EMAIL,
        sender_password: str = SENDER_PASSWORD,
    ):
        """Send an email notification (non-blocking)."""
        def _send():
            try:
                msg = MIMEText(body, "plain")
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = to

                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, [to], msg.as_string())
                print(f"[Email sent] → {to}: {subject}")
            except Exception as e:
                print(f"[Email notification error] {e}")

        threading.Thread(target=_send, daemon=True).start()

    @staticmethod
    def notify(
        title: str,
        message: str,
        email_to: str = "",
        email_subject: str = "",
        email_body: str = "",
    ):
        """Send desktop + optional email notification."""
        NotificationService.desktop(title, message)
        if email_to:
            NotificationService.email(
                to=email_to,
                subject=email_subject or title,
                body=email_body or message,
            )
from datetime import datetime, timedelta
from typing import Any, Dict

from . import schemas
from .database import DatabaseError, execute, fetch_one
from .utils import jwt
from .utils.mailer import send_otp_email
from .utils.otp import generate_otp
from .utils.security import hash_password, verify_password


OTP_TTL_MINUTES = 5
otp_store: Dict[str, Dict[str, Any]] = {}


def _cleanup_expired_otps() -> None:
    now = datetime.utcnow()
    expired_emails = [email for email, record in otp_store.items() if now > record.get("expires_at", now)]
    for email in expired_emails:
        otp_store.pop(email, None)


def send_registration_otp(name: str, email: str) -> Dict[str, Any]:
    if not name or not email:
        return {"status": "error", "data": {}, "message": "Name and email are required"}
    if not schemas.validate_email(email):
        return {"status": "error", "data": {}, "message": "Invalid email"}

    try:
        _cleanup_expired_otps()
        normalized_email = email.strip().lower()
        normalized_name = name.strip()

        existing = fetch_one("SELECT id FROM users WHERE email=%s", (normalized_email,))
        if existing:
            return {"status": "error", "data": {}, "message": "Email already registered"}

        otp_code = generate_otp()
        otp_store[normalized_email] = {
            "otp": str(otp_code),
            "name": normalized_name,
            "verified": False,
            "expires_at": datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES),
        }

        sent, err = send_otp_email(email=normalized_email, otp_code=otp_code)
        if not sent:
            otp_store.pop(normalized_email, None)
            return {"status": "error", "data": {}, "message": f"Failed to send OTP: {err}"}

        return {"status": "success", "data": {}, "message": "OTP sent successfully"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Failed to send registration OTP"}


def verify_registration_otp(email: str, otp_input: str) -> Dict[str, Any]:
    if not email or not otp_input:
        return {"status": "error", "data": {}, "message": "Email and OTP are required"}
    if not schemas.validate_email(email):
        return {"status": "error", "data": {}, "message": "Invalid email"}

    _cleanup_expired_otps()
    normalized_email = email.strip().lower()
    record = otp_store.get(normalized_email)
    if not record:
        return {"status": "error", "data": {}, "message": "OTP not found or expired"}

    expires_at = record.get("expires_at")
    if not expires_at or datetime.utcnow() > expires_at:
        otp_store.pop(normalized_email, None)
        return {"status": "error", "data": {}, "message": "OTP expired"}

    if record.get("verified"):
        return {"status": "error", "data": {}, "message": "OTP already used"}

    if str(record.get("otp", "")).strip() != str(otp_input).strip():
        return {"status": "error", "data": {}, "message": "Invalid OTP"}

    record["verified"] = True
    record["otp"] = None
    return {"status": "success", "data": {}, "message": "OTP verified successfully"}


def complete_registration(email: str, password: str) -> Dict[str, Any]:
    if not email or not password:
        return {"status": "error", "data": {}, "message": "Email and password are required"}
    if not schemas.validate_email(email):
        return {"status": "error", "data": {}, "message": "Invalid email"}
    if len(password) < 8:
        return {"status": "error", "data": {}, "message": "Password must be at least 8 characters"}

    normalized_email = email.strip().lower()
    _cleanup_expired_otps()
    record = otp_store.get(normalized_email)
    if not record:
        return {"status": "error", "data": {}, "message": "OTP verification required"}
    if not record.get("verified"):
        return {"status": "error", "data": {}, "message": "OTP verification required"}

    try:
        existing = fetch_one("SELECT id FROM users WHERE email=%s", (normalized_email,))
        if existing:
            otp_store.pop(normalized_email, None)
            return {"status": "error", "data": {}, "message": "Email already registered"}

        pw_hash = hash_password(password)
        execute(
            "INSERT INTO users(name, email, password_hash) VALUES(%s,%s,%s)",
            (record.get("name", "").strip(), normalized_email, pw_hash),
        )
        otp_store.pop(normalized_email, None)
        return {"status": "success", "data": {}, "message": "Registration completed successfully"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Registration failed"}


def register(name: str, email: str, password: str) -> Dict[str, Any]:
    return send_registration_otp(name=name, email=email)


def verify_otp(email: str, otp_input: str) -> Dict[str, Any]:
    return verify_registration_otp(email, otp_input)


def login(email: str, password: str) -> Dict[str, Any]:
    if not email or not password:
        return {"status": "error", "data": {}, "message": "Email and password are required"}
    if not schemas.validate_email(email):
        return {"status": "error", "data": {}, "message": "Invalid email"}

    try:
        row = fetch_one("SELECT id, name, email, password_hash, created_at FROM users WHERE email=%s", (email,))
        if not row:
            return {"status": "error", "data": {}, "message": "Invalid credentials"}
        if not verify_password(password, row.get("password_hash", "")):
            return {"status": "error", "data": {}, "message": "Invalid credentials"}
        user_id = int(row["id"])
        user = {"id": row["id"], "name": row["name"], "email": row["email"], "created_at": row["created_at"]}
        token = jwt.encode({"sub": user_id, "email": email})
        return {"status": "success", "data": {"token": token, "user": user}, "message": "Logged in"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Login failed"}


def update_profile(user_id: int, name: str) -> Dict[str, Any]:
    if not name or not name.strip():
        return {"status": "error", "data": {}, "message": "Name cannot be empty"}
    try:
        user = fetch_one("SELECT id FROM users WHERE id=%s", (int(user_id),))
        if not user:
            return {"status": "error", "data": {}, "message": "User not found"}
        execute("UPDATE users SET name=%s WHERE id=%s", (name.strip(), int(user_id)))
        updated = fetch_one("SELECT id, name, email, created_at FROM users WHERE id=%s", (int(user_id),))
        return {"status": "success", "data": {"user": updated}, "message": "Username updated"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Update failed"}


def change_password(user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
    if not current_password or not new_password:
        return {"status": "error", "data": {}, "message": "Current and new password are required"}
    if len(new_password) < 6:
        return {"status": "error", "data": {}, "message": "New password must be at least 6 characters"}
    try:
        row = fetch_one("SELECT password_hash FROM users WHERE id=%s", (int(user_id),))
        if not row:
            return {"status": "error", "data": {}, "message": "User not found"}
        if not verify_password(current_password, row.get("password_hash", "")):
            return {"status": "error", "data": {}, "message": "Current password is incorrect"}
        new_hash = hash_password(new_password)
        execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, int(user_id)))
        return {"status": "success", "data": {}, "message": "Password changed successfully"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Password change failed"}


def reset_password(email: str, new_password: str) -> Dict[str, Any]:
    if not email or not new_password:
        return {"status": "error", "data": {}, "message": "Email and new password are required"}
    if not schemas.validate_email(email):
        return {"status": "error", "data": {}, "message": "Invalid email"}
    if len(new_password) < 6:
        return {"status": "error", "data": {}, "message": "Password must be at least 6 characters"}
    try:
        user = fetch_one("SELECT id FROM users WHERE email=%s", (email,))
        if not user:
            return {"status": "error", "data": {}, "message": "No account found with that email"}
        new_hash = hash_password(new_password)
        execute("UPDATE users SET password_hash=%s WHERE email=%s", (new_hash, email))
        return {"status": "success", "data": {}, "message": "Password reset successfully"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Password reset failed"}

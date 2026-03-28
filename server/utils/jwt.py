import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional, Tuple


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("utf-8"))


def _secret() -> bytes:
    return os.getenv("PRODUCTIVITY_JWT_SECRET", "dev_secret_change_me").encode("utf-8")


def encode(payload: Dict[str, Any], exp_seconds: int = 60 * 60 * 24) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    body = dict(payload)
    body.setdefault("iat", now)
    body.setdefault("exp", now + exp_seconds)

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode(token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    if not token or token.count(".") != 2:
        return False, None, "Invalid token format"
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected = hmac.new(_secret(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url_encode(expected), sig_b64):
            return False, None, "Invalid token signature"
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        exp = int(payload.get("exp", 0))
        if exp and int(time.time()) > exp:
            return False, None, "Token expired"
        return True, payload, "OK"
    except Exception:
        return False, None, "Token decode failed"


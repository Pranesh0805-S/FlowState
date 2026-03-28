from typing import Any, Dict, Optional

from server import main as server_main


class ApiClient:
    def __init__(self):
        self.token: Optional[str] = None
        self.user: Optional[Dict[str, Any]] = None

    def set_auth(self, token: str, user: Dict[str, Any]):
        self.token = token
        self.user = user

    def clear_auth(self):
        self.token = None
        self.user = None

    def call(self, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = dict(payload or {})
        if self.token and action not in (
            "auth.login",
            "auth.register",
            "auth.verify_otp",
            "auth.send_registration_otp",
            "auth.verify_registration_otp",
            "auth.complete_registration",
            "ping",
        ):
            p["token"] = self.token
        return server_main.handle_request(action, p)


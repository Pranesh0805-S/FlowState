from pathlib import Path
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parents[1]
_local_env = _project_root / ".env.local"
load_dotenv(_local_env if _local_env.exists() else _project_root / ".env")

from typing import Any, Dict

from . import auth, dashboard, history, tasks, teams
from .utils import jwt


def _ok(data: Dict[str, Any], message: str = "OK") -> Dict[str, Any]:
    return {"status": "success", "data": data, "message": message}


def _err(message: str) -> Dict[str, Any]:
    return {"status": "error", "data": {}, "message": message}


def _require_auth(payload: Dict[str, Any]) -> Dict[str, Any]:
    token = payload.get("token") or ""
    ok, decoded, msg = jwt.decode(token)
    if not ok or not decoded:
        return _err(msg)
    return _ok({"auth": decoded})


def handle_request(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Client calls:
        response = server.main.handle_request(action, payload)
    """
    try:
        if action == "ping":
            return _ok({"pong": True}, "pong")

        # ── Auth routes (no token required) ──────────────────────────────
        if action == "auth.send_registration_otp":
            return auth.send_registration_otp(payload.get("name", ""), payload.get("email", ""))

        if action == "auth.verify_registration_otp":
            return auth.verify_registration_otp(payload.get("email", ""), payload.get("otp", ""))

        if action == "auth.complete_registration":
            return auth.complete_registration(payload.get("email", ""), payload.get("password", ""))

        if action == "auth.register":
            return auth.register(payload.get("name", ""), payload.get("email", ""), payload.get("password", ""))

        if action == "auth.verify_otp":
            return auth.verify_otp(payload.get("email", ""), payload.get("otp_input", ""))

        if action == "auth.login":
            return auth.login(payload.get("email", ""), payload.get("password", ""))

        if action == "auth.reset_password":
            # Forgot password flow — email + new password, no token needed
            return auth.reset_password(
                email=payload.get("email", ""),
                new_password=payload.get("new_password", ""),
            )
        if action == "auth.send_password_reset_otp":
            return auth.send_password_reset_otp(payload.get("email", ""))
        if action == "auth.verify_password_reset_otp":
            return auth.verify_password_reset_otp(payload.get("email", ""), payload.get("otp", ""))

        # ── Everything below requires a valid token ───────────────────────
        auth_res = _require_auth(payload)
        if auth_res["status"] != "success":
            return auth_res
        user_id = int(auth_res["data"]["auth"]["sub"])

        # ── Profile & account ─────────────────────────────────────────────
        if action == "auth.update_profile":
            return auth.update_profile(
                user_id=user_id,
                name=payload.get("name", ""),
            )

        if action == "auth.change_password":
            return auth.change_password(
                user_id=user_id,
                current_password=payload.get("current_password", ""),
                new_password=payload.get("new_password", ""),
            )

        # ── Tasks ─────────────────────────────────────────────────────────
        if action == "tasks.create":
            p = dict(payload)
            p["user_id"] = user_id
            return tasks.create_task(p)
        if action == "tasks.update":
            return tasks.update_task(user_id, int(payload.get("task_id", 0)), payload)
        if action == "tasks.move":
            return tasks.move_task(user_id, int(payload.get("task_id", 0)), payload.get("status", ""))
        if action == "tasks.delete":
            return tasks.delete_task(user_id, int(payload.get("task_id", 0)))
        if action == "tasks.list":
            return tasks.list_tasks(user_id)

        # ── Teams ─────────────────────────────────────────────────────────
        if action == "teams.create":
            return teams.create_team(user_id, payload.get("name", ""))
        if action == "teams.assign_member":
            return teams.assign_member(user_id, int(payload.get("team_id", 0)), int(payload.get("user_id", 0)))
        if action == "teams.assign_task":
            return teams.assign_task(user_id, int(payload.get("team_id", 0)), int(payload.get("task_id", 0)))
        if action == "teams.list_team_tasks":
            return teams.list_team_tasks(user_id, int(payload.get("team_id", 0)))
        if action == "teams.list_for_user":
            return teams.list_teams_for_user(user_id)

        # ── Dashboard & History ───────────────────────────────────────────
        if action == "dashboard.metrics":
            history.overdue_scan_and_log(user_id)
            return dashboard.get_metrics(user_id)

        if action == "history.list":
            return history.list_history(user_id=user_id, limit=int(payload.get("limit", 100)))

        return _err("Unknown action")

    except Exception:
        return _err("Request failed")

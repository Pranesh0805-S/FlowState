from datetime import date
from typing import Any, Dict, Optional, Tuple


ALLOWED_STATUSES = {"backlog", "in_progress", "blocked", "completed"}
ALLOWED_PRIORITIES = {"low", "medium", "high"}


def require_fields(payload: Dict[str, Any], fields) -> Tuple[bool, str]:
    missing = [f for f in fields if payload.get(f) in (None, "")]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    return True, "OK"


def validate_email(email: str) -> bool:
    return bool(email) and ("@" in email) and ("." in email)


def parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    try:
        parts = d.split("-")
        if len(parts) != 3:
            return None
        y, m, dd = (int(parts[0]), int(parts[1]), int(parts[2]))
        return date(y, m, dd)
    except Exception:
        return None


def validate_task_payload(payload: Dict[str, Any]) -> Tuple[bool, str]:
    ok, msg = require_fields(payload, ["title"])
    if not ok:
        return False, msg
    status = payload.get("status", "backlog")
    if status not in ALLOWED_STATUSES:
        return False, "Invalid status"
    priority = payload.get("priority", "medium")
    if priority not in ALLOWED_PRIORITIES:
        return False, "Invalid priority"
    due_date = payload.get("due_date")
    if due_date and not parse_date(due_date):
        return False, "Invalid due_date (expected YYYY-MM-DD)"
    est = payload.get("duration_estimated")
    if est not in (None, ""):
        try:
            if int(est) < 0:
                return False, "duration_estimated must be >= 0"
        except Exception:
            return False, "duration_estimated must be a number (minutes)"
    urgent = payload.get("urgency_flag")
    if urgent not in (None, "", True, False, 0, 1, "0", "1"):
        return False, "urgency_flag must be boolean-like"
    return True, "OK"


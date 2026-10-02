from datetime import date
from typing import Any, Dict, Optional

from dateutil.parser import isoparse

from . import schemas
from .database import DatabaseError, execute, fetch_all, fetch_one
from .history import log_event


def _parse_due(due_date: Optional[str]) -> Optional[date]:
    if not due_date:
        return None
    try:
        return isoparse(due_date).date()
    except Exception:
        return schemas.parse_date(due_date)


def _is_overdue(due: Optional[date]) -> bool:
    return bool(due and due < date.today())


# ✅ SYSTEM-CALCULATED PRIORITY
def calculate_priority(
    due: Optional[date],
    estimated_minutes: Optional[int],
    is_urgent: int
) -> str:
    if is_urgent == 1:
        return "high"

    if due:
        days_left = (due - date.today()).days
        if days_left <= 3:
            return "high"

    if estimated_minutes and estimated_minutes >= 120:
        return "medium"

    return "low"


def create_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, msg = schemas.validate_task_payload(payload)
    if not ok:
        return {"status": "error", "data": {}, "message": msg}

    user_id = payload.get("user_id")
    if not user_id:
        return {"status": "error", "data": {}, "message": "user_id required"}

    try:
        due = _parse_due(payload.get("due_date"))

        urgent_flag = payload.get("urgency_flag")
        is_urgent = 1 if str(urgent_flag) in ("1", "True", "true") or urgent_flag is True else 0

        est = payload.get("duration_estimated")
        estimated_minutes = int(est) if est not in (None, "") else None

        priority = calculate_priority(due, estimated_minutes, is_urgent)

        task_id = execute(
            """
            INSERT INTO tasks (
                user_id,
                title,
                description,
                category,
                status,
                priority,
                due_date,
                estimated_minutes,
                urgent
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                int(user_id),
                payload.get("title"),
                payload.get("description"),
                payload.get("category"),
                payload.get("status", "backlog"),
                priority,
                due,
                estimated_minutes,
                is_urgent,
            ),
        )

        task = fetch_one("SELECT * FROM tasks WHERE id=%s", (task_id,))
        log_event(int(task_id), "created")
        return {"status": "success", "data": {"task": task}, "message": "Task created"}

    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def update_task(user_id: int, task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        existing = fetch_one("SELECT * FROM tasks WHERE id=%s AND user_id=%s", (int(task_id), int(user_id)))
        if not existing:
            return {"status": "error", "data": {}, "message": "Task not found"}

        fields = {}

        for k in ["title", "category", "status"]:
            if payload.get(k) not in (None, ""):
                fields[k] = payload[k]

        if payload.get("description") is not None:
            fields["description"] = payload.get("description")

        if payload.get("due_date") is not None:
            fields["due_date"] = _parse_due(payload.get("due_date"))

        if payload.get("duration_estimated") is not None:
            est = payload.get("duration_estimated")
            fields["estimated_minutes"] = int(est) if est not in (None, "") else None

        if payload.get("urgency_flag") is not None:
            urgent_flag = payload.get("urgency_flag")
            fields["urgent"] = 1 if str(urgent_flag) in ("1", "True", "true") or urgent_flag is True else 0

        # ✅ recalculate priority if needed
        if any(k in fields for k in ("due_date", "estimated_minutes", "urgent")):
            due = fields.get("due_date", existing.get("due_date"))
            if isinstance(due, str):
                due = schemas.parse_date(due[:10])
            est = fields.get("estimated_minutes", existing.get("estimated_minutes"))
            urg = fields.get("urgent", existing.get("urgent"))
            fields["priority"] = calculate_priority(due, est, urg)

        if "status" in fields and fields["status"] not in schemas.ALLOWED_STATUSES:
            return {"status": "error", "data": {}, "message": "Invalid status"}

        if not fields:
            return {"status": "success", "data": {"task": existing}, "message": "No changes"}

        set_sql = ", ".join([f"{k}=%s" for k in fields.keys()])
        params = list(fields.values()) + [int(task_id)]
        params.append(int(user_id))
        execute(f"UPDATE tasks SET {set_sql}, updated_at=CURRENT_TIMESTAMP WHERE id=%s AND user_id=%s", tuple(params))
        log_event(int(task_id), "updated")

        task = fetch_one("SELECT * FROM tasks WHERE id=%s", (int(task_id),))
        return {"status": "success", "data": {"task": task}, "message": "Task updated"}

    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}
    except Exception:
        return {"status": "error", "data": {}, "message": "Update failed"}


def move_task(user_id: int, task_id: int, new_status: str) -> Dict[str, Any]:
    if new_status not in schemas.ALLOWED_STATUSES:
        return {"status": "error", "data": {}, "message": "Invalid status"}

    try:
        task = fetch_one("SELECT * FROM tasks WHERE id=%s AND user_id=%s", (int(task_id), int(user_id)))
        if not task:
            return {"status": "error", "data": {}, "message": "Task not found"}

        allowed = {
            "backlog": {"in_progress"},
            "in_progress": {"blocked", "completed"},
            "blocked": {"in_progress", "completed"},
            "completed": set(),
        }

        current = task.get("status")
        if new_status != current and new_status not in allowed.get(current, set()):
            return {"status": "error", "data": {}, "message": f"Invalid transition {current} -> {new_status}"}

        execute("UPDATE tasks SET status=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s AND user_id=%s", (new_status, int(task_id), int(user_id)))

        if new_status != current:
            log_event(int(task_id), f"moved:{current}->{new_status}")

        task2 = fetch_one("SELECT * FROM tasks WHERE id=%s", (int(task_id),))
        return {"status": "success", "data": {"task": task2}, "message": "Moved"}

    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def delete_task(user_id: int, task_id: int) -> Dict[str, Any]:
    try:
        existing = fetch_one("SELECT id FROM tasks WHERE id=%s AND user_id=%s", (int(task_id), int(user_id)))
        if not existing:
            return {"status": "error", "data": {}, "message": "Task not found"}

        execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (int(task_id), int(user_id)))
        return {"status": "success", "data": {}, "message": "Task deleted"}

    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def list_tasks(user_id: int, include_overdue_flag: bool = True) -> Dict[str, Any]:
    try:
        rows = fetch_all(
            "SELECT * FROM tasks WHERE user_id=%s ORDER BY updated_at DESC",
            (int(user_id),),
        )

        if include_overdue_flag:
            for r in rows:
                due = r.get("due_date")
                r["overdue"] = bool(due and str(due)[:10] < date.today().isoformat() and r.get("status") != "completed")

        return {"status": "success", "data": {"tasks": rows}, "message": "OK"}

    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}

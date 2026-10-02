from datetime import date
from typing import Any, Dict, Optional

from .database import DatabaseError, execute, fetch_all


def log_event(task_id: int, event: str) -> None:
    try:
        execute("INSERT INTO history(task_id, event) VALUES(%s,%s)", (task_id, event))
    except Exception:
        # non-fatal
        return


def list_history(user_id: Optional[int] = None, limit: int = 100) -> Dict[str, Any]:
    try:
        if user_id:
            rows = fetch_all(
                """
                SELECT h.id, h.task_id, h.event, h.timestamp, t.title, t.status, t.due_date
                FROM history h
                JOIN tasks t ON t.id = h.task_id
                WHERE t.user_id=%s
                ORDER BY h.timestamp DESC
                LIMIT %s
                """,
                (user_id, int(limit)),
            )
        else:
            rows = fetch_all(
                """
                SELECT h.id, h.task_id, h.event, h.timestamp, t.title, t.status, t.due_date
                FROM history h
                JOIN tasks t ON t.id = h.task_id
                ORDER BY h.timestamp DESC
                LIMIT %s
                """,
                (int(limit),),
            )
        return {"status": "success", "data": {"items": rows}, "message": "OK"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def overdue_scan_and_log(user_id: int) -> None:
    # Logs overdue events (idempotency is not enforced; keep it simple)
    try:
        today = date.today()
        rows = fetch_all(
            "SELECT id, due_date, status FROM tasks WHERE user_id=%s AND status!='completed' AND due_date IS NOT NULL",
            (user_id,),
        )
        for r in rows:
            due = r.get("due_date")
            if due and str(due)[:10] < today.isoformat():
                prior = fetch_all("SELECT id FROM history WHERE task_id=%s AND event='overdue' AND timestamp >= date('now','-1 day')", (int(r["id"]),))
                if not prior:
                    log_event(int(r["id"]), "overdue")
    except Exception:
        return


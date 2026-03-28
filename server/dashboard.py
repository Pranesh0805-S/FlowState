from datetime import date, datetime, timedelta
from typing import Any, Dict

from .database import DatabaseError, fetch_all


def get_metrics(user_id: int) -> Dict[str, Any]:
    try:
        tasks = fetch_all("SELECT id, status, priority, due_date, updated_at FROM tasks WHERE user_id=%s", (int(user_id),))
        today = date.today()
        week_start = today - timedelta(days=7)

        completed_today = 0
        completed_week = 0
        overdue_count = 0
        high_priority_count = 0
        total = len(tasks)
        completed_total = 0

        for t in tasks:
            status = t.get("status")
            priority = t.get("priority")
            due = t.get("due_date")
            updated_at = t.get("updated_at")
            if priority == "high":
                high_priority_count += 1
            if due and due < today and status != "completed":
                overdue_count += 1
            if status == "completed":
                completed_total += 1
                if isinstance(updated_at, datetime):
                    upd_date = updated_at.date()
                    if upd_date == today:
                        completed_today += 1
                    if upd_date >= week_start:
                        completed_week += 1

        completion_rate = int((completed_total / total) * 100) if total else 0
        data = {
            "tasks_completed_today": completed_today,
            "tasks_completed_week": completed_week,
            "overdue_count": overdue_count,
            "high_priority_count": high_priority_count,
            "completion_rate": completion_rate,
        }
        return {"status": "success", "data": data, "message": "OK"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


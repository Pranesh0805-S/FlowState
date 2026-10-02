from datetime import date
from typing import Any, Dict

from .database import DatabaseError, execute, fetch_all, fetch_one


def create_team(user_id: int, name: str) -> Dict[str, Any]:
    if not name:
        return {"status": "error", "data": {}, "message": "Team name required"}
    try:
        team_id = execute("INSERT INTO teams(name, created_by) VALUES(%s,%s)", (name.strip(), int(user_id)))
        execute("INSERT OR IGNORE INTO team_members(team_id, user_id) VALUES(%s,%s)", (team_id, int(user_id)))
        team = fetch_one("SELECT * FROM teams WHERE id=%s", (team_id,))
        return {"status": "success", "data": {"team": team}, "message": "Team created"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def assign_member(requester_id: int, team_id: int, user_id: int) -> Dict[str, Any]:
    try:
        team = fetch_one("SELECT id FROM teams WHERE id=%s AND created_by=%s", (int(team_id), int(requester_id)))
        if not team:
            return {"status": "error", "data": {}, "message": "Team not found"}
        user = fetch_one("SELECT id FROM users WHERE id=%s", (int(user_id),))
        if not user:
            return {"status": "error", "data": {}, "message": "User not found"}
        execute("INSERT IGNORE INTO team_members(team_id, user_id) VALUES(%s,%s)", (int(team_id), int(user_id)))
        return {"status": "success", "data": {}, "message": "Member assigned"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def assign_task(user_id: int, team_id: int, task_id: int) -> Dict[str, Any]:
    try:
        team = fetch_one("SELECT id FROM teams WHERE id=%s AND created_by=%s", (int(team_id), int(user_id)))
        if not team:
            return {"status": "error", "data": {}, "message": "Team not found"}
        task = fetch_one("SELECT id FROM tasks WHERE id=%s AND user_id=%s", (int(task_id), int(user_id)))
        if not task:
            return {"status": "error", "data": {}, "message": "Task not found"}
        execute("INSERT IGNORE INTO team_tasks(team_id, task_id) VALUES(%s,%s)", (int(team_id), int(task_id)))
        return {"status": "success", "data": {}, "message": "Task assigned"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def list_team_tasks(user_id: int, team_id: int) -> Dict[str, Any]:
    try:
        rows = fetch_all(
            """
            SELECT t.*
            FROM team_tasks tt
            JOIN tasks t ON t.id = tt.task_id
            JOIN team_members tm ON tm.team_id=tt.team_id
            WHERE tt.team_id=%s AND tm.user_id=%s
            ORDER BY t.updated_at DESC
            """,
            (int(team_id), int(user_id)),
        )
        today = date.today()
        for r in rows:
            due = r.get("due_date")
            r["overdue"] = bool(due and str(due)[:10] < today.isoformat() and r.get("status") != "completed")
        return {"status": "success", "data": {"tasks": rows}, "message": "OK"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


def list_teams_for_user(user_id: int) -> Dict[str, Any]:
    try:
        rows = fetch_all(
            """
            SELECT tm.team_id, t.name, t.created_at
            FROM team_members tm
            JOIN teams t ON t.id = tm.team_id
            WHERE tm.user_id=%s
            ORDER BY t.created_at DESC
            """,
            (int(user_id),),
        )
        return {"status": "success", "data": {"teams": rows}, "message": "OK"}
    except DatabaseError as e:
        return {"status": "error", "data": {}, "message": f"DB error: {e}"}


"""REST API for the Flowstate web client. Run with `uvicorn server.api:app`."""
from pathlib import Path
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

_root = Path(__file__).resolve().parents[1]
_env_file = _root / ".env.local"
load_dotenv(_env_file if _env_file.exists() else _root / ".env")

from . import auth, dashboard, history, tasks, teams
from .database import fetch_one
from .main import handle_request
from .utils import jwt


app = FastAPI(title="Flowstate API", version="1.0.0", docs_url="/api/docs")
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
web_origin = os.getenv("WEB_ORIGIN", "").strip().rstrip("/")
if web_origin:
    allowed_origins.append(web_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmailInput(Input):
    email: str = Field(min_length=3, max_length=255)


class RegisterInput(EmailInput):
    name: str = Field(min_length=1, max_length=120)


class OtpInput(EmailInput):
    otp: str = Field(min_length=6, max_length=6)


class PasswordInput(EmailInput):
    password: str = Field(min_length=8, max_length=128)


class ResetPasswordInput(EmailInput):
    new_password: str = Field(min_length=8, max_length=128)


class LoginInput(EmailInput):
    password: str = Field(min_length=1, max_length=128)


class TaskInput(Input):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
    category: Optional[str] = Field(default=None, max_length=120)
    due_date: Optional[str] = None
    duration_estimated: Optional[int] = Field(default=None, ge=0, le=100000)
    urgency_flag: Optional[bool] = False
    status: Optional[str] = "backlog"


class TaskPatch(Input):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
    category: Optional[str] = Field(default=None, max_length=120)
    due_date: Optional[str] = None
    duration_estimated: Optional[int] = Field(default=None, ge=0, le=100000)
    urgency_flag: Optional[bool] = None
    status: Optional[str] = None


class MoveInput(Input):
    status: str


class TeamInput(Input):
    name: str = Field(min_length=1, max_length=200)


class AssignTaskInput(Input):
    task_id: int = Field(gt=0)


class InviteInput(Input):
    email: str = Field(min_length=3, max_length=255)


class ProfileInput(Input):
    name: str = Field(min_length=1, max_length=120)


class ChangePasswordInput(Input):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


def _status_for(message: str) -> int:
    low = message.lower()
    if "invalid token" in low or "token expired" in low:
        return 401
    if "not found" in low or "no account" in low:
        return 404
    if "invalid" in low or "required" in low or "must be" in low or "verification" in low or "expired" in low:
        return 422
    if "db error" in low or "request failed" in low:
        return 500
    return 400


def _result(result: Dict[str, Any]) -> Dict[str, Any]:
    if result.get("status") != "success":
        raise HTTPException(status_code=_status_for(str(result.get("message", "Request failed"))), detail=result.get("message", "Request failed"))
    return result.get("data", {})


def current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    valid, claims, message = jwt.decode(token)
    if not valid or not claims:
        raise HTTPException(status_code=401, detail=message)
    row = fetch_one("SELECT id, name, email, created_at FROM users WHERE id=%s", (int(claims.get("sub", 0)),))
    if not row:
        raise HTTPException(status_code=401, detail="Account not found")
    return {"id": int(row["id"]), "name": row["name"], "email": row["email"], "created_at": row["created_at"]}


def _protected(action: str, payload: Dict[str, Any], user: Dict[str, Any], authorization: Optional[str]) -> Dict[str, Any]:
    token = (authorization or "").partition(" ")[2]
    payload["token"] = token
    return _result(handle_request(action, payload))


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "flowstate-api"}


@app.post("/api/auth/register")
def register(body: RegisterInput):
    return _result(auth.send_registration_otp(body.name, body.email))


@app.post("/api/auth/register/verify")
def verify_registration(body: OtpInput):
    return _result(auth.verify_registration_otp(body.email, body.otp))


@app.post("/api/auth/register/complete")
def complete_registration(body: PasswordInput):
    return _result(auth.complete_registration(body.email, body.password))


@app.post("/api/auth/login")
def login(body: LoginInput):
    return _result(auth.login(body.email, body.password))


@app.post("/api/auth/password-reset")
def send_reset_code(body: EmailInput):
    return _result(auth.send_password_reset_otp(body.email))


@app.post("/api/auth/password-reset/verify")
def verify_reset_code(body: OtpInput):
    return _result(auth.verify_password_reset_otp(body.email, body.otp))


@app.post("/api/auth/password-reset/complete")
def complete_reset(body: ResetPasswordInput):
    return _result(auth.reset_password(body.email, body.new_password))


@app.post("/api/auth/logout", status_code=204)
def logout():
    return Response(status_code=204)


@app.get("/api/auth/me")
def me(user: Dict[str, Any] = Depends(current_user)):
    return {"user": user}


@app.get("/api/tasks")
def list_tasks(user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("tasks.list", {}, user, authorization)


@app.post("/api/tasks", status_code=201)
def create_task(body: TaskInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("tasks.create", body.model_dump(exclude_unset=True), user, authorization)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, body: TaskPatch, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("tasks.update", {"task_id": task_id, **body.model_dump(exclude_unset=True)}, user, authorization)


@app.post("/api/tasks/{task_id}/move")
def move_task(task_id: int, body: MoveInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("tasks.move", {"task_id": task_id, "status": body.status}, user, authorization)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    _protected("tasks.delete", {"task_id": task_id}, user, authorization)
    return Response(status_code=204)


@app.get("/api/dashboard")
def dashboard_metrics(user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("dashboard.metrics", {}, user, authorization)


@app.get("/api/history")
def history_items(limit: int = Query(default=100, ge=1, le=500), user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("history.list", {"limit": limit}, user, authorization)


@app.get("/api/teams")
def list_teams(user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("teams.list_for_user", {}, user, authorization)


@app.post("/api/teams", status_code=201)
def create_team(body: TeamInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("teams.create", {"name": body.name}, user, authorization)


@app.get("/api/teams/{team_id}/tasks")
def team_tasks(team_id: int, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("teams.list_team_tasks", {"team_id": team_id}, user, authorization)


@app.post("/api/teams/{team_id}/tasks")
def assign_task(team_id: int, body: AssignTaskInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("teams.assign_task", {"team_id": team_id, "task_id": body.task_id}, user, authorization)


@app.post("/api/teams/{team_id}/members")
def invite_member(team_id: int, body: InviteInput, user: Dict[str, Any] = Depends(current_user)):
    result = teams.assign_member_by_email(user["id"], team_id, body.email)
    return _result(result)


@app.patch("/api/profile")
def update_profile(body: ProfileInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("auth.update_profile", {"name": body.name}, user, authorization)


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordInput, user: Dict[str, Any] = Depends(current_user), authorization: Optional[str] = Header(default=None)):
    return _protected("auth.change_password", body.model_dump(), user, authorization)

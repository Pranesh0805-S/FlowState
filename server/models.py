from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    desc: Optional[str]
    category: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    estimated_minutes: Optional[int]
    urgent: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class Team:
    id: int
    name: str
    created_at: datetime


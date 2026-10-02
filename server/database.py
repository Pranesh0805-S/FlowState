"""Small SQLite data layer; the application works without a database server."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DatabaseError(Exception):
    pass


def _database_path() -> Path:
    configured = os.getenv("PRODUCTIVITY_DB_PATH")
    return Path(configured).expanduser() if configured else Path(__file__).resolve().parents[1] / "database" / "productivity.db"


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialize() -> None:
    schema = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
    try:
        with _connect() as conn:
            conn.executescript(schema.read_text(encoding="utf-8"))
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(str(exc)) from exc


@contextmanager
def get_conn():
    conn = None
    try:
        conn = _connect()
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        if conn:
            conn.rollback()
        raise DatabaseError(str(exc)) from exc
    finally:
        if conn:
            conn.close()


def _query(query: str) -> str:
    # Keep existing parameterized query call sites portable while using sqlite.
    return query.replace("%s", "?").replace("INSERT IGNORE", "INSERT OR IGNORE")


def fetch_one(query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(_query(query), params or ()).fetchone()
        return dict(row) if row is not None else None


def fetch_all(query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(_query(query), params or ()).fetchall()]


def execute(query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    with get_conn() as conn:
        cursor = conn.execute(_query(query), params or ())
        return int(cursor.lastrowid or 0)


initialize()

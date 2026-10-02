"""SQLite for local development and PostgreSQL for hosted deployments."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DatabaseError(Exception):
    pass


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def _database_path() -> Path:
    configured = os.getenv("PRODUCTIVITY_DB_PATH")
    return Path(configured).expanduser() if configured else Path(__file__).resolve().parents[1] / "database" / "productivity.db"


def _connect():
    if _database_url():
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(_database_url(), row_factory=dict_row, connect_timeout=10)
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _is_postgres() -> bool:
    return bool(_database_url())


def _postgres_schema() -> str:
    return Path(__file__).resolve().parents[1].joinpath("database", "schema.postgres.sql").read_text(encoding="utf-8")


def initialize() -> None:
    try:
        if _is_postgres():
            with get_conn() as conn:
                for statement in _postgres_schema().split(";"):
                    if statement.strip():
                        conn.execute(statement)
        else:
            schema = Path(__file__).resolve().parents[1] / "database" / "schema.sql"
            with _connect() as conn:
                conn.executescript(schema.read_text(encoding="utf-8"))
                columns = {row[1] for row in conn.execute("PRAGMA table_info(teams)").fetchall()}
                if "created_by" not in columns:
                    conn.execute("ALTER TABLE teams ADD COLUMN created_by INTEGER REFERENCES users(id) ON DELETE CASCADE")
                    conn.execute(
                        "UPDATE teams SET created_by=(SELECT user_id FROM team_members WHERE team_id=teams.id ORDER BY id LIMIT 1) WHERE created_by IS NULL"
                    )
    except Exception as exc:
        if isinstance(exc, (sqlite3.Error, OSError)) or exc.__class__.__module__.startswith("psycopg"):
            raise DatabaseError(str(exc)) from exc
        raise


@contextmanager
def get_conn():
    conn = None
    try:
        conn = _connect()
        yield conn
        conn.commit()
    except Exception as exc:
        if conn:
            conn.rollback()
        if isinstance(exc, (sqlite3.Error,)) or exc.__class__.__module__.startswith("psycopg"):
            raise DatabaseError(str(exc)) from exc
        raise
    finally:
        if conn:
            conn.close()


def _query(query: str) -> str:
    if _is_postgres():
        return query.replace("date('now','-1 day')", "CURRENT_TIMESTAMP - INTERVAL '1 day'")
    return query.replace("%s", "?")


def fetch_one(query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(_query(query), params or ()).fetchone()
        return dict(row) if row is not None else None


def fetch_all(query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        return [dict(row) for row in conn.execute(_query(query), params or ()).fetchall()]


def execute(query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    with get_conn() as conn:
        sql = _query(query)
        if _is_postgres() and sql.lstrip().upper().startswith("INSERT ") and " RETURNING " not in sql.upper():
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        cursor = conn.execute(sql, params or ())
        if _is_postgres():
            row = cursor.fetchone() if cursor.description else None
            return int(row["id"]) if row and row.get("id") is not None else 0
        return int(cursor.lastrowid or 0)


initialize()

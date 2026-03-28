import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import mysql.connector


class DatabaseError(Exception):
    pass


def _db_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("PRODUCTIVITY_DB_HOST", "localhost"),
        "port": int(os.getenv("PRODUCTIVITY_DB_PORT", "3306")),
        "user": os.getenv("PRODUCTIVITY_DB_USER", "root"),
        "password": os.getenv("PRODUCTIVITY_DB_PASSWORD", "MySQL@8.p"),
        "database": os.getenv("PRODUCTIVITY_DB_NAME", "productivity_automation_system"),
    }


@contextmanager
def get_conn():
    try:
        conn = mysql.connector.connect(**_db_config())
        yield conn
        conn.close()
    except mysql.connector.Error as e:
        raise DatabaseError(str(e)) from e


def fetch_one(query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return row


def fetch_all(query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows


def execute(query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        last_id = cur.lastrowid or 0
        cur.close()
        return int(last_id)


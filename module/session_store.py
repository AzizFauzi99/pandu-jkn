import uuid
from dataclasses import dataclass
from datetime import datetime

from utils.db import run_admin

DEFAULT_TITLE = "Percakapan baru"

COLUMNS = "id, user_nik, title, starred, created_at, updated_at"


@dataclass
class Session:
    id: str
    user_id: str  # NIK pemilik session
    title: str
    starred: bool
    created_at: datetime
    updated_at: datetime


def _to_session(row: dict) -> Session:
    return Session(
        id=row["id"],
        user_id=str(row["user_nik"]),
        title=row["title"],
        starred=row["starred"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# Semua fungsi menyaring berdasarkan user_id (NIK), jadi session milik user
# lain dianggap tidak ada.
def create_session(user_id: str, title: str | None = None) -> Session:
    rows = run_admin(
        f"INSERT INTO sessions (id, user_nik, title) VALUES (%s, %s, %s) "
        f"RETURNING {COLUMNS}",
        (str(uuid.uuid4()), user_id, (title or "").strip() or DEFAULT_TITLE),
    )
    return _to_session(rows[0])


def list_sessions(user_id: str, starred: bool | None = None) -> list[Session]:
    sql = f"SELECT {COLUMNS} FROM sessions WHERE user_nik = %s"
    params: list = [user_id]
    if starred is not None:
        sql += " AND starred = %s"
        params.append(starred)
    sql += " ORDER BY updated_at DESC"
    rows = run_admin(sql, tuple(params))
    return [_to_session(r) for r in rows]


def get_session(user_id: str, session_id: str) -> Session | None:
    rows = run_admin(
        f"SELECT {COLUMNS} FROM sessions WHERE id = %s AND user_nik = %s",
        (session_id, user_id),
    )
    return _to_session(rows[0]) if rows else None


def update_title(user_id: str, session_id: str, title: str) -> Session | None:
    rows = run_admin(
        f"UPDATE sessions SET title = %s, updated_at = now() "
        f"WHERE id = %s AND user_nik = %s RETURNING {COLUMNS}",
        (title.strip(), session_id, user_id),
    )
    return _to_session(rows[0]) if rows else None


def set_starred(user_id: str, session_id: str, starred: bool) -> Session | None:
    rows = run_admin(
        f"UPDATE sessions SET starred = %s WHERE id = %s AND user_nik = %s "
        f"RETURNING {COLUMNS}",
        (starred, session_id, user_id),
    )
    return _to_session(rows[0]) if rows else None


def delete_session(user_id: str, session_id: str) -> bool:
    rows = run_admin(
        f"DELETE FROM sessions WHERE id = %s AND user_nik = %s RETURNING id",
        (session_id, user_id),
    )
    return bool(rows)

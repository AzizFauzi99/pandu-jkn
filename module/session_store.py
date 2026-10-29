import uuid
from dataclasses import dataclass
from datetime import datetime

from utils.db import run_admin

DEFAULT_TITLE = "Percakapan baru"

_columns = "id, user_nik, title, starred, created_at, updated_at"


@dataclass
class Session:
    id: str
    user_nik: int
    title: str
    starred: bool
    created_at: datetime
    updated_at: datetime


def create_session(user_nik: str, title: str | None = None) -> Session:
    rows = run_admin(
        f"insert into sessions (id, user_nik, title) values (%s, %s, %s) returning {_columns}",
        (str(uuid.uuid4()), int(user_nik), (title or "").strip() or DEFAULT_TITLE),
    )
    return Session(**rows[0])


def list_sessions(user_nik: str, starred: bool | None = None) -> list[Session]:
    sql = f"select {_columns} from sessions where user_nik = %s"
    params = [int(user_nik)]
    if starred is not None:
        sql += " and starred = %s"
        params.append(starred)

    rows = run_admin(f"{sql} order by updated_at desc", tuple(params))
    return [Session(**row) for row in rows]


def get_session(user_nik: str, session_id: str) -> Session | None:
    rows = run_admin(
        f"select {_columns} from sessions where id = %s and user_nik = %s",
        (session_id, int(user_nik)),
    )
    return Session(**rows[0]) if rows else None


def update_title(user_nik: str, session_id: str, title: str) -> Session | None:
    rows = run_admin(
        f"""
        update sessions set title = %s, updated_at = now()
        where id = %s and user_nik = %s
        returning {_columns}
        """,
        (title.strip(), session_id, int(user_nik)),
    )
    return Session(**rows[0]) if rows else None


def set_starred(user_nik: str, session_id: str, starred: bool) -> Session | None:
    rows = run_admin(
        f"""
        update sessions set starred = %s
        where id = %s and user_nik = %s
        returning {_columns}
        """,
        (starred, session_id, int(user_nik)),
    )
    return Session(**rows[0]) if rows else None


def touch_session(user_nik: str, session_id: str) -> None:
    run_admin(
        "update sessions set updated_at = now() where id = %s and user_nik = %s",
        (session_id, int(user_nik)),
    )


def delete_session(user_nik: str, session_id: str) -> bool:
    rows = run_admin(
        "delete from sessions where id = %s and user_nik = %s returning id",
        (session_id, int(user_nik)),
    )
    return bool(rows)

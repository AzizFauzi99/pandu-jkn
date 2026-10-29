import uuid
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TITLE = "Percakapan baru"


def _now() -> datetime:
    return datetime.now(ZoneInfo("Asia/Jakarta"))


@dataclass
class Session:
    id: str
    user_id: str
    title: str
    starred: bool = False
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


# Penyimpanan sementara di memori. Ganti isi fungsi-fungsi di bawah dengan
# query database setelah skema session dari Database management tersedia.
# Semua fungsi menyaring berdasarkan user_id, jadi session milik user lain
# dianggap tidak ada.
_sessions: dict[str, Session] = {}


def create_session(user_id: str, title: str | None = None) -> Session:
    session = Session(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=(title or "").strip() or DEFAULT_TITLE,
    )
    _sessions[session.id] = session
    return session


def list_sessions(user_id: str, starred: bool | None = None) -> list[Session]:
    sessions = [s for s in _sessions.values() if s.user_id == user_id]
    if starred is not None:
        sessions = [s for s in sessions if s.starred == starred]
    return sorted(sessions, key=lambda s: s.updated_at, reverse=True)


def get_session(user_id: str, session_id: str) -> Session | None:
    session = _sessions.get(session_id)
    return session if session and session.user_id == user_id else None


def update_title(user_id: str, session_id: str, title: str) -> Session | None:
    session = get_session(user_id, session_id)
    if session:
        session.title = title.strip()
        session.updated_at = _now()
    return session


def set_starred(user_id: str, session_id: str, starred: bool) -> Session | None:
    session = get_session(user_id, session_id)
    if session:
        session.starred = starred
    return session


def delete_session(user_id: str, session_id: str) -> bool:
    if get_session(user_id, session_id) is None:
        return False
    del _sessions[session_id]
    return True

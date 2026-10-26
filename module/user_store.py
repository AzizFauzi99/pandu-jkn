import os
import uuid
from dataclasses import dataclass

from utils.security import hash_password


@dataclass
class User:
    id: str
    email: str
    password_hash: str


# Penyimpanan sementara di memori. Ganti isi fungsi-fungsi di bawah dengan
# query database setelah skema user dari Database management tersedia.
_users_by_email: dict[str, User] = {}


def get_user_by_email(email: str) -> User | None:
    return _users_by_email.get(email.strip().lower())


def get_user_by_id(user_id: str) -> User | None:
    return next((u for u in _users_by_email.values() if u.id == user_id), None)


def create_user(email: str, password: str) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email.strip().lower(),
        password_hash=hash_password(password),
    )
    _users_by_email[user.email] = user
    return user


def seed_dev_user() -> None:
    """Buat user uji lokal dari .env bila DEV_USER_EMAIL dan DEV_USER_PASSWORD diisi."""
    email = os.getenv("DEV_USER_EMAIL")
    password = os.getenv("DEV_USER_PASSWORD")
    if email and password and not get_user_by_email(email):
        create_user(email, password)

from dataclasses import dataclass

from module.db import connect


@dataclass
class User:
    id: str  # email; dipakai sebagai `sub` di JWT dan kunci data milik user
    email: str
    password_hash: str
    nik: int
    nama_lengkap: str


# Tabel `users` dikelola Database management (register). Modul ini hanya membaca.
def get_user_by_email(email: str) -> User | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT email, password_hash, nik, nama_lengkap FROM users "
            "WHERE lower(email) = %s",
            (email.strip().lower(),),
        ).fetchone()
    if row is None:
        return None
    email, password_hash, nik, nama_lengkap = row
    return User(
        id=email, email=email, password_hash=password_hash, nik=nik,
        nama_lengkap=nama_lengkap,
    )


def get_user_by_id(user_id: str) -> User | None:
    return get_user_by_email(user_id)

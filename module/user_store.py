from dataclasses import dataclass

from utils.db import run_admin, run_select
from utils.security import hash_password


@dataclass
class User:
    id: str
    email: str
    password_hash: str


def _to_user(row: dict) -> User:
    return User(id=str(row["nik"]), email=row["email"], password_hash=row["password_hash"])


def get_user_by_email(email: str) -> User | None:
    rows = run_admin(
        "select nik, email, password_hash from users where email = %s",
        (email.strip().lower(),),
    )
    return _to_user(rows[0]) if rows else None


def get_user_by_id(user_id: str) -> User | None:
    rows = run_admin(
        "select nik, email, password_hash from users where nik = %s", (user_id,)
    )
    return _to_user(rows[0]) if rows else None


def nik_terdaftar_di_ktp(nik: str) -> bool:
    rows = run_select("select 1 from bpjs_kepesertaan where pstv01 = %s", (int(nik),), limit=1)
    return bool(rows)


def create_user(nama_lengkap: str, email: str, no_hp: str, nik: str, password: str) -> User:
    rows = run_admin(
        """
        insert into users (nik, nama_lengkap, email, no_hp, password_hash)
        values (%s, %s, %s, %s, %s)
        returning nik, email, password_hash
        """,
        (nik, nama_lengkap.strip(), email.strip().lower(), no_hp.strip(), hash_password(password)),
    )
    return _to_user(rows[0])


def update_profile(nik: str, profile: dict) -> dict:
    rows = run_admin(
        """
        update users
        set tanggal_lahir = %(tanggal_lahir)s,
            jenis_kelamin = %(jenis_kelamin)s,
            tinggi_badan = %(tinggi_badan)s,
            berat_badan = %(berat_badan)s,
            alergi_makanan = %(alergi_makanan)s,
            riwayat_penyakit = %(riwayat_penyakit)s
        where nik = %(nik)s
        returning nik, nama_lengkap, email, no_hp, tanggal_lahir, jenis_kelamin,
                  tinggi_badan, berat_badan, alergi_makanan, riwayat_penyakit
        """,
        {**profile, "nik": nik},
    )
    return rows[0]

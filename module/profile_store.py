import json
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel, Field, StringConstraints, field_validator

from utils.db import get_conninfo

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ProfileData(BaseModel):
    nama_lengkap: str | None = Field(default=None, max_length=150)
    nomor_hp: str | None = Field(
        default=None, description="Format Indonesia, mis. 081234567890 atau +6281234567890"
    )
    tanggal_lahir: date | None = None
    jenis_kelamin: Literal["laki-laki", "perempuan"] | None = None
    nik: str | None = Field(default=None, description="Angka, harus terdaftar di bpjs_kepesertaan (pstv01)")
    tinggi_badan_cm: float | None = Field(default=None, ge=30, le=272)
    berat_badan_kg: float | None = Field(default=None, ge=2, le=700)
    alergi_makanan: list[ShortText] = Field(default_factory=list, max_length=50)
    riwayat_penyakit: list[ShortText] = Field(default_factory=list, max_length=50)
    nomor_kartu_bpjs: str | None = Field(default=None, description="13 digit")

    @field_validator("nama_lengkap")
    @classmethod
    def _strip_name(cls, v: str | None) -> str | None:
        return v.strip() or None if v else None

    @field_validator("nomor_hp")
    @classmethod
    def _check_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        digits = v.strip().replace(" ", "").replace("-", "")
        body = digits[1:] if digits.startswith("+") else digits
        if not body.isdigit() or not (
            digits.startswith(("08", "+628", "628")) and 10 <= len(body) <= 15
        ):
            raise ValueError("Nomor HP harus berformat Indonesia, mis. 081234567890")
        return digits

    @field_validator("nik")
    @classmethod
    def _check_nik(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not (v.isascii() and v.isdigit() and len(v) <= 16):
            raise ValueError("NIK harus berupa angka (maks. 16 digit)")
        return v

    @field_validator("nomor_kartu_bpjs")
    @classmethod
    def _check_bpjs(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not (v.isascii() and v.isdigit() and len(v) == 13):
            raise ValueError("Nomor kartu BPJS harus 13 digit angka")
        return v

    @field_validator("tanggal_lahir")
    @classmethod
    def _check_birthdate(cls, v: date | None) -> date | None:
        if v is not None and (v > date.today() or v.year < 1900):
            raise ValueError("Tanggal lahir tidak valid")
        return v


class ProfileIncomplete(Exception):
    """Field wajib untuk membuat/mengubah baris users belum terisi."""


class ProfileConflict(Exception):
    """NIK sudah dipakai akun lain."""


class NikNotFound(Exception):
    """NIK tidak terdaftar di bpjs_kepesertaan."""


_GENDER_TO_DB = {"laki-laki": "L", "perempuan": "P"}
_GENDER_FROM_DB = {v: k for k, v in _GENDER_TO_DB.items()}


def _load_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except ValueError:
        pass
    return [x.strip() for x in raw.split(",") if x.strip()]


def _num(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def get_profile(email: str) -> ProfileData:
    with psycopg.connect(get_conninfo(), connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("select * from users where email = %s", (email,))
            row = cur.fetchone()
    if row is None:
        return ProfileData()
    return ProfileData(
        nama_lengkap=row["nama_lengkap"],
        nomor_hp=row["no_hp"],
        tanggal_lahir=row["tanggal_lahir"],
        jenis_kelamin=_GENDER_FROM_DB.get(row["jenis_kelamin"]),
        nik=str(row["nik"]),
        tinggi_badan_cm=_num(row["tinggi_badan"]),
        berat_badan_kg=_num(row["berat_badan"]),
        alergi_makanan=_load_list(row["alergi_makanan"]),
        riwayat_penyakit=_load_list(row["riwayat_penyakit"]),
    )


def save_profile(email: str, password_hash: str, profile: ProfileData) -> ProfileData:
    """Ganti seluruh profil baris users milik email ini (insert bila belum ada)."""
    with psycopg.connect(get_conninfo(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("select nik from users where email = %s", (email,))
            existing = cur.fetchone()
            nik = int(profile.nik) if profile.nik else (existing[0] if existing else None)
            if nik is None or not profile.nama_lengkap:
                raise ProfileIncomplete("nik dan nama_lengkap wajib diisi")
            values = (
                nik,
                profile.nama_lengkap,
                profile.nomor_hp,
                profile.tanggal_lahir,
                _GENDER_TO_DB.get(profile.jenis_kelamin),
                profile.tinggi_badan_cm,
                profile.berat_badan_kg,
                json.dumps(profile.alergi_makanan, ensure_ascii=False),
                json.dumps(profile.riwayat_penyakit, ensure_ascii=False),
            )
            try:
                if existing:
                    cur.execute(
                        "update users set nik=%s, nama_lengkap=%s, no_hp=%s, tanggal_lahir=%s,"
                        " jenis_kelamin=%s, tinggi_badan=%s, berat_badan=%s,"
                        " alergi_makanan=%s, riwayat_penyakit=%s where email=%s",
                        (*values, email),
                    )
                else:
                    cur.execute(
                        "insert into users (nik, nama_lengkap, no_hp, tanggal_lahir,"
                        " jenis_kelamin, tinggi_badan, berat_badan, alergi_makanan,"
                        " riwayat_penyakit, email, password_hash)"
                        " values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (*values, email, password_hash),
                    )
            except psycopg.errors.ForeignKeyViolation:
                raise NikNotFound("NIK tidak terdaftar di data kepesertaan BPJS") from None
            except psycopg.errors.UniqueViolation:
                raise ProfileConflict("NIK sudah dipakai akun lain") from None
    return get_profile(email)

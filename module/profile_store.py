from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ProfileData(BaseModel):
    nama_lengkap: str | None = Field(default=None, max_length=150)
    nomor_hp: str | None = Field(
        default=None, description="Format Indonesia, mis. 081234567890 atau +6281234567890"
    )
    tanggal_lahir: date | None = None
    jenis_kelamin: Literal["laki-laki", "perempuan"] | None = None
    nik: str | None = Field(default=None, description="16 digit")
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
        if not (v.isascii() and v.isdigit() and len(v) == 16):
            raise ValueError("NIK harus 16 digit angka")
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


# Penyimpanan sementara di memori, kunci = user id. Ganti isi fungsi di bawah
# dengan query database setelah skema dari Database management tersedia.
_profiles: dict[str, ProfileData] = {}


def get_profile(user_id: str) -> ProfileData:
    return _profiles.get(user_id) or ProfileData()


def save_profile(user_id: str, profile: ProfileData) -> ProfileData:
    _profiles[user_id] = profile
    return profile

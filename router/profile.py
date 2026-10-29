from datetime import date
from decimal import Decimal

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from module.user_store import User, update_profile
from router.auth import get_current_user

router = APIRouter(tags=["profile"])


class ProfileRequest(BaseModel):
    tanggal_lahir: date
    jenis_kelamin: str = Field(pattern=r"^[LP]$")
    tinggi_badan: Decimal = Field(gt=0)
    berat_badan: Decimal = Field(gt=0)
    alergi_makanan: str | None = None
    riwayat_penyakit: str | None = None


@router.post("/profile")
def post_profile(request: ProfileRequest, user: User = Depends(get_current_user)):
    try:
        return update_profile(user.id, request.model_dump())
    except psycopg.Error:
        raise HTTPException(status_code=502, detail="Gagal menghubungi database")

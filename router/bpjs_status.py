import psycopg
from fastapi import APIRouter, HTTPException

from module.bpjs_status import cek_status

router = APIRouter(tags=["bpjs"])


@router.get("/bpjs-status/{user_id}")
def get_bpjs_status(user_id: str):
    try:
        return cek_status(user_id)
    except psycopg.Error:
        raise HTTPException(status_code=502, detail="Gagal menghubungi database")

import logging
from pathlib import Path

import psycopg
from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from module.bpjs_status import cek_status
from utils.db import is_select_only, run_select

logger = logging.getLogger("uvicorn.error")

knowledge_file = (
    Path(__file__).resolve().parent.parent / "knowledge" / "bpjs_table_knowledge.md"
)


@tool
def baca_knowledge() -> str:
    """Baca penjelasan database BPJS: daftar tabel, arti kolom, cara dekode kode,
    dan contoh query. Panggil ini sebelum menyusun SQL."""
    logger.info("tool baca_knowledge")
    return knowledge_file.read_text()


@tool
def query_database(sql: str) -> list[dict] | dict:
    """Jalankan query SELECT read-only ke database BPJS.

    Args:
        sql: Satu pernyataan SELECT. Sertakan LIMIT dan hindari SELECT * pada tabel besar.
    """
    logger.info("tool query_database sql=%r", sql)
    if not is_select_only(sql):
        return {
            "error": "Hanya satu pernyataan SELECT atau WITH yang diizinkan.",
            "saran": "Tulis ulang sebagai satu SELECT tanpa tanda titik koma di tengah.",
        }

    try:
        return run_select(sql)
    except psycopg.errors.QueryCanceled:
        logger.info("tool query_database timeout")
        return {
            "error": "Query melebihi batas waktu 60 detik.",
            "saran": "Persempit rentang tanggal, kurangi JOIN, atau agregasi lebih dulu.",
        }
    except psycopg.Error as e:
        logger.info("tool query_database gagal: %s", e)
        return {
            "error": str(e),
            "saran": "Periksa nama tabel dan kolom lewat baca_knowledge, lalu coba lagi.",
        }


@tool
def get_bpjs_status(runtime: ToolRuntime) -> dict:
    """Cek status kepesertaan JKN dan kelayakan mengikuti BPJS milik pengguna yang sedang login."""
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info("tool get_bpjs_status user_nik=%r", user_nik)
    try:
        return cek_status(user_nik)
    except psycopg.Error as e:
        logger.info("tool get_bpjs_status gagal: %s", e)
        return {
            "error": str(e),
            "saran": "Sampaikan bahwa data kepesertaan sedang tidak dapat diakses.",
        }


bpjs_tools = [baca_knowledge, query_database, get_bpjs_status]

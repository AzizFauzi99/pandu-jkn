import logging

import psycopg
from langchain_core.tools import tool

from utils.db import is_select_only, run_select
from utils.helpdesk_prompt import helpdesk_prompt

logger = logging.getLogger("uvicorn.error")


@tool
def list_tables() -> list[dict]:
    """Daftar tabel di database BPJS beserta perkiraan jumlah barisnya."""
    logger.info("tool list_tables")
    return run_select(
        """
        select c.relname as nama_tabel,
               cast(c.reltuples as bigint) as perkiraan_baris
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where c.relkind = 'r' and n.nspname = 'public'
        order by c.relname
        """
    )


@tool
def describe_table(nama_tabel: str) -> list[dict]:
    """Lihat kolom, tipe data, dan jumlah kode label yang tersedia untuk sebuah tabel.

    Args:
        nama_tabel: Nama tabel, misalnya "bpjs_kepesertaan".
    """
    logger.info("tool describe_table nama_tabel=%r", nama_tabel)
    return run_select(
        """
        select col.column_name as kolom,
               col.data_type as tipe,
               count(lookup.code_value) as jumlah_kode
        from information_schema.columns col
        left join bpjs_metadata_lookup lookup
               on lookup.variable_name = upper(col.column_name)
        where col.table_schema = 'public' and col.table_name = %s
        group by col.ordinal_position, col.column_name, col.data_type
        order by col.ordinal_position
        """,
        (nama_tabel,),
        limit=100,
    )


@tool
def cari_kode(variable_name: str, kata_kunci: str = "") -> list[dict]:
    """Cari arti kode suatu kolom di tabel lookup, atau terjemahkan istilah jadi kode.

    Args:
        variable_name: Nama kolom dalam huruf besar, misalnya "PSTV09".
        kata_kunci: Kata pada label yang dicari, misalnya "jawa". Kosongkan untuk semua.
    """
    logger.info("tool cari_kode variable_name=%r kata_kunci=%r", variable_name, kata_kunci)
    return run_select(
        """
        select code_value as kode, label_text as label
        from bpjs_metadata_lookup
        where variable_name = upper(%s) and label_text ilike %s
        order by code_value
        """,
        (variable_name, f"%{kata_kunci}%"),
    )


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
    except psycopg.Error as e:
        logger.info("tool query_database gagal: %s", e)
        return {
            "error": str(e),
            "saran": "Periksa nama tabel dan kolom lewat describe_table, lalu coba lagi.",
        }


helpdesk_subagent = {
    "name": "helpdesk",
    "description": (
        "Tangani pertanyaan administratif dan statistik seputar BPJS Kesehatan/JKN: "
        "kepesertaan, segmen peserta, kelas rawat, status aktif, badan usaha, "
        "kunjungan faskes, serta sebaran menurut wilayah. Gunakan subagent ini untuk "
        "pertanyaan yang jawabannya perlu diambil dari database data sampel BPJS. "
        "Jangan gunakan untuk keluhan atau gejala kesehatan pengguna."
    ),
    "system_prompt": helpdesk_prompt,
    "tools": [list_tables, describe_table, cari_kode, query_database],
}

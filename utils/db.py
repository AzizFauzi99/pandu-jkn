import os
from decimal import Decimal

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def is_select_only(sql: str):
    """Pastikan SQL hanya satu pernyataan baca."""
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:
        return False
    return cleaned.lower().startswith(("select", "with"))


def run_admin(sql: str, params: tuple | None = None):
    """Jalankan query dengan koneksi yang boleh menulis (tabel users)."""
    with psycopg.connect(os.getenv("DATABASE_ADMIN"), connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            return [
                {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
                for row in cur.fetchall()
            ]


def run_select(sql: str, params: tuple | None = None, limit: int = 50):
    with psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=10) as conn:
        conn.read_only = True
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("set statement_timeout = 60000")
            cur.execute(sql, params)
            return [
                {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
                for row in cur.fetchmany(limit)
            ]

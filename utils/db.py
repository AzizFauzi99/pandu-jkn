import os
from decimal import Decimal

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

load_dotenv()


def get_conninfo() -> str:
    """DATABASE_URL bila ada, jika tidak dirakit dari DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return make_conninfo(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def is_select_only(sql: str):
    """Pastikan SQL hanya satu pernyataan baca."""
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:
        return False
    return cleaned.lower().startswith(("select", "with"))


def run_select(sql: str, params: tuple | None = None, limit: int = 50):
    with psycopg.connect(get_conninfo(), connect_timeout=10) as conn:
        conn.read_only = True
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("set statement_timeout = 60000")
            cur.execute(sql, params)
            return [
                {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}
                for row in cur.fetchmany(limit)
            ]

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def connect() -> psycopg.Connection:
    """Buka koneksi baru ke Postgres. Dipakai dengan `with`, yang meng-commit saat keluar."""
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5)

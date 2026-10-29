import logging
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("uvicorn.error")

# Data faskes hanya memuat Puskesmas dan Rumah sakit.
TIPE_BY_KEBUTUHAN = {
    "puskesmas": "puskesmas",
    "klinik": "puskesmas",
    "igd": "rumah_sakit",
    "rumah sakit": "rumah_sakit",
}

# Awalan administratif yang ditulis berbeda-beda di kolom alamat.
STOPWORDS = {"kota", "kabupaten", "kab", "kab.", "kec", "kec.", "kecamatan"}

QUERY = """
SELECT nama_faskes, jenis_faskes, alamat, telepon, latitude, longitude
FROM faskes
WHERE tipe = %(tipe)s {filters}
ORDER BY (nama_faskes ~* '^(RSUD|RSUP)') DESC, nama_faskes
LIMIT %(limit)s
"""


def _maps_url(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def cari_faskes_db(lokasi: str, kebutuhan: str = "puskesmas", limit: int = 5) -> list[dict]:
    """Cari faskes yang alamatnya memuat semua kata pada `lokasi`.

    Mengembalikan list kosong bila tidak ada yang cocok atau lokasi kosong.
    """
    tipe = TIPE_BY_KEBUTUHAN.get(kebutuhan.strip().lower(), "puskesmas")
    tokens = [t for t in lokasi.lower().split() if t not in STOPWORDS]
    if not tokens:
        return []

    params = {"tipe": tipe, "limit": limit}
    clauses = []
    for i, token in enumerate(tokens):
        params[f"t{i}"] = f"%{token}%"
        clauses.append(f"AND alamat ILIKE %(t{i})s")
    sql = QUERY.format(filters=" ".join(clauses))

    with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return [
        {
            "nama": nama,
            "jenis": jenis,
            "alamat": alamat,
            "telepon": telepon,
            "peta": _maps_url(lat, lng),
        }
        for nama, jenis, alamat, telepon, lat, lng in rows
    ]

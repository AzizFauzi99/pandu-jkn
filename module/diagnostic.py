import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import psycopg
from langchain_core.tools import tool

from module.bpjs_status import cek_status
from module.faskes import cari_faskes_db
from utils.diagnostic_prompt import diagnostic_prompt

logger = logging.getLogger("uvicorn.error")

RED_FLAGS = {
    "nyeri dada": "Nyeri dada berpotensi masalah jantung",
    "sesak": "Sesak napas",
    "sulit bernapas": "Sulit bernapas",
    "tidak sadar": "Penurunan kesadaran",
    "pingsan": "Penurunan kesadaran",
    "kejang": "Kejang",
    "lumpuh": "Kelumpuhan mendadak (curiga stroke)",
    "bicara pelo": "Bicara pelo mendadak (curiga stroke)",
    "wajah mencong": "Wajah mencong mendadak (curiga stroke)",
    "muntah darah": "Muntah darah",
    "batuk darah": "Batuk darah",
    "bab hitam": "Perdarahan saluran cerna",
    "perdarahan hebat": "Perdarahan hebat",
    "darah tidak berhenti": "Perdarahan hebat",
    "keracunan": "Keracunan",
    "overdosis": "Overdosis",
    "ingin bunuh diri": "Risiko bunuh diri",
    "menyakiti diri": "Risiko menyakiti diri",
    "reaksi alergi berat": "Reaksi alergi berat",
    "bibir bengkak": "Kemungkinan anafilaksis",
}

@tool
def check_red_flags(keluhan: str) -> dict:
    """Periksa teks keluhan pengguna terhadap tanda bahaya (red flag) gawat darurat.

    Args:
        keluhan: Teks keluhan pengguna apa adanya.
    """
    logger.info("tool check_red_flags keluhan=%r", keluhan)
    text = keluhan.lower()
    found = sorted({desc for key, desc in RED_FLAGS.items() if key in text})
    return {
        "level": "emergency" if found else "tidak_terdeteksi",
        "tanda_bahaya": found,
        "catatan": "Pengecekan berbasis kata kunci; tetap nilai konteks keluhan.",
    }


@tool
def cari_faskes(kota: str, kebutuhan: str = "puskesmas") -> list[dict]:
    """Cari fasilitas kesehatan berdasarkan lokasi dan kebutuhan.

    Args:
        kota: Nama kota, kabupaten, atau kecamatan pengguna.
        kebutuhan: "puskesmas", "klinik", atau "igd" (gawat darurat).
    """
    logger.info("tool cari_faskes kota=%r kebutuhan=%r", kota, kebutuhan)
    try:
        hasil = cari_faskes_db(kota, kebutuhan)
    except Exception:
        logger.exception("cari_faskes gagal mengakses database")
        return [
            {
                "ditemukan": False,
                "pesan": (
                    "Pencarian faskes sedang bermasalah. Minta maaf kepada pengguna, "
                    "arahkan ke Mobile JKN (FKTP terdaftar) atau IGD terdekat bila darurat."
                ),
            }
        ]
    return hasil or [
        {
            "ditemukan": False,
            "pesan": (
                "Sampaikan teks berikut kepada pengguna apa adanya, jangan "
                "menambah pertanyaan apa pun: "
                f"'Maaf, data faskes di {kota} belum tersedia di sistem saya. "
                "Untuk berobat dengan JKN, cek FKTP terdaftar Anda di Mobile JKN. "
                "Jika kondisi darurat, segera ke IGD terdekat atau hubungi 119.'"
            ),
        }
    ]


@tool
def get_bpjs_status(user_id: str) -> dict:
    """Cek status kepesertaan JKN dan apakah pengguna dapat mengikuti BPJS.

    Args:
        user_id: Nomor ID peserta pada kartu JKN.
    """
    logger.info("tool get_bpjs_status user_id=%r", user_id)
    try:
        return cek_status(user_id)
    except psycopg.Error as e:
        logger.info("tool get_bpjs_status gagal: %s", e)
        return {
            "error": str(e),
            "saran": "Sampaikan bahwa data kepesertaan sedang tidak dapat diakses.",
        }


@tool
def buat_ringkasan_dokter(
    keluhan_utama: str,
    onset: str,
    gejala_penyerta: list[str],
    level_triase: str,
    saran_diberikan: list[str],
    usia: int | None = None,
    jenis_kelamin: str | None = None,
    riwayat_penyakit: list[str] | None = None,
    alergi: list[str] | None = None,
    obat_saat_ini: list[str] | None = None,
) -> dict:
    """Susun ringkasan terstruktur percakapan untuk diteruskan ke dokter.

    Args:
        keluhan_utama: Keluhan utama pengguna.
        onset: Sejak kapan dan berapa lama keluhan berlangsung.
        gejala_penyerta: Gejala lain yang menyertai.
        level_triase: "emergency", "segera", atau "mandiri".
        saran_diberikan: Saran pertolongan pertama yang sudah diberikan.
        usia: Usia pengguna.
        jenis_kelamin: Jenis kelamin pengguna.
        riwayat_penyakit: Riwayat penyakit pengguna.
        alergi: Alergi pengguna.
        obat_saat_ini: Obat yang sedang dikonsumsi.
    """
    return {
        "dibuat_pada": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds"),
        "pasien": {"usia": usia, "jenis_kelamin": jenis_kelamin},
        "keluhan_utama": keluhan_utama,
        "onset": onset,
        "gejala_penyerta": gejala_penyerta,
        "riwayat_penyakit": riwayat_penyakit or [],
        "alergi": alergi or [],
        "obat_saat_ini": obat_saat_ini or [],
        "level_triase": level_triase,
        "saran_diberikan": saran_diberikan,
    }


diagnostic_subagent = {
    "name": "diagnostic",
    "description": (
        "Tangani SEMUA pesan terkait kesehatan pengguna: keluhan dan gejala, "
        "pertolongan pertama, pencarian faskes/Puskesmas/klinik/IGD/dokter di "
        "suatu kota, rujukan, status kepesertaan saat berobat, dan ringkasan untuk "
        "dokter. Juga tangani pesan lanjutan dalam percakapan yang sama, termasuk "
        "saat pengguna hanya menyebut lokasi atau melengkapi data keluhan. "
        "Bertanya balik jika data kurang."
    ),
    "system_prompt": diagnostic_prompt,
    "tools": [check_red_flags, cari_faskes, get_bpjs_status, buat_ringkasan_dokter],
}

import logging
from pathlib import Path
from typing import Literal

import psycopg
from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from module.bpjs_riwayat import biaya_klaim, kunjungan_pengguna, ringkasan_diagnosis
from module.bpjs_status import cek_status
from module.profile_store import get_profile
from module.user_store import get_user_by_id
from utils.db import is_select_only, run_select

logger = logging.getLogger("uvicorn.error")

knowledge_file = (
    Path(__file__).resolve().parent.parent / "knowledge" / "bpjs_table_knowledge.md"
)
panduan_dir = Path(__file__).resolve().parent.parent / "knowledge" / "panduan_bpjs_kesehatan"


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


def data_tidak_dapat_diakses(nama_tool: str, error: psycopg.Error):
    logger.info("tool %s gagal: %s", nama_tool, error)
    return {
        "error": "Data tidak dapat diakses saat ini.",
        "saran": "Sampaikan hal ini kepada pengguna dan sarankan mencoba lagi nanti.",
    }


@tool
def get_bpjs_status(runtime: ToolRuntime) -> dict:
    """Cek status kepesertaan JKN dan kelayakan mengikuti BPJS milik pengguna yang sedang login."""
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info("tool get_bpjs_status user_nik=%r", user_nik)
    try:
        return cek_status(user_nik)
    except psycopg.Error as e:
        return data_tidak_dapat_diakses("get_bpjs_status", e)


@tool
def cari_kunjungan(
    runtime: ToolRuntime,
    layanan: Literal["semua", "faskes_pertama", "rawat_jalan_rs", "rawat_inap_rs"] = "semua",
    dari_tanggal: str | None = None,
    sampai_tanggal: str | None = None,
    jumlah: int = 10,
) -> dict:
    """Cari riwayat kunjungan milik pengguna yang sedang login ke faskes tingkat pertama dan
    rumah sakit, urut dari yang terbaru. Hasil memuat jumlah total kunjungan yang cocok.
    Untuk rumah sakit tersedia juga diagnosis sekunder, lama rawat, dan biaya.

    Args:
        layanan: "faskes_pertama", "rawat_jalan_rs", "rawat_inap_rs", atau "semua".
        dari_tanggal: Tanggal awal format YYYY-MM-DD. Kosongkan bila tidak dibatasi.
        sampai_tanggal: Tanggal akhir format YYYY-MM-DD. Kosongkan bila tidak dibatasi.
        jumlah: Banyak kunjungan terbaru yang ditampilkan per jenis, maksimal 30.
    """
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info(
        "tool cari_kunjungan user_nik=%r layanan=%r dari=%r sampai=%r jumlah=%r",
        user_nik, layanan, dari_tanggal, sampai_tanggal, jumlah,
    )
    try:
        return kunjungan_pengguna(user_nik, layanan, dari_tanggal, sampai_tanggal, jumlah)
    except psycopg.Error as e:
        return data_tidak_dapat_diakses("cari_kunjungan", e)


@tool
def ringkasan_riwayat_diagnosis(runtime: ToolRuntime) -> dict:
    """Diagnosis yang paling sering muncul pada kunjungan pengguna yang sedang login ke faskes
    tingkat pertama dan rumah sakit, termasuk diagnosis sekunder (penyakit penyerta)."""
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info("tool ringkasan_riwayat_diagnosis user_nik=%r", user_nik)
    try:
        return ringkasan_diagnosis(user_nik)
    except psycopg.Error as e:
        return data_tidak_dapat_diakses("ringkasan_riwayat_diagnosis", e)


@tool
def get_biaya_klaim(runtime: ToolRuntime) -> dict:
    """Ringkasan biaya klaim yang dibayar BPJS atas perawatan pengguna yang sedang login."""
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info("tool get_biaya_klaim user_nik=%r", user_nik)
    try:
        return biaya_klaim(user_nik)
    except psycopg.Error as e:
        return data_tidak_dapat_diakses("get_biaya_klaim", e)


@tool
def get_profil_akun(runtime: ToolRuntime) -> dict:
    """Data profil akun milik pengguna yang sedang login: nama, tanggal lahir, jenis kelamin,
    tinggi dan berat badan, alergi makanan, serta riwayat penyakit."""
    user_nik = runtime.config["configurable"]["user_nik"]
    logger.info("tool get_profil_akun user_nik=%r", user_nik)
    try:
        user = get_user_by_id(user_nik)
        return get_profile(user.email).model_dump(mode="json")
    except psycopg.Error as e:
        return data_tidak_dapat_diakses("get_profil_akun", e)


@tool
def baca_panduan(topik: str = "") -> str:
    """Baca panduan prosedur BPJS, misalnya cara membayar iuran, mengganti faskes, kartu hilang,
    dokumen pendaftaran, dan kanal resmi. Kosongkan topik untuk melihat daftar panduan beserta
    aturan menjawabnya; baca daftar itu sebelum memilih topik.

    Args:
        topik: Nama panduan persis seperti pada daftar yang tersedia.
    """
    logger.info("tool baca_panduan topik=%r", topik)
    tersedia = {berkas.stem: berkas for berkas in panduan_dir.glob("*.md")}
    if topik in tersedia:
        return tersedia[topik].read_text()
    if not tersedia:
        return (
            "Belum ada panduan tertulis. Jawaban Anda hanya boleh menyampaikan bahwa panduan "
            "untuk hal ini belum tersedia dan mengarahkan pengguna ke Mobile JKN atau Care "
            "Center 165. Dilarang menyebut langkah, menu aplikasi, syarat, atau jangka waktu "
            "dari ingatan Anda."
        )
    petunjuk = panduan_dir / "README.txt"
    isi_petunjuk = petunjuk.read_text() if petunjuk.exists() else ""
    return f"{isi_petunjuk}\n\nTopik yang tersedia: {', '.join(sorted(tersedia))}"


bpjs_tools = [
    get_bpjs_status,
    cari_kunjungan,
    ringkasan_riwayat_diagnosis,
    get_biaya_klaim,
    get_profil_akun,
    baca_panduan,
]

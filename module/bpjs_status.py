from utils.db import run_select

peta_status = {
    1: ("sudah_aktif", "Tidak ada tindakan yang diperlukan."),
    2: ("tidak_bisa", "Ahli waris dapat mengurus penonaktifan di kantor BPJS terdekat."),
    3: ("bisa_daftar", "Daftar ulang sebagai peserta mandiri (PBPU) lewat Mobile JKN atau kantor BPJS."),
    4: ("bisa_daftar", "Daftar ulang sebagai peserta mandiri (PBPU) lewat Mobile JKN atau kantor BPJS."),
    5: ("bisa_daftar", "Perjanjian kerja sama berakhir. Daftar ulang sebagai peserta mandiri (PBPU)."),
    6: ("perlu_verifikasi", "Hubungi Care Center 165 untuk memastikan alasan tidak ditanggung."),
    7: ("perlu_tindakan", "Selesaikan penangguhan kepesertaan di kantor BPJS terdekat."),
    8: ("perlu_tindakan", "Lunasi tunggakan iuran lewat Mobile JKN. Kepesertaan aktif kembali setelah pembayaran."),
    9: ("perlu_tindakan", "Badan usaha menunggak iuran. Hubungi bagian kepegawaian atau kantor BPJS."),
    10: ("perlu_tindakan", "Lunasi iuran bulan berjalan agar kepesertaan tidak berakhir."),
    11: ("perlu_tindakan", "Lanjutkan proses aktivasi kepesertaan di kantor BPJS terdekat."),
    12: ("perlu_tindakan", "Selesaikan penangguhan pembayaran iuran lewat Mobile JKN atau kantor BPJS."),
    13: ("perlu_tindakan", "Bawa KTP dan Kartu Keluarga ke kantor BPJS untuk penggabungan data ganda."),
    14: ("perlu_verifikasi", "Izin tinggal habis. Konfirmasi ke kantor BPJS terdekat."),
    15: ("bisa_daftar", "Usia melewati batas tanggungan anak PPU. Daftar sebagai peserta mandiri (PBPU)."),
    16: ("bisa_daftar", "Usia melewati batas tanggungan anak PPU. Daftar sebagai peserta mandiri (PBPU)."),
    18: ("perlu_verifikasi", "Hubungi Care Center 165 untuk konfirmasi status kepesertaan."),
    19: ("perlu_verifikasi", "Hubungi Care Center 165 untuk konfirmasi status kepesertaan veteran."),
    20: ("perlu_verifikasi", "Peserta tercatat berada di luar negeri. Hubungi Care Center 165."),
}

status_tak_dikenal = (
    "perlu_verifikasi",
    "Status kepesertaan tidak dapat dipastikan. Hubungi Care Center 165 atau cek Mobile JKN.",
)

bisa_ikut = {
    "sudah_aktif": True,
    "bisa_daftar": True,
    "perlu_tindakan": True,
    "tidak_bisa": False,
    "perlu_verifikasi": None,
}


def _hasil(user_id: str, kategori: str, alasan: str, tindakan: str, baris: dict | None = None):
    return {
        "userId": user_id,
        "ditemukan": baris is not None,
        "statusKode": baris["status_kode"] if baris else None,
        "status": baris["status"] if baris else None,
        "segmen": baris["segmen"] if baris else None,
        "kelasRawat": baris["kelas_rawat"] if baris else None,
        "bisaIkut": bisa_ikut[kategori],
        "kategori": kategori,
        "alasan": alasan,
        "tindakan": tindakan,
    }


def cek_status(user_id: str):
    """Cek kepesertaan JKN berdasarkan ID peserta (pstv01) dan simpulkan kelayakannya."""
    bersih = user_id.strip()
    if not bersih.isdigit():
        return _hasil(
            user_id,
            "perlu_verifikasi",
            "Format nomor peserta tidak valid, hanya menerima angka.",
            "Periksa kembali nomor peserta pada kartu JKN atau aplikasi Mobile JKN.",
        )

    baris = run_select(
        """
        select k.pstv17 as status_kode,
               status.label_text as status,
               segmen.label_text as segmen,
               kelas.label_text as kelas_rawat
        from bpjs_kepesertaan k
        left join bpjs_metadata_lookup status
               on status.variable_name = 'PSTV17' and status.code_value = k.pstv17
        left join bpjs_metadata_lookup segmen
               on segmen.variable_name = 'PSTV08' and segmen.code_value = k.pstv08
        left join bpjs_metadata_lookup kelas
               on kelas.variable_name = 'PSTV07' and kelas.code_value = k.pstv07
        where k.pstv01 = %s
        """,
        (int(bersih),),
        limit=1,
    )

    if not baris:
        return _hasil(
            user_id,
            "bisa_daftar",
            "Nomor peserta tidak ditemukan pada data sampel. Ini belum tentu berarti "
            "belum terdaftar, karena data yang tersedia hanya sebagian dari peserta nasional.",
            "Pastikan status sebenarnya lewat Mobile JKN atau Care Center 165. "
            "Bila memang belum terdaftar, pendaftaran dapat dilakukan lewat kanal yang sama.",
        )

    data = baris[0]
    kategori, tindakan = peta_status.get(data["status_kode"], status_tak_dikenal)
    label = data["status"] or f"kode {data['status_kode']}"
    return _hasil(user_id, kategori, f"Status kepesertaan tercatat: {label}.", tindakan, data)

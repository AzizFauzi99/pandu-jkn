from module.bpjs_tools import bpjs_tools
from utils.helpdesk_prompt import helpdesk_prompt

helpdesk_subagent = {
    "name": "helpdesk",
    "description": (
        "Tangani pertanyaan pribadi pengguna tentang dirinya sendiri: status dan "
        "kelayakan kepesertaan BPJS/JKN, riwayat kunjungan ke faskes dan rumah sakit, "
        "diagnosis yang paling sering muncul, biaya klaim yang dibayar BPJS, data "
        "profil akun, serta panduan prosedur BPJS (iuran, ganti faskes, kartu hilang, "
        "dokumen pendaftaran). Data pribadi hanya untuk pengguna yang sedang login. "
        "Jangan gunakan untuk keluhan atau gejala kesehatan, dan tidak untuk "
        "statistik umum atau data orang lain."
    ),
    "system_prompt": helpdesk_prompt,
    "tools": bpjs_tools,
}

from module.bpjs_tools import bpjs_tools
from utils.helpdesk_prompt import helpdesk_prompt

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
    "tools": bpjs_tools,
}

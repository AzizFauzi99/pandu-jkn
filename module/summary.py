from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

SUMMARY_INSTRUCTION = """
Anda menyusun ringkasan klinis untuk dokter dari percakapan antara pasien dan
asisten kesehatan JKN. Gunakan hanya informasi yang benar-benar ada di
percakapan; isi "tidak disebutkan" atau kosongkan jika tidak ada. Jangan
menambahkan diagnosis. Tulis dalam bahasa Indonesia yang ringkas dan klinis.
"""


class DoctorSummary(BaseModel):
    keluhan_utama: str = Field(description="Keluhan utama pasien")
    onset: str = Field(description="Sejak kapan dan berapa lama keluhan berlangsung")
    tingkat_keparahan: str = Field(description="Tingkat keparahan atau suhu bila ada")
    gejala_penyerta: list[str] = Field(default_factory=list)
    usia: int | None = None
    jenis_kelamin: str | None = None
    riwayat_penyakit: list[str] = Field(default_factory=list)
    alergi: list[str] = Field(default_factory=list)
    obat_saat_ini: list[str] = Field(default_factory=list)
    level_triase: str = Field(
        description="emergency, segera, mandiri, atau belum_ditentukan"
    )
    saran_diberikan: list[str] = Field(default_factory=list)
    data_belum_lengkap: list[str] = Field(
        default_factory=list,
        description="Informasi penting yang belum diketahui dan perlu ditanyakan dokter",
    )


def _text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def build_transcript(messages) -> str:
    lines = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "Pasien"
        elif isinstance(message, AIMessage):
            role = "Asisten"
        else:
            continue
        text = _text(message.content).strip()
        if text:
            lines.append(f"{role}: {text}")
    return "\n".join(lines)


def generate_summary(llm, messages) -> DoctorSummary | None:
    transcript = build_transcript(messages)
    if not transcript:
        return None
    structured_llm = llm.with_structured_output(DoctorSummary)
    return structured_llm.invoke(
        [
            ("system", SUMMARY_INSTRUCTION),
            ("human", f"Percakapan:\n{transcript}"),
        ]
    )

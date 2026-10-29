import base64
import logging
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from module.image_store import get_image
from utils.llm import load_llm
from utils.nutrition_prompt import NUTRITION_IMAGE_PROMPT, nutrition_prompt

logger = logging.getLogger("uvicorn.error")

ACTIVITY_FACTORS = {
    "sedentari": 1.2,
    "ringan": 1.375,
    "sedang": 1.55,
    "berat": 1.725,
}


class UserHealthProfile(BaseModel):
    kondisi_kesehatan: list[str] = Field(
        default_factory=list,
        description="Contoh: diabetes, hipertensi, kolesterol, asam urat, maag",
    )
    alergi: list[str] = Field(default_factory=list)
    usia: int | None = None
    jenis_kelamin: Literal["laki-laki", "perempuan"] | None = None
    berat_badan_kg: float | None = None
    tinggi_badan_cm: float | None = None
    aktivitas: Literal["sedentari", "ringan", "sedang", "berat"] = "ringan"
    target: str | None = Field(
        default=None, description="Contoh: turun berat badan, jaga berat badan"
    )


class FoodComponent(BaseModel):
    nama: str = Field(description="Nama komponen makanan dalam bahasa Indonesia")
    porsi: str = Field(description="Perkiraan porsi, mis. '1 piring (150 g)'")
    kalori_kkal: float
    protein_g: float
    karbohidrat_g: float
    lemak_g: float
    gula_g: float
    serat_g: float
    natrium_mg: float
    keyakinan: float = Field(ge=0, le=1, description="Tingkat keyakinan 0-1")


class NutritionTotals(BaseModel):
    kalori_kkal: float = 0
    protein_g: float = 0
    karbohidrat_g: float = 0
    lemak_g: float = 0
    gula_g: float = 0
    serat_g: float = 0
    natrium_mg: float = 0


class FoodAssessment(BaseModel):
    """Keluaran model dari foto; total dihitung di kode, bukan oleh model."""

    makanan_terdeteksi: bool
    nama_hidangan: str = Field(description="Nama hidangan secara keseluruhan")
    komponen: list[FoodComponent] = Field(default_factory=list)
    penilaian: str = Field(description="Penilaian singkat kecocokan dengan profil pengguna")
    peringatan: list[str] = Field(
        default_factory=list,
        description="Konflik dengan alergi/kondisi kesehatan pengguna",
    )
    rekomendasi_pola_makan: list[str] = Field(
        default_factory=list,
        description="Saran konkret pola makan yang dipersonalisasi",
    )
    saran_pengganti: list[str] = Field(
        default_factory=list, description="Alternatif lebih sehat untuk komponen bermasalah"
    )
    catatan: str = Field(description="Keterbatasan analisis dan pengingat konsultasi")


class NutritionAnalysis(FoodAssessment):
    total: NutritionTotals
    kebutuhan_kalori_harian_kkal: float | None = None


def _sum_totals(components: list[FoodComponent]) -> NutritionTotals:
    fields = NutritionTotals.model_fields
    return NutritionTotals(
        **{f: round(sum(getattr(c, f) for c in components), 1) for f in fields}
    )


def estimate_daily_calories(
    usia: int,
    jenis_kelamin: str,
    berat_badan_kg: float,
    tinggi_badan_cm: float,
    aktivitas: str = "ringan",
) -> dict:
    """Mifflin-St Jeor: BMR dikali faktor aktivitas."""
    bmr = 10 * berat_badan_kg + 6.25 * tinggi_badan_cm - 5 * usia
    bmr += 5 if jenis_kelamin == "laki-laki" else -161
    tdee = bmr * ACTIVITY_FACTORS.get(aktivitas, ACTIVITY_FACTORS["ringan"])
    bmi = berat_badan_kg / (tinggi_badan_cm / 100) ** 2
    return {
        "bmr_kkal": round(bmr),
        "kebutuhan_kalori_harian_kkal": round(tdee),
        "bmi": round(bmi, 1),
    }


def _profile_text(profile: UserHealthProfile, kalori_harian: float | None) -> str:
    lines = [
        f"Kondisi kesehatan: {', '.join(profile.kondisi_kesehatan) or 'tidak disebutkan'}",
        f"Alergi: {', '.join(profile.alergi) or 'tidak disebutkan'}",
        f"Usia: {profile.usia or 'tidak disebutkan'}",
        f"Jenis kelamin: {profile.jenis_kelamin or 'tidak disebutkan'}",
        f"Berat badan (kg): {profile.berat_badan_kg or 'tidak disebutkan'}",
        f"Tinggi badan (cm): {profile.tinggi_badan_cm or 'tidak disebutkan'}",
        f"Target: {profile.target or 'tidak disebutkan'}",
    ]
    if kalori_harian:
        lines.append(f"Perkiraan kebutuhan kalori harian: {kalori_harian} kkal")
    return "\n".join(lines)


def analyze_food_image(
    llm,
    image_bytes: bytes,
    mime_type: str,
    profile: UserHealthProfile,
) -> NutritionAnalysis:
    kalori_harian = None
    if all([profile.usia, profile.jenis_kelamin, profile.berat_badan_kg, profile.tinggi_badan_cm]):
        kalori_harian = estimate_daily_calories(
            profile.usia,
            profile.jenis_kelamin,
            profile.berat_badan_kg,
            profile.tinggi_badan_cm,
            profile.aktivitas,
        )["kebutuhan_kalori_harian_kkal"]

    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
    structured_llm = llm.with_structured_output(FoodAssessment)
    assessment: FoodAssessment = structured_llm.invoke(
        [
            ("system", NUTRITION_IMAGE_PROMPT),
            (
                "human",
                [
                    {
                        "type": "text",
                        "text": "Profil pengguna:\n" + _profile_text(profile, kalori_harian),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            ),
        ]
    )
    return NutritionAnalysis(
        **assessment.model_dump(),
        total=_sum_totals(assessment.komponen),
        kebutuhan_kalori_harian_kkal=kalori_harian,
    )


@tool
def hitung_kebutuhan_kalori(
    usia: int,
    jenis_kelamin: str,
    berat_badan_kg: float,
    tinggi_badan_cm: float,
    aktivitas: str = "ringan",
) -> dict:
    """Perkirakan kebutuhan kalori harian dan BMI pengguna.

    Args:
        usia: Usia dalam tahun.
        jenis_kelamin: "laki-laki" atau "perempuan".
        berat_badan_kg: Berat badan dalam kg.
        tinggi_badan_cm: Tinggi badan dalam cm.
        aktivitas: "sedentari", "ringan", "sedang", atau "berat".
    """
    logger.info("tool hitung_kebutuhan_kalori")
    return estimate_daily_calories(
        usia, jenis_kelamin.strip().lower(), berat_badan_kg, tinggi_badan_cm,
        aktivitas.strip().lower(),
    )


@tool
def analisis_foto_makanan(
    foto_id: str,
    kondisi_kesehatan: list[str] | None = None,
    alergi: list[str] | None = None,
    usia: int | None = None,
    jenis_kelamin: str | None = None,
    berat_badan_kg: float | None = None,
    tinggi_badan_cm: float | None = None,
    aktivitas: str = "ringan",
    target: str | None = None,
) -> dict:
    """Analisis foto makanan pengguna: komponen makanan, gizi, dan rekomendasi.

    Args:
        foto_id: ID foto dari pesan pengguna, mis. "foto_1a2b3c4d".
        kondisi_kesehatan: Kondisi kesehatan pengguna (diabetes, hipertensi, dll).
        alergi: Alergi makanan pengguna.
        usia: Usia pengguna.
        jenis_kelamin: "laki-laki" atau "perempuan".
        berat_badan_kg: Berat badan dalam kg.
        tinggi_badan_cm: Tinggi badan dalam cm.
        aktivitas: "sedentari", "ringan", "sedang", atau "berat".
        target: Target pengguna, mis. turun berat badan.
    """
    logger.info("tool analisis_foto_makanan foto_id=%r", foto_id)
    stored = get_image(foto_id.strip())
    if stored is None:
        return {
            "error": (
                f"Foto '{foto_id}' tidak ditemukan. Minta pengguna mengirim ulang "
                "fotonya."
            )
        }
    image_bytes, mime_type = stored
    try:
        profile = UserHealthProfile(
            kondisi_kesehatan=kondisi_kesehatan or [],
            alergi=alergi or [],
            usia=usia,
            jenis_kelamin=jenis_kelamin.strip().lower() if jenis_kelamin else None,
            berat_badan_kg=berat_badan_kg,
            tinggi_badan_cm=tinggi_badan_cm,
            aktivitas=aktivitas.strip().lower(),
            target=target,
        )
        return analyze_food_image(load_llm, image_bytes, mime_type, profile).model_dump()
    except Exception:
        logger.exception("analisis_foto_makanan failed")
        return {"error": "Gagal menganalisis foto. Minta pengguna mencoba lagi."}


nutrition_subagent = {
    "name": "nutrition",
    "description": (
        "Tangani pertanyaan seputar gizi dan pola makan: kandungan nutrisi "
        "makanan, kalori, diet, menu sehat, dan rekomendasi makan sesuai kondisi "
        "kesehatan (diabetes, hipertensi, kolesterol, dll). Tangani juga pesan "
        "yang berisi FOTO makanan (ditandai '[Foto makanan terlampir: foto_id=...]'); "
        "sertakan foto_id tersebut apa adanya saat mendelegasikan. Juga tangani "
        "pesan lanjutan dalam topik yang sama."
    ),
    "system_prompt": nutrition_prompt,
    "tools": [analisis_foto_makanan, hitung_kebutuhan_kalori],
}

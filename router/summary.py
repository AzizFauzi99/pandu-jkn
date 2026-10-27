from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from module.summary import DoctorSummary, generate_summary
from router.chat import agents_instance

router = APIRouter(tags=["summary"])


class SummaryRequest(BaseModel):
    session_id: str


@router.post("/summary", response_model=DoctorSummary)
def post_summary(request: SummaryRequest):
    messages = agents_instance.get_messages(request.session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")

    try:
        summary = generate_summary(agents_instance.llm_instance, messages)
    except Exception:
        raise HTTPException(status_code=502, detail="Gagal membuat ringkasan")

    if summary is None:
        raise HTTPException(status_code=404, detail="Belum ada percakapan")
    return summary

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from module import session_store
from module.summary import DoctorSummary, generate_summary
from module.user_store import User
from router.auth import get_current_user
from router.chat import agents_instance

router = APIRouter(tags=["summary"])


class SummaryRequest(BaseModel):
    session_id: str


@router.post("/summary", response_model=DoctorSummary)
def post_summary(request: SummaryRequest, user: User = Depends(get_current_user)):
    if session_store.get_session(user.id, request.session_id) is None:
        raise HTTPException(status_code=404, detail="Session tidak ditemukan")

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

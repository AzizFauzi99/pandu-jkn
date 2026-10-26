import base64
import binascii
import json
import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from module.agent import Agents
from module.image_store import save_image

logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["chat"])
agents_instance = Agents()

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGES = 4
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class ChatImage(BaseModel):
    mime_type: str = Field(description="image/jpeg, image/png, atau image/webp")
    data: str = Field(description="Isi gambar dalam base64 (tanpa prefix data:)")


class ChatRequest(BaseModel):
    user_input: str
    session_id: str | None = None
    images: list[ChatImage] = Field(default_factory=list, max_length=MAX_IMAGES)


def _store_images(images: list[ChatImage]) -> list[str]:
    ids = []
    for image in images:
        if image.mime_type not in ALLOWED_MIME:
            raise HTTPException(status_code=415, detail="Format gambar harus jpeg, png, atau webp")
        try:
            raw = base64.b64decode(image.data, validate=True)
        except (binascii.Error, ValueError):
            raise HTTPException(status_code=422, detail="Data gambar bukan base64 yang valid")
        if not raw:
            raise HTTPException(status_code=400, detail="Gambar kosong")
        if len(raw) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Ukuran gambar maksimal 8 MB")
        ids.append(save_image(raw, image.mime_type))
    return ids


@router.post("/chat")
def post_chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    user_input = request.user_input
    for image_id in _store_images(request.images):
        user_input += f"\n[Foto makanan terlampir: foto_id={image_id}]"

    def event_stream():
        try:
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"

            for token in agents_instance.ai_agent(user_input, session_id):
                payload = json.dumps({"answer": token})
                yield f"data: {payload}\n\n"

            yield 'data: {"completed": true}\n\n'

        except Exception:
            logger.exception("chat streaming failed session_id=%s", session_id)
            yield 'data: {"error": "Streaming failed"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

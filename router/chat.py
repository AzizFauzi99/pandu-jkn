import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from module.agent import Agents

router = APIRouter(tags=["chat"])
agents_instance = Agents()


class ChatRequest(BaseModel):
    user_input: str
    session_id: str | None = None


@router.post("/chat")
def post_chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())

    def event_stream():
        try:
            yield f"data: {json.dumps({'session_id': session_id})}\n\n"

            for token in agents_instance.ai_agent(request.user_input, session_id):
                payload = json.dumps({"answer": token})
                yield f"data: {payload}\n\n"

            yield 'data: {"completed": true}\n\n'

        except Exception:
            yield 'data: {"error": "Streaming failed"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

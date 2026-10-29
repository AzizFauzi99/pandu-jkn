from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from module import session_store
from module.session_store import Session
from module.summary import _text
from module.user_store import User
from router.auth import get_current_user
from router.chat import agents_instance

router = APIRouter(prefix="/sessions", tags=["session"])


class CreateSessionRequest(BaseModel):
    title: str | None = Field(default=None, max_length=100)


class UpdateSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class StarRequest(BaseModel):
    starred: bool


class SessionResponse(BaseModel):
    id: str
    title: str
    starred: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    role: str
    content: str


def _to_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        title=session.title,
        starred=session.starred,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Session tidak ditemukan"
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def post_session(
    request: CreateSessionRequest, user: User = Depends(get_current_user)
):
    return _to_response(session_store.create_session(user.id, request.title))


@router.get("", response_model=list[SessionResponse])
def get_sessions(starred: bool | None = None, user: User = Depends(get_current_user)):
    return [_to_response(s) for s in session_store.list_sessions(user.id, starred)]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, user: User = Depends(get_current_user)):
    session = session_store.get_session(user.id, session_id)
    if session is None:
        raise _not_found()
    return _to_response(session)


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_session_messages(session_id: str, user: User = Depends(get_current_user)):
    if session_store.get_session(user.id, session_id) is None:
        raise _not_found()

    history = []
    for message in agents_instance.get_messages(session_id):
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            continue
        content = _text(message.content).strip()
        if content:
            history.append(MessageResponse(role=role, content=content))
    return history


@router.patch("/{session_id}", response_model=SessionResponse)
def patch_session(
    session_id: str,
    request: UpdateSessionRequest,
    user: User = Depends(get_current_user),
):
    session = session_store.update_title(user.id, session_id, request.title)
    if session is None:
        raise _not_found()
    return _to_response(session)


@router.put("/{session_id}/star", response_model=SessionResponse)
def put_session_star(
    session_id: str, request: StarRequest, user: User = Depends(get_current_user)
):
    session = session_store.set_starred(user.id, session_id, request.starred)
    if session is None:
        raise _not_found()
    return _to_response(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, user: User = Depends(get_current_user)):
    if not session_store.delete_session(user.id, session_id):
        raise _not_found()
    agents_instance.delete_messages(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

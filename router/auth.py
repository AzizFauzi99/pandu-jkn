from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from module.token_blacklist import is_revoked, revoke
from module.user_store import User, get_user_by_email, get_user_by_id, seed_dev_user
from utils.security import (
    JWT_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)

# Dipakai agar waktu respons sama baik email terdaftar maupun tidak.
_DUMMY_HASH = hash_password("dummy-password")

seed_dev_user()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
def post_login(request: LoginRequest):
    user = get_user_by_email(request.email)
    password_ok = verify_password(
        request.password, user.password_hash if user else _DUMMY_HASH
    )
    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=JWT_EXPIRE_MINUTES * 60,
    )


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    payload = decode_access_token(credentials.credentials)
    if payload is None or is_revoked(payload["jti"]):
        raise unauthorized
    return payload


def get_current_user(payload: dict = Depends(get_token_payload)) -> User:
    user = get_user_by_id(payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/logout")
def post_logout(
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
):
    revoke(payload["jti"], payload["exp"])
    return {"message": "Logout berhasil"}

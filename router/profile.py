from fastapi import APIRouter, Depends, HTTPException

from module.profile_store import (
    NikNotFound,
    ProfileConflict,
    ProfileData,
    ProfileIncomplete,
    get_profile,
    save_profile,
)
from module.user_store import User
from router.auth import get_current_user

router = APIRouter(tags=["profile"])


class ProfileResponse(ProfileData):
    email: str


@router.get("/profile", response_model=ProfileResponse)
def get_user_profile(user: User = Depends(get_current_user)):
    return ProfileResponse(email=user.email, **get_profile(user.email).model_dump())


@router.put("/profile", response_model=ProfileResponse)
def put_user_profile(profile: ProfileData, user: User = Depends(get_current_user)):
    # Email mengikuti akun login sehingga hanya-baca; PUT mengganti seluruh profil.
    try:
        saved = save_profile(user.email, user.password_hash, profile)
    except (ProfileIncomplete, NikNotFound) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ProfileConflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ProfileResponse(email=user.email, **saved.model_dump())

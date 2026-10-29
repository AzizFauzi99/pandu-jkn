from fastapi import APIRouter, Depends

from module.profile_store import ProfileData, get_profile, save_profile
from module.user_store import User
from router.auth import get_current_user

router = APIRouter(tags=["profile"])


class ProfileResponse(ProfileData):
    email: str


@router.get("/profile", response_model=ProfileResponse)
def get_user_profile(user: User = Depends(get_current_user)):
    return ProfileResponse(email=user.email, **get_profile(user.id).model_dump())


@router.put("/profile", response_model=ProfileResponse)
def put_user_profile(profile: ProfileData, user: User = Depends(get_current_user)):
    # Email mengikuti akun login sehingga hanya-baca; PUT mengganti seluruh profil.
    saved = save_profile(user.id, profile)
    return ProfileResponse(email=user.email, **saved.model_dump())

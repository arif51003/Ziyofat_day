import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, Form, File

from app.database import db_dep
from app.models import Media
from app.schemas import UserProfileResponse
from app.dependencies import current_user

router = APIRouter(prefix="/user", tags=["User"])

ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


def _safe_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower() if ext else ""


UPLOAD_DIR = "media_uploads"


def _to_profile_response(user) -> UserProfileResponse:
    return UserProfileResponse(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar.url if user.avatar else None,
    )


@router.get("/profile/", response_model=UserProfileResponse)
async def me(current_user: current_user):
    return _to_profile_response(current_user)


@router.patch("/profile/update", response_model=UserProfileResponse)
async def update_me(
    session:db_dep,
    current_user: current_user,
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    avatar: UploadFile | None = File(None),
):


    if first_name is not None:
        current_user.first_name = first_name
    if last_name is not None:
        current_user.last_name = last_name

    if avatar:
        ext = _safe_ext(avatar.filename)
        if ext not in ALLOWED_AVATAR_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Ruxsat etilmagan fayl turi")

        content = await avatar.read()
        if len(content) > MAX_AVATAR_SIZE:
            raise HTTPException(status_code=400, detail="Fayl hajmi 5MB dan katta")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as f:
            f.write(content)

        media = Media(url=f"/static/{filename}")
        session.add(media)
        session.flush([media])

        current_user.avatar_id = media.id

    session.commit()
    session.refresh(current_user)

    return _to_profile_response(current_user)

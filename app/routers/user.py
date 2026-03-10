import os
import uuid
from fastapi import APIRouter, Request, UploadFile, Form, File

from app.database import db_dep
from app.models import Media
from app.schemas import UserProfileResponse
from app.dependencies import current_user

router = APIRouter(prefix="/user", tags=["User"])


def _safe_ext(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower() if ext else ""


UPLOAD_DIR = "media_uploads"


@router.get("/profile/", response_model=UserProfileResponse)
async def me(current_user: current_user):
    return current_user


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
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4().hex}{_safe_ext(avatar.filename)}"
        path = os.path.join(UPLOAD_DIR, filename)

        with open(path, "wb") as f:
            f.write(await avatar.read())

        media = Media(url=f"/static/{filename}")
        session.add(media)
        session.flush([media])

        current_user.avatar_id = media.id

    session.commit()
    session.refresh(current_user)

    return current_user

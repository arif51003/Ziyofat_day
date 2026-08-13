from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.database import db_dep
from app.dependencies import admin_user
from app.schemas import RefreshTokenRequest
from app.models import User, TokenBlacklist
from app.utils import verify_password, generate_jwt_tokens, decode_jwt_token, hash_password


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login/")
async def login(
    db: db_dep, username: str | None = Form(None), password: str | None = Form(None)
):
    # email, password ask
    # user topilsa, yangi access va refresh tokenlar generatsiya qilamiz
    stmt = select(User).where(User.username == username)
    user = db.execute(stmt).scalars().first()
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Foydalanuvchi faol emas")

    access_token, refresh_token = generate_jwt_tokens(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_admin": user.is_admin
        }
    }


@router.post("/refresh/")
async def refresh(db: db_dep, data: RefreshTokenRequest):
    decoded_data = decode_jwt_token(data.refresh_token)

    exp_time = datetime.fromtimestamp(decoded_data["exp"], tz=timezone.utc)
    if exp_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401, detail="Refresh token expired. Please log in."
        )

    user_id = decoded_data["sub"]
    access_token = generate_jwt_tokens(user_id, is_access_only=True)

    return {
        "access_token": access_token,
    }


jwt_security = HTTPBearer(auto_error=False)


@router.post("/logout", status_code=200)
async def logout(
    session: db_dep,
    credentials: HTTPAuthorizationCredentials = Depends(jwt_security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid token")

    token = credentials.credentials  # toza token

    session.add(TokenBlacklist(token=token))
    session.commit()

    return {"detail": "Logout successfully"}

VALID_ROLES = {"waiter", "kitchen", "cashier"}


@router.post("/user-create", status_code=201)
async def create_user(
    db: db_dep,
    admin: admin_user,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    is_admin: bool = Form(False),
):
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Noto'g'ri role. Ruxsat etilgan: {', '.join(sorted(VALID_ROLES))}",
        )

    stmt = select(User).where(User.username == username)
    existing_user = db.execute(stmt).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(password)

    new_user = User(
        username=username,
        password_hash=hashed_password,
        role=role,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "is_admin": new_user.is_admin
    }
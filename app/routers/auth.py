from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Form, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import db_dep
from app.dependencies import admin_user
from app.schemas import RefreshTokenRequest
from app.models import Restaurant, User, TokenBlacklist
from app.utils import (
    verify_password,
    generate_jwt_tokens,
    decode_jwt_token,
    hash_password,
    has_active_subscription,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin,
        "is_platform_owner": user.is_platform_owner,
        "restaurant": (
            {"id": user.restaurant.id, "name": user.restaurant.name, "code": user.restaurant.code}
            if user.restaurant
            else None
        ),
    }


@router.post("/login/")
async def login(
    response: Response,
    db: db_dep,
    username: str | None = Form(None),
    password: str | None = Form(None),
    restaurant_code: str | None = Form(None),
):
    # restaurant_code bo'sh bo'lsa - platforma egasi (restaurant_id NULL) sifatida qidiramiz,
    # bo'lsa - o'sha restoran ichidan username qidiramiz (username restoran ichida unique)
    stmt = select(User).options(joinedload(User.restaurant))

    if restaurant_code:
        restaurant = db.scalar(select(Restaurant).where(Restaurant.code == restaurant_code))
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restoran topilmadi")
        stmt = stmt.where(User.username == username, User.restaurant_id == restaurant.id)
    else:
        stmt = stmt.where(User.username == username, User.restaurant_id.is_(None))

    user = db.execute(stmt).scalars().first()
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Foydalanuvchi faol emas")
    if not has_active_subscription(user.restaurant):
        raise HTTPException(status_code=403, detail="Restoran obunasi faol emas")

    access_token, refresh_token = generate_jwt_tokens(user.id)

    if user.is_admin or user.is_platform_owner:
        # Also authenticate the Starlette-Admin session so an admin who logs
        # in through the SPA can open /admin without logging in a second time.
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=True,
            samesite="lax",
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_out(user),
    }


@router.post("/register-restaurant", status_code=201)
async def register_restaurant(
    db: db_dep,
    restaurant_name: str = Form(...),
    restaurant_code: str = Form(...),
    phone: str | None = Form(None),
    username: str = Form(...),
    password: str = Form(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
):
    """Ochiq (auth talab qilinmaydigan) ro'yxatdan o'tish: yangi restoran + uning
    birinchi admin hisobini bir vaqtda yaratadi, trial holatida boshlaydi."""
    restaurant_code = restaurant_code.strip().lower()

    if not restaurant_code or not restaurant_code.replace("-", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Restoran kodi faqat harf, raqam va '-' belgisidan iborat bo'lishi kerak",
        )

    existing = db.scalar(select(Restaurant).where(Restaurant.code == restaurant_code))
    if existing:
        raise HTTPException(status_code=400, detail="Bu restoran kodi band")

    restaurant = Restaurant(
        name=restaurant_name,
        code=restaurant_code,
        phone=phone,
        subscription_status="trial",
        trial_ends_at=datetime.now() + timedelta(days=14),
        is_active=True,
    )
    db.add(restaurant)
    db.flush()  # restaurant.id kerak

    admin_user_obj = User(
        restaurant_id=restaurant.id,
        username=username,
        password_hash=hash_password(password),
        role="admin",
        first_name=first_name,
        last_name=last_name,
        is_admin=True,
    )
    db.add(admin_user_obj)
    db.commit()
    db.refresh(admin_user_obj)
    admin_user_obj.restaurant = restaurant

    access_token, refresh_token = generate_jwt_tokens(admin_user_obj.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": _user_out(admin_user_obj),
    }


@router.post("/refresh/")
async def refresh(db: db_dep, data: RefreshTokenRequest):
    decoded_data = decode_jwt_token(data.refresh_token, expected_type="refresh")

    exp_time = datetime.fromtimestamp(decoded_data["exp"], tz=timezone.utc)
    if exp_time < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=401, detail="Refresh token expired. Please log in."
        )

    user_id = decoded_data["sub"]

    user = db.scalar(
        select(User).where(User.id == user_id).options(joinedload(User.restaurant))
    )
    if not user or user.is_deleted or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found yoki faol emas")
    if not has_active_subscription(user.restaurant):
        raise HTTPException(status_code=403, detail="Restoran obunasi faol emas")

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

    stmt = select(User).where(
        User.username == username, User.restaurant_id == admin.restaurant_id
    )
    existing_user = db.execute(stmt).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = hash_password(password)

    new_user = User(
        restaurant_id=admin.restaurant_id,
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

from datetime import datetime, timezone
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.database import db_dep
from app.models import User, TokenBlacklist
from app.utils import decode_jwt_token, has_active_subscription


jwt_security = HTTPBearer(auto_error=False)


def get_current_user_jwt(
    session: db_dep, credentials: HTTPAuthorizationCredentials = Depends(jwt_security)
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = credentials.credentials
    stmt = select(TokenBlacklist).where(TokenBlacklist.token == token)
    if session.execute(stmt).scalar():
        raise HTTPException(status_code=401, detail="Token in blacklist")

    decoded = decode_jwt_token(credentials.credentials, expected_type="access")
    user_id = decoded["sub"]
    exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)

    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token expired.")

    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.avatar), joinedload(User.restaurant))
    )
    user = session.execute(stmt).scalars().first()

    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Foydalanuvchi faol emas")

    if not has_active_subscription(user.restaurant):
        raise HTTPException(status_code=403, detail="Restoran obunasi faol emas")

    return user


# Role-based dependencies
def require_waiter(user: Annotated[User, Depends(get_current_user_jwt)]) -> User:
    """Ensure user has waiter role"""
    if user.role != "waiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat waiter uchun",
        )
    return user


def require_kitchen(user: Annotated[User, Depends(get_current_user_jwt)]) -> User:
    """Ensure user has kitchen role"""
    if user.role != "kitchen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat kitchen uchun",
        )
    return user


def require_cashier(user: Annotated[User, Depends(get_current_user_jwt)]) -> User:
    """Ensure user has cashier role"""
    if user.role != "cashier":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat cashier uchun",
        )
    return user


def require_admin(user: Annotated[User, Depends(get_current_user_jwt)]) -> User:
    """Ensure user is an admin of their own restaurant"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat admin uchun",
        )
    return user


def require_platform_owner(user: Annotated[User, Depends(get_current_user_jwt)]) -> User:
    """Ensure user is the platform owner (manages restaurants/subscriptions, not tied to any one restaurant)"""
    if not user.is_platform_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat platforma egasi uchun",
        )
    return user


# For brevity in routers
current_user = Annotated[User, Depends(get_current_user_jwt)]
waiter_user = Annotated[User, Depends(require_waiter)]
kitchen_user = Annotated[User, Depends(require_kitchen)]
cashier_user = Annotated[User, Depends(require_cashier)]
admin_user = Annotated[User, Depends(require_admin)]
platform_owner_user = Annotated[User, Depends(require_platform_owner)]


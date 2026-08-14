from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, Response
from jose import jwt
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.database import get_db
from app.models import Restaurant, User
from app.utils import (
    verify_password,
    generate_jwt_tokens,
    decode_jwt_token,
    has_active_subscription,
)
from app.config import settings


class JSONAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ):
        # The stock login template only has one "Username" field, so a
        # restaurant admin types "restoran-kodi/username"; a bare username
        # (no "/") is treated as a platform-owner login (restaurant_id NULL).
        db = next(get_db())
        try:
            if "/" in username:
                code, uname = username.split("/", 1)
                restaurant = (
                    db.query(Restaurant).filter(Restaurant.code == code.strip().lower()).first()
                )
                if not restaurant:
                    raise LoginFailed("Restoran topilmadi.")
                user = (
                    db.query(User)
                    .filter(User.username == uname, User.restaurant_id == restaurant.id)
                    .first()
                )
            else:
                user = (
                    db.query(User)
                    .filter(User.username == username, User.restaurant_id.is_(None))
                    .first()
                )

            if not user or user.is_deleted:
                raise LoginFailed("User not found.")

            if not (user.is_admin or user.is_platform_owner):
                raise LoginFailed("User is not admin.")

            if not user.is_active:
                raise LoginFailed("User is not active.")

            if not verify_password(password, user.password_hash):
                raise LoginFailed("Invalid password.")

            if not has_active_subscription(user.restaurant):
                raise LoginFailed("Restoran obunasi faol emas.")
        finally:
            db.close()

        # The admin cookie always carries an access-type token (is_authenticated
        # only accepts type="access"); remember_me just extends its lifetime to
        # match the refresh-token window instead of swapping in a refresh token.
        expire_delta = (
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            if remember_me
            else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        token = generate_jwt_tokens(
            user.id,
            is_access_only=True,
            access_expires_delta=timedelta(seconds=expire_delta) if remember_me else None,
        )

        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=expire_delta,
            secure=True,
            samesite="lax",
        )
        db.close()

        return response

    async def is_authenticated(self, request: Request) -> User | None:
        token = request.cookies.get("access_token")

        if not token:
            return None

        try:
            payload = decode_jwt_token(token, expected_type="access")
        except (jwt.JWTError, HTTPException):
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        if payload.get("exp") < datetime.now(UTC).timestamp():
            return None

        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if user is None or user.is_deleted or not user.is_active:
                return None

            if not (user.is_admin or user.is_platform_owner):
                return None

            if not has_active_subscription(user.restaurant):
                return None

            # Tenant-scoped ModelViews read this to filter rows to the
            # logged-in admin's own restaurant (see app/admin/views.py).
            request.state.user = user

            return user
        finally:
            db.close()

    async def logout(self, request: Request, response: Response) -> Response:
        response.delete_cookie("access_token")
        return response
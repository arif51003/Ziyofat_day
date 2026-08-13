from datetime import UTC, datetime

from fastapi import HTTPException, Request, Response
from jose import jwt
from starlette_admin.auth import AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.database import get_db
from app.models import User
from app.utils import (
    verify_password,
    generate_jwt_tokens,
    decode_jwt_token,
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
        db = next(get_db())
        try:
            user = db.query(User).filter(User.username == username).first()

            if not user or user.is_deleted:
                raise LoginFailed("User not found.")

            if not user.is_admin:
                raise LoginFailed("User is not admin.")

            if not user.is_active:
                raise LoginFailed("User is not active.")

            if not verify_password(password, user.password_hash):
                raise LoginFailed("Invalid password.")
        finally:
            db.close()

        access_token, refresh_token = generate_jwt_tokens(user.id)

        token = refresh_token if remember_me else access_token
        expire_delta = (
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            if remember_me
            else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
            payload = decode_jwt_token(token)
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

            if user is None or user.is_deleted or not user.is_admin or not user.is_active:
                return None

            return user
        finally:
            db.close()

    async def logout(self, request: Request, response: Response) -> Response:
        response.delete_cookie("access_token")
        return response
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def generate_slug(title):
    return title.lower().replace(" ", "-")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def generate_jwt_tokens(
    user_id: int, is_access_only: bool = False, access_expires_delta: timedelta | None = None
):
    access_token = jwt.encode(
        algorithm=settings.ALGORITHM,
        key=settings.SECRET_KEY,
        claims={
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(timezone.utc)
            + (access_expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        },
    )

    if is_access_only:
        return access_token

    refresh_token = jwt.encode(
        algorithm=settings.ALGORITHM,
        key=settings.SECRET_KEY,
        claims={
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        },
    )

    return access_token, refresh_token


def decode_jwt_token(token: str, expected_type: str | None = None):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    if expected_type is not None and payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")

    return payload

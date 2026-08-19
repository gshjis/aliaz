"""Безопасность: хэширование паролей и работа с JWT-токенами."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from config import settings


def hash_password(password: str) -> str:
    """Хэшировать пароль с помощью bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Проверить пароль против bcrypt-хэша."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int) -> str:
    """Создать JWT-токен доступа для пользователя."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "type": "access",
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Декодировать JWT-токен доступа и вернуть user_id.

    Raises:
        jwt.PyJWTError: если токен невалиден, просрочен или не является access-токеном.
    """
    payload = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != "access":
        raise jwt.PyJWTError("Not an access token")
    sub = payload.get("sub")
    if sub is None:
        raise jwt.PyJWTError("Token sub is missing")
    return int(str(sub))


def create_refresh_token(user_id: int) -> str:
    """Создать refresh-токен (долгоживущий) для обновления access-токена."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_refresh_expire_minutes),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_refresh_token(token: str) -> int:
    """Декодировать refresh-токен и вернуть user_id.

    Raises:
        jwt.PyJWTError: если токен невалиден, просрочен или не является refresh-токеном.
    """
    payload = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    if payload.get("type") != "refresh":
        raise jwt.PyJWTError("Not a refresh token")
    sub = payload.get("sub")
    if sub is None:
        raise jwt.PyJWTError("Token sub is missing")
    return int(str(sub))

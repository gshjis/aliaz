"""Безопасность: хэширование паролей и работа с JWT-токенами."""

from datetime import datetime, timedelta, timezone

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
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)  # type: ignore[reportUnknownMemberType]


def decode_access_token(token: str) -> int:
    """Декодировать JWT-токен и вернуть user_id.

    Raises:
        jwt.PyJWTError: если токен невалиден или просрочен.
    """
    payload = jwt.decode(  # type: ignore[reportUnknownMemberType]
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    sub = payload.get("sub")  # type: ignore[reportUnknownMemberType]
    if sub is None:
        raise jwt.PyJWTError("Token sub is missing")
    return int(str(sub))

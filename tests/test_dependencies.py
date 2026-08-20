"""Тесты зависимостей аутентификации (auth.dependencies)."""

import pytest
from auth.dependencies import get_current_user
from auth.security import create_access_token
from database.models import User
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_current_user_no_credentials(db_session: AsyncSession) -> None:
    """Если нет токена, поднимается 401."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None, db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session: AsyncSession) -> None:
    """Если токен невалиден, поднимается 401."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=type("obj", (), {"credentials": "invalid.token.here"})(),
            db=db_session,
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_expired_token(db_session: AsyncSession) -> None:
    """Если токен просрочен, поднимается 401."""
    # Создаем пользователя
    user = User(
        nickname="testuser",
        email="test@example.com",
        password_hash="hashedpassword",
    )
    db_session.add(user)
    await db_session.commit()

    # Создаем просроченный токен (с прошлой датой истечения)
    from datetime import datetime, timedelta, UTC

    payload = {
        "sub": str(user.id),
        "iat": datetime.now(UTC) - timedelta(hours=1),
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "type": "access",
        "jti": "test-jti",
    }
    import jwt
    from config import settings

    expired_token = jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=type("obj", (), {"credentials": expired_token})(),
            db=db_session,
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid or expired token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(db_session: AsyncSession) -> None:
    """Если пользователь не найден по токену, поднимается 401."""
    token = create_access_token(999999)  # Не существующий user_id

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            credentials=type("obj", (), {"credentials": token})(),
            db=db_session,
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_current_user_success(db_session: AsyncSession) -> None:
    """Если токен валиден и пользователь найден, возвращается User."""
    # Создаем пользователя
    user = User(
        nickname="testuser",
        email="test@example.com",
        password_hash="hashedpassword",
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user.id)

    result = await get_current_user(
        credentials=type("obj", (), {"credentials": token})(),
        db=db_session,
    )

    assert result.id == user.id
    assert result.nickname == user.nickname

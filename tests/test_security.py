"""Тесты безопасности: хэширование паролей и JWT (пакет auth.security)."""

import jwt
import pytest
from auth.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from config import settings


def test_hash_password_changes_value() -> None:
    """Хэш не должен совпадать с исходным паролем."""
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_verify_password_success() -> None:
    """Валидный пароль подтверждается."""
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_failure() -> None:
    """Невалидный пароль не подтверждается."""
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_create_decode_token_roundtrip() -> None:
    """Токен должен декодироваться обратно в тот же user_id."""
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_decode_invalid_token_raises() -> None:
    """Невалидный токен должен вызывать PyJWTError."""
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not.a.valid.token")


def test_decode_token_missing_sub_raises() -> None:
    """Токен без поля sub должен вызывать ошибку."""
    token = jwt.encode(
        {"iat": 1}, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)


def test_token_contains_expiry() -> None:
    """В токене должно быть поле exp в будущем."""
    import time

    token = create_access_token(1)
    decoded = jwt.decode(
        token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    assert decoded["exp"] > time.time()


def test_refresh_token_roundtrip() -> None:
    """Refresh-токен декодируется в тот же user_id."""
    token = create_refresh_token(7)
    assert decode_refresh_token(token) == 7


def test_refresh_token_has_longer_lifetime() -> None:
    """Refresh-токен живёт дольше access-токена."""

    access = create_access_token(1)
    refresh = create_refresh_token(1)
    access_exp = jwt.decode(
        access, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )["exp"]
    refresh_exp = jwt.decode(
        refresh, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )["exp"]
    assert refresh_exp > access_exp


def test_access_token_rejected_as_refresh() -> None:
    """Access-токен нельзя использовать как refresh-токен."""
    access = create_access_token(1)
    with pytest.raises(jwt.PyJWTError):
        decode_refresh_token(access)


def test_refresh_token_rejected_as_access() -> None:
    """Refresh-токен нельзя использовать как access-токен."""
    refresh = create_refresh_token(1)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(refresh)

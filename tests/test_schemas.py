"""Тесты pydantic-схем (пакет schemas)."""

import pytest
from pydantic import ValidationError
from schemas.auth import LoginRequest, RegisterRequest, RefreshRequest, TokenResponse, UserResponse
from schemas.words import WordCreateRequest, WordResponse


def test_register_request_valid() -> None:
    """Валидные данные регистрации проходят."""
    r = RegisterRequest(
        nickname="alice", email="alice@example.com", password="password123"
    )
    assert r.nickname == "alice"
    assert r.telegram_nickname is None


def test_register_request_short_nickname() -> None:
    """Слишком короткий nickname отклоняется."""
    with pytest.raises(ValidationError):
        RegisterRequest(
            nickname="ab", email="alice@example.com", password="password123"
        )


def test_register_request_invalid_email() -> None:
    """Невалидный email отклоняется."""
    with pytest.raises(ValidationError):
        RegisterRequest(nickname="alice", email="not-an-email", password="password123")


def test_register_request_short_password() -> None:
    """Слишком короткий пароль отклоняется."""
    with pytest.raises(ValidationError):
        RegisterRequest(nickname="alice", email="alice@example.com", password="short")


def test_login_request_valid() -> None:
    """Валидные данные входа проходят."""
    login = LoginRequest(email="alice@example.com", password="password123")
    assert login.email == "alice@example.com"


def test_user_response_from_attributes() -> None:
    """UserResponse строится из ORM-объекта (from_attributes)."""

    class FakeUser:
        id = 1
        nickname = "nick"
        email = "e@m.com"
        telegram_nickname = None

    u = UserResponse.model_validate(FakeUser())
    assert u.id == 1
    assert u.nickname == "nick"
    assert u.email == "e@m.com"
    assert u.telegram_nickname is None


def test_token_response_default_type() -> None:
    """TokenResponse имеет тип токена 'bearer' по умолчанию."""
    t = TokenResponse(access_token="xyz", refresh_token="abc")
    assert t.access_token == "xyz"
    assert t.refresh_token == "abc"
    assert t.token_type == "bearer"


def test_word_create_request_valid() -> None:
    """Валидное слово проходит."""
    w = WordCreateRequest(word_en="hello")
    assert w.word_en == "hello"


def test_word_create_request_empty() -> None:
    """Пустое слово отклоняется."""
    with pytest.raises(ValidationError):
        WordCreateRequest(word_en="")


def test_word_response_from_attributes() -> None:
    """WordResponse строится из ORM-объекта."""

    class FakeWord:
        id = 1
        word_en = "hello"
        translation = "привет"
        transcription = "[həˈləʊ]"
        corrected_word = "hello"
        created_at = "2020-01-01T00:00:00"

    w = WordResponse.model_validate(FakeWord())
    assert w.translation == "привет"
    assert w.word_en == "hello"
    assert w.transcription == "[həˈləʊ]"
    assert w.corrected_word == "hello"


def test_refresh_request_valid() -> None:
    """RefreshRequest с валидным токеном проходит."""
    r = RefreshRequest(refresh_token="valid.token.here")
    assert r.refresh_token == "valid.token.here"


def test_refresh_request_empty_token() -> None:
    """RefreshRequest с пустым токеном отклоняется."""
    with pytest.raises(ValidationError):
        RefreshRequest(refresh_token="")


def test_register_request_max_length_nickname() -> None:
    """Слишком длинный nickname отклоняется."""
    with pytest.raises(ValidationError):
        RegisterRequest(
            nickname="a" * 256,
            email="alice@example.com",
            password="password123",
        )


def test_register_request_max_length_password() -> None:
    """Слишком длинный пароль отклоняется."""
    with pytest.raises(ValidationError):
        RegisterRequest(
            nickname="alice",
            email="alice@example.com",
            password="a" * 129,
        )


def test_login_request_invalid_email() -> None:
    """LoginRequest с невалидным email отклоняется."""
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="password123")

"""Pydantic-схемы для аутентификации и пользователей."""

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Данные для регистрации нового пользователя."""

    nickname: str = Field(min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telegram_nickname: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Проверить сложность пароля: буква, цифра и спецсимвол."""
        if not re.search(r"[A-Za-zА-Яа-я]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-zА-Яа-я0-9]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    """Данные для входа в систему."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Данные для обновления access-токена."""

    refresh_token: str = Field(min_length=1)


class UserResponse(BaseModel):
    """Публичные данные пользователя."""

    id: int
    nickname: str
    email: str
    telegram_nickname: str | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Ответ с JWT-токенами доступа и обновления."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

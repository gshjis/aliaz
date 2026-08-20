"""Pydantic-схемы для аутентификации и пользователей."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Данные для регистрации нового пользователя."""

    nickname: str = Field(min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telegram_nickname: str | None = None


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

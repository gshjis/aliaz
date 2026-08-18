"""Pydantic-схемы приложения."""

from .auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .words import WordCreateRequest, WordResponse

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "WordCreateRequest",
    "WordResponse",
]

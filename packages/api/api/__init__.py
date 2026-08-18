"""Роутеры API приложения."""

from .auth import router as auth_router
from .main import app
from .words import router as words_router

__all__ = ["auth_router", "words_router", "app"]

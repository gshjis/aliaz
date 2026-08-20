"""Базовые типы сервиса перевода."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationResult:
    """Результат перевода.

    Содержит перевод, транскрипцию и исправленное (нормализованное) слово.
    """

    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    transcription: str = ""
    corrected_word: str = ""


class Translator(ABC):
    """Абстракция сервиса перевода.

    Реализации подключают внешние сервисы-переводчики. Бизнес-логика
    зависит только от этого интерфейса.
    """

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "ru",
    ) -> TranslationResult:
        """Перевести текст с source_lang на target_lang."""
        raise NotImplementedError

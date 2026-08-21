"""Пакет сервиса перевода слов."""

from config.settings import settings
from translator.base import TranslationResult, Translator
from translator.openai import OpenAITranslator
from translator.stub import StubTranslator

__all__ = [
    "StubTranslator",
    "TranslationResult",
    "Translator",
    "get_translator",
    "OpenAITranslator",
]


_translator: Translator | None = None


def get_translator() -> Translator:
    """Вернуть активный сервис перевода.

    Если задан ключ OpenAI — возвращается OpenAITranslator, иначе —
    StubTranslator. Инстанс кэшируется на уровне модуля.
    """
    global _translator
    if _translator is not None:
        return _translator

    if settings.openai_api_key:
        _translator = OpenAITranslator(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )
    else:
        _translator = StubTranslator()
    return _translator

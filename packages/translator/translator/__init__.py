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


def get_translator() -> Translator:
    """Вернуть активный сервис перевода.

    На текущем этапе возвращается заглушка. В дальнейшем здесь можно
    подключать реального провайдера (DeepL, Google Translate и т.д.)
    на основе конфигурации.
    """
    if settings.openai_api_key:
        return OpenAITranslator(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )
    return StubTranslator()

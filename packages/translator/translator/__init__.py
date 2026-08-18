"""Пакет сервиса перевода слов."""

from translator.base import TranslationResult, Translator
from translator.stub import StubTranslator

__all__ = ["StubTranslator", "TranslationResult", "Translator", "get_translator"]


def get_translator() -> Translator:
    """Вернуть активный сервис перевода.

    На текущем этапе возвращается заглушка. В дальнейшем здесь можно
    подключать реального провайдера (DeepL, Google Translate и т.д.)
    на основе конфигурации.
    """
    return StubTranslator()

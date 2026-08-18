"""Тесты сервиса перевода (пакет translator)."""

import pytest
from translator import StubTranslator, TranslationResult, get_translator
from translator.base import Translator


@pytest.mark.asyncio
async def test_stub_translator_default_langs() -> None:
    """Заглушка переводит с en на ru по умолчанию."""
    translator = StubTranslator()
    result = await translator.translate("hello")
    assert isinstance(result, TranslationResult)
    assert result.source_text == "hello"
    assert result.translated_text == "[заглушка] hello"
    assert result.source_lang == "en"
    assert result.target_lang == "ru"


@pytest.mark.asyncio
async def test_stub_translator_custom_langs() -> None:
    """Заглушка учитывает переданные языки."""
    translator = StubTranslator()
    result = await translator.translate("hi", source_lang="fr", target_lang="de")
    assert result.source_lang == "fr"
    assert result.target_lang == "de"
    assert result.translated_text == "[заглушка] hi"


def test_get_translator_returns_stub() -> None:
    """Фабрика должна возвращать экземпляр StubTranslator."""
    assert isinstance(get_translator(), StubTranslator)


def test_translator_is_abstract() -> None:
    """Translator — абстрактный класс и не должен инстанцироваться."""
    assert issubclass(StubTranslator, Translator)
    with pytest.raises(TypeError):
        Translator()  # type: ignore[abstract]

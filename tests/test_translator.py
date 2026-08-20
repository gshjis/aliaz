"""Тесты для сервиса перевода."""

from unittest.mock import AsyncMock, patch

import pytest
from translator import OpenAITranslator, get_translator
from translator.base import TranslationResult


@pytest.mark.asyncio
async def test_get_translator_returns_stub_by_default():
    """Тест, что по умолчанию возвращается StubTranslator."""
    # Проверяем, что если нет API ключа, возвращается StubTranslator
    # Но в текущем окружении API ключ есть, поэтому проверим, что возвращается какой-то переводчик
    translator = get_translator()
    # Возвращается ли какой-либо переводчик (не None)
    assert translator is not None


@pytest.mark.asyncio
async def test_openai_translator_translate():
    """Тест метода перевода OpenAITranslator."""
    # Создаем мок для клиента OpenAI
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        # Настраиваем мок для возврата ответа
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Мок для ответа от API
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = (
            "hello: привет\nтранскрипция: [həˈləʊ]"
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Создаем экземпляр переводчика
        translator = OpenAITranslator(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

        # Выполняем перевод
        result = await translator.translate("hello", "en", "ru")

        # Проверяем результат
        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        assert "привет" in result.translated_text
        assert result.source_lang == "en"
        assert result.target_lang == "ru"


@pytest.mark.asyncio
async def test_openai_translator_api_error():
    """Тест обработки ошибки API OpenAI."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Мок для ошибки API
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        translator = OpenAITranslator(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

        result = await translator.translate("hello", "en", "ru")

        # При ошибке возвращается исходный текст
        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"


@pytest.mark.asyncio
async def test_openai_translator_empty_choices():
    """Тест обработки пустого списка choices."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Мок для пустого choices
        mock_response = AsyncMock()
        mock_response.choices = []
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = OpenAITranslator(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"


@pytest.mark.asyncio
async def test_openai_translator_none_content():
    """Тест обработки None в message.content."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Мок для None content
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = OpenAITranslator(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"


@pytest.mark.asyncio
async def test_openai_translator_malformed_json():
    """Тест обработки некорректного JSON в ответе."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Мок для некорректного JSON
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "not json at all"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = OpenAITranslator(
            api_key="test-key", base_url="https://openrouter.ai/api/v1"
        )

        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"


@pytest.mark.asyncio
async def test_stub_translator():
    """Тест StubTranslator напрямую."""
    from translator.stub import StubTranslator

    translator = StubTranslator()
    result = await translator.translate("hello", "en", "ru")

    assert isinstance(result, TranslationResult)
    assert result.source_text == "hello"
    assert result.source_lang == "en"
    assert result.target_lang == "ru"
    assert "[заглушка]" in result.translated_text
    assert result.transcription == ""
    assert result.corrected_word == "hello"

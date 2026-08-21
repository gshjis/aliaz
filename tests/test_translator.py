"""Тесты для сервиса перевода."""

from unittest.mock import AsyncMock, patch

import pytest
from translator import OpenAITranslator, get_translator
from translator.base import TranslationResult
from translator.stub import StubTranslator


def _make_translator() -> OpenAITranslator:
    """Создать OpenAITranslator с тестовыми настройками."""
    return OpenAITranslator(
        api_key="test-key", base_url="https://openrouter.ai/api/v1"
    )


def _mock_response(content: str) -> AsyncMock:
    """Создать мок-ответ OpenAI с заданным контентом."""
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = content
    return mock_response


@pytest.mark.asyncio
async def test_get_translator_returns_stub_by_default():
    """Тест, что без API-ключа возвращается StubTranslator."""
    with patch("translator.settings.openai_api_key", None):
        # Сбрасываем кэш, чтобы фабрика пересоздала инстанс
        import translator

        translator._translator = None
        result = get_translator()
        assert isinstance(result, StubTranslator)
        translator._translator = None


@pytest.mark.asyncio
async def test_get_translator_returns_openai_when_key_set():
    """Тест, что при наличии API-ключа возвращается OpenAITranslator."""
    with patch("translator.settings.openai_api_key", "test-key"):
        import translator

        translator._translator = None
        result = get_translator()
        assert isinstance(result, OpenAITranslator)
        translator._translator = None


@pytest.mark.asyncio
async def test_get_translator_uses_settings():
    """Тест, что фабрика передаёт настройки в OpenAITranslator."""
    with (
        patch("translator.settings.openai_api_key", "test-key"),
        patch("translator.settings.openai_base_url", "https://example.com/v1"),
        patch("translator.settings.openai_model", "test-model"),
        patch("translator.OpenAITranslator") as mock_cls,
    ):
        import translator

        translator._translator = None
        get_translator()
        mock_cls.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="test-model",
        )
        translator._translator = None


@pytest.mark.asyncio
async def test_openai_translator_translate():
    """Тест корректного JSON-парсинга ответа OpenAITranslator."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '{"corrected_word": "hello", "translation": "привет", '
                '"transcription": "[привет]", "language_swapped": false}'
            )
        )

        translator = _make_translator()

        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        assert result.translated_text == "привет"
        assert result.transcription == "[привет]"
        assert result.corrected_word == "hello"
        assert result.source_lang == "en"
        assert result.target_lang == "ru"
        assert result.language_swapped is False


@pytest.mark.asyncio
async def test_openai_translator_uses_json_mode():
    """Тест, что запрос использует JSON mode (response_format)."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '{"corrected_word": "hello", "translation": "привет", '
                '"transcription": "[привет]", "language_swapped": false}'
            )
        )

        translator = _make_translator()
        await translator.translate("hello", "en", "ru")

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_openai_translator_prompt_mentions_json():
    """Тест, что в сообщениях присутствует слово json (требование JSON mode)."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '{"corrected_word": "hello", "translation": "привет", '
                '"transcription": "[привет]", "language_swapped": false}'
            )
        )

        translator = _make_translator()
        await translator.translate("hello", "en", "ru")

        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]
        all_text = " ".join(m["content"] for m in messages).lower()
        assert "json" in all_text


@pytest.mark.asyncio
async def test_transcription_on_target_language():
    """Тест, что промпт требует транскрипцию на языке перевода (target_lang)."""
    translator = _make_translator()
    prompt = translator._build_system_prompt("en", "ru")

    assert "target_lang" in prompt
    assert "языке ПЕРЕВОДА" in prompt
    assert "кириллицей" in prompt


@pytest.mark.asyncio
async def test_openai_translator_guaranteed_fields():
    """Тест, что отсутствующие поля заполняются дефолтами."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        # Ответ без transcription и language_swapped
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '{"corrected_word": "hello", "translation": "привет"}'
            )
        )

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert result.transcription == ""
        assert result.language_swapped is False
        assert result.corrected_word == "hello"


@pytest.mark.asyncio
async def test_openai_translator_missing_corrected_word():
    """Тест, что при отсутствии corrected_word используется исходный текст."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '{"translation": "привет", "transcription": "[привет]"}'
            )
        )

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert result.corrected_word == "hello"
        assert result.source_text == "hello"


@pytest.mark.asyncio
async def test_openai_translator_language_swapped_backend_retries():
    """Тест авто-смены языков на бэкенде при language_swapped=true.

    Бэкенд должен повторить запрос с поменяными source/target местами
    и вернуть результат с language_swapped=True и исправленными языками.
    """
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Первый вызов: ввод на ru, но source_lang=en -> language_swapped=true
        first = _mock_response(
            '{"corrected_word": "привет", "translation": "hello", '
            '"transcription": "[hello]", "language_swapped": true}'
        )
        # Второй вызов (после смены языков): source=ru, target=en
        second = _mock_response(
            '{"corrected_word": "привет", "translation": "hello", '
            '"transcription": "[hello]", "language_swapped": false}'
        )
        mock_client.chat.completions.create = AsyncMock(
            side_effect=[first, second]
        )

        translator = _make_translator()
        result = await translator.translate("привет", "en", "ru")

        assert result.language_swapped is True
        assert result.source_lang == "ru"
        assert result.target_lang == "en"
        assert result.translated_text == "hello"
        assert result.corrected_word == "привет"

        # Проверяем, что запрос был сделан дважды
        assert mock_client.chat.completions.create.call_count == 2
        # Второй запрос должен использовать поменяные языки
        _, kwargs = mock_client.chat.completions.create.call_args_list[1]
        messages = kwargs["messages"]
        system_content = messages[0]["content"]
        assert "с ru на en" in system_content


@pytest.mark.asyncio
async def test_openai_translator_json_fence():
    """Тест снятия ```json```-обрамления в ответе."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_response(
                '```json\n{"corrected_word": "hello", "translation": "привет", '
                '"transcription": "[привет]"}\n```'
            )
        )

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.translated_text == "привет"
        assert result.corrected_word == "hello"


@pytest.mark.asyncio
async def test_openai_translator_api_error():
    """Тест graceful-обработки ошибки API OpenAI."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        from openai import APIError

        mock_client.chat.completions.create = AsyncMock(
            side_effect=APIError("API Error", request=None, body=None)
        )

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        # Fallback не должен раскрывать детали ошибки
        assert "ошибка" not in result.translated_text
        assert result.translated_text == ""
        assert result.language_swapped is False


@pytest.mark.asyncio
async def test_openai_translator_empty_choices():
    """Тест обработки пустого списка choices."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = []
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        assert result.translated_text == ""
        assert result.language_swapped is False


@pytest.mark.asyncio
async def test_openai_translator_none_content():
    """Тест обработки None в message.content."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        assert result.translated_text == ""
        assert result.language_swapped is False


@pytest.mark.asyncio
async def test_openai_translator_malformed_json():
    """Тест graceful-обработки некорректного JSON в ответе."""
    with patch("translator.openai.AsyncOpenAI") as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "not json at all"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        translator = _make_translator()
        result = await translator.translate("hello", "en", "ru")

        assert isinstance(result, TranslationResult)
        assert result.source_text == "hello"
        # Сырой текст не должен попадать в перевод
        assert result.translated_text == ""
        assert result.language_swapped is False


@pytest.mark.asyncio
async def test_stub_translator():
    """Тест StubTranslator напрямую."""
    translator = StubTranslator()
    result = await translator.translate("hello", "en", "ru")

    assert isinstance(result, TranslationResult)
    assert result.source_text == "hello"
    assert result.source_lang == "en"
    assert result.target_lang == "ru"
    assert "[заглушка]" in result.translated_text
    assert result.transcription == ""
    assert result.corrected_word == "hello"
    assert result.language_swapped is False
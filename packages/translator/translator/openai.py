"""Реализация сервиса перевода с использованием OpenAI API."""

import json
import logging
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI
from translator.base import TranslationResult, Translator
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenAITranslator(Translator):
    """Переводчик с использованием OpenAI API.

    Возвращает перевод, транскрипцию и исправленное слово (нормализацию опечаток).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        """Инициализировать переводчик.

        Args:
            api_key: Ключ API для OpenAI.
            base_url: Базовый URL для API.
            model: Модель OpenAI для использования.
        """
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_base_url,
        )
        self._model = model or settings.openai_model

    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "ru",
    ) -> TranslationResult:
        """Перевести текст с source_lang на target_lang.

        Args:
            text: Текст для перевода.
            source_lang: Исходный язык.
            target_lang: Целевой язык.

        Returns:
            Результат перевода с транскрипцией и исправленным словом.
        """
        data = await self._request_translation(text, source_lang, target_lang)
        if data is None:
            return self._fallback(text, source_lang, target_lang)

        fields = self._extract_fields(data, text)

        if fields["language_swapped"]:
            # Коллизия языков: ввод не на source_lang. Бэкенд сам меняет
            # языки местами и повторяет запрос один раз в правильном направлении.
            new_source = target_lang
            new_target = source_lang
            data = await self._request_translation(text, new_source, new_target)
            if data is None:
                return self._fallback(text, new_source, new_target)
            fields = self._extract_fields(data, text)
            return TranslationResult(
                source_text=fields["corrected_word"],
                translated_text=fields["translation"],
                source_lang=new_source,
                target_lang=new_target,
                transcription=fields["transcription"],
                corrected_word=fields["corrected_word"],
                language_swapped=True,
            )

        return TranslationResult(
            source_text=fields["corrected_word"],
            translated_text=fields["translation"],
            source_lang=source_lang,
            target_lang=target_lang,
            transcription=fields["transcription"],
            corrected_word=fields["corrected_word"],
            language_swapped=False,
        )

    async def _request_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> dict[str, Any] | None:
        """Выполнить один запрос к OpenAI и вернуть распарсенный JSON.

        Args:
            text: Текст для перевода.
            source_lang: Исходный язык.
            target_lang: Целевой язык.

        Returns:
            Словарь с данными ответа или None при ошибке/пустом ответе.
        """
        system_prompt = self._build_system_prompt(source_lang, target_lang)
        user_prompt = f"Переведи слово или фразу: '{text}'"

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            result_text = self._extract_content(response)
            if not result_text:
                return None
            return self._parse_json(result_text)
        except (APIError, APIConnectionError, APITimeoutError) as exc:
            logger.warning("Ошибка OpenAI API при переводе: %s", exc)
            return None

    def _build_system_prompt(self, source_lang: str, target_lang: str) -> str:
        """Собрать системный промпт для модели.

        Args:
            source_lang: Исходный язык.
            target_lang: Целевой язык.

        Returns:
            Текст системного промпта.
        """
        return (
            f"Вы профессиональный переводчик. Переведите следующее слово или фразу "
            f"с {source_lang} на {target_lang}. "
            "Исправьте возможные опечатки в исходном слове. "
            "В ответе обязательно верните JSON-объект с полями: "
            "corrected_word (исправленное слово на исходном языке), "
            "translation (перевод), "
            "transcription (транскрипция/произношение), "
            "language_swapped (true, если ввод фактически на другом языке, "
            "не совпадающем с source_lang; иначе false). "
            "ТРАНСКРИПЦИЯ ОБЯЗАТЕЛЬНО должна быть на языке ПЕРЕВОДА (target_lang), "
            "а не на языке источника. Например, если переводим с английского на русский, "
            "транскрипция пишется русскими буквами (кириллицей). "
            "Если ввод на языке, отличном от source_lang (коллизия языков), "
            "установите language_swapped в true и переведите в правильном направлении: "
            "translation — это перевод введённого слова на язык, противоположный языку ввода. "
            "Пример ответа: "
            '{"corrected_word": "word", "translation": "слово", '
            '"transcription": "[слово]", "language_swapped": false}.'
        )

    def _extract_content(self, response: Any) -> str | None:
        """Извлечь текстовый контент из ответа OpenAI.

        Args:
            response: Ответ API OpenAI.

        Returns:
            Текст ответа или None, если контент отсутствует.
        """
        if not response.choices:
            return None
        content = response.choices[0].message.content
        if not content:
            return None
        return content

    def _parse_json(self, content: str) -> dict[str, Any] | None:
        """Распарсить JSON из ответа, снимая ```json```-обрамление.

        Args:
            content: Сырой текст ответа.

        Returns:
            Словарь с данными или None, если JSON некорректен.
        """
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        if not cleaned:
            return None

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Не удалось распарсить JSON в ответе переводчика")
            return None

        if not isinstance(data, dict):
            logger.warning("Ответ переводчика не является JSON-объектом")
            return None
        return data

    def _extract_fields(self, data: dict[str, Any], text: str) -> dict[str, Any]:
        """Гарантированно извлечь поля из данных ответа с дефолтами.

        Args:
            data: Распарсенный JSON-объект ответа.
            text: Исходный текст (дефолт для corrected_word).

        Returns:
            Словарь с гарантированными полями corrected_word, translation,
            transcription и language_swapped.
        """
        return {
            "corrected_word": str(data.get("corrected_word") or text),
            "translation": str(data.get("translation") or ""),
            "transcription": str(data.get("transcription") or ""),
            "language_swapped": bool(data.get("language_swapped", False)),
        }

    def _fallback(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
    ) -> TranslationResult:
        """Вернуть результат-заглушку при ошибке перевода.

        Args:
            text: Исходный текст.
            source_lang: Исходный язык.
            target_lang: Целевой язык.

        Returns:
            Результат с исходным текстом и пустым переводом.
        """
        return TranslationResult(
            source_text=text,
            translated_text="",
            source_lang=source_lang,
            target_lang=target_lang,
            transcription="",
            corrected_word=text,
            language_swapped=False,
        )
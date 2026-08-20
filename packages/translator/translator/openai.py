"""Реализация сервиса перевода с использованием OpenAI API."""

import json
import os
from typing import Optional

from openai import AsyncOpenAI
from translator.base import TranslationResult, Translator


class OpenAITranslator(Translator):
    """Переводчик с использованием OpenAI API.

    Возвращает перевод, транскрипцию и исправленное слово (нормализацию опечаток).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """Инициализировать переводчик.

        Args:
            api_key: Ключ API для OpenAI.
            base_url: Базовый URL для API.
            model: Модель OpenAI для использования.
        """
        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        self._model = model

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
        system_prompt = (
            f"Вы профессиональный переводчик. Переведите следующее слово или фразу "
            f"с {source_lang} на {target_lang}. "
            "Исправьте возможные опечатки в исходном слове. "
            "В ответе обязательно верните JSON с полями: "
            "corrected_word (исправленное слово на исходном языке), "
            "translation (перевод), "
            "transcription (транскрипция/произношение). "
            "Пример ответа: "
            '{"corrected_word": "word", "translation": "слово", "transcription": "[слово]"}. '
            "Если ввод — на русском, и нужна транскрипция для русского слова, "
            "верните её кириллицей в квадратных скобках."
        )

        user_prompt = f"Переведи слово или фразу: '{text}'"

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            result_text = response.choices[0].message.content
            if result_text is None:
                result_text = text

            # Удаляем обрамляющие ```json ``` если есть
            cleaned = result_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

            corrected_word = text
            translation = ""
            transcription = ""

            try:
                data = json.loads(cleaned)
                corrected_word = data.get("corrected_word", text) or text
                translation = data.get("translation", "") or ""
                transcription = data.get("transcription", "") or ""
            except Exception:
                # Если не JSON — пытаемся извлечь данные из текста
                translation = cleaned
                transcription = ""
                corrected_word = text

            return TranslationResult(
                source_text=corrected_word,
                translated_text=translation,
                source_lang=source_lang,
                target_lang=target_lang,
                transcription=transcription,
                corrected_word=corrected_word,
            )
        except Exception as e:
            return TranslationResult(
                source_text=text,
                translated_text=f"[ошибка перевода: {str(e)}]",
                source_lang=source_lang,
                target_lang=target_lang,
                transcription="",
                corrected_word=text,
            )

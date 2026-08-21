"""Заглушка сервиса перевода.

Используется до подключения реального внешнего сервиса-переводчика.
"""

from translator.base import TranslationResult, Translator


class StubTranslator(Translator):
    """Возвращает фиктивный перевод, не обращаясь к внешним сервисам."""

    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "ru",
    ) -> TranslationResult:
        return TranslationResult(
            source_text=text,
            translated_text=f"[заглушка] {text}",
            source_lang=source_lang,
            target_lang=target_lang,
            transcription="",
            corrected_word=text,
            language_swapped=False,
        )

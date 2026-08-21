"""Pydantic-схемы для слов."""

from datetime import datetime

from pydantic import BaseModel, Field


class WordCreateRequest(BaseModel):
    """Данные для добавления слова."""

    word_en: str = Field(min_length=1, max_length=255)
    source_lang: str = "en"
    target_lang: str = "ru"


class WordResponse(BaseModel):
    """Слово с переводом."""

    id: int
    word_en: str
    translation: str | None
    transcription: str | None
    corrected_word: str | None
    language_swapped: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}

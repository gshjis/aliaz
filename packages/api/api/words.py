"""Роутер слов: запись, просмотр и удаление слов пользователя."""

from auth import get_current_user
from database.connection import get_db
from database.models import User, Word
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.words import WordCreateRequest, WordResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from translator import get_translator

router = APIRouter(prefix="/words", tags=["words"])


@router.post(
    "",
    response_model=WordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_word(
    payload: WordCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Word:
    """Добавить слово, получив перевод через сервис-переводчик."""
    translator = get_translator()
    result = await translator.translate(
        payload.word_en,
        source_lang=payload.source_lang,
        target_lang=payload.target_lang,
    )

    word = Word(
        owner_id=current_user.id,
        word_en=payload.word_en,
        translation=result.translated_text,
        transcription=result.transcription,
        corrected_word=result.corrected_word or payload.word_en,
        language_swapped=result.language_swapped,
    )
    db.add(word)
    await db.commit()
    await db.refresh(word)
    return word


@router.get("", response_model=list[WordResponse])
async def list_words(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Word]:
    """Вернуть список слов текущего пользователя."""
    result = await db.scalars(
        select(Word)
        .where(Word.owner_id == current_user.id)
        .order_by(Word.created_at.desc())
    )
    return list(result.all())


@router.get("/{word_id}", response_model=WordResponse)
async def get_word(
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Word:
    """Вернуть одно слово текущего пользователя."""
    word = await db.get(Word, word_id)
    if word is None or word.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found",
        )
    return word


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_word(
    word_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить слово текущего пользователя."""
    word = await db.get(Word, word_id)
    if word is None or word.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found",
        )
    await db.delete(word)
    await db.commit()

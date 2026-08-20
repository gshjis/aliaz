"""Модели базы данных."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_nickname: Mapped[str | None] = mapped_column(String(255))
    words: Mapped[list["Word"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    word_en: Mapped[str] = mapped_column(String(255), nullable=False)
    translation: Mapped[str | None] = mapped_column(String(255))
    transcription: Mapped[str | None] = mapped_column(String(255), nullable=True)
    corrected_word: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner: Mapped["User"] = relationship(back_populates="words")

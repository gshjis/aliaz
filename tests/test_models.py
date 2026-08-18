"""Тесты моделей базы данных (пакет database.models)."""

from database.models import Base, User, Word
from sqlalchemy import inspect


def test_table_names() -> None:
    """Имена таблиц соответствуют ожидаемым."""
    assert User.__tablename__ == "users"
    assert Word.__tablename__ == "words"


def test_models_are_declarative() -> None:
    """Модели наследуются от декларативной базы."""
    assert issubclass(User, Base)
    assert issubclass(Word, Base)


def test_user_columns_constraints() -> None:
    """Поля User имеют ожидаемые ограничения."""
    cols = User.__table__.columns
    assert cols["nickname"].nullable is False
    assert cols["nickname"].unique is True
    assert cols["email"].nullable is False
    assert cols["email"].unique is True
    assert cols["password_hash"].nullable is False


def test_word_columns_constraints() -> None:
    """Поля Word имеют ожидаемые ограничения."""
    cols = Word.__table__.columns
    assert cols["owner_id"].nullable is False
    assert cols["word_en"].nullable is False
    assert cols["translation"].nullable is True


def test_user_word_relationship() -> None:
    """Связь User.words <-> Word.owner настроена корректно."""
    user_inspect = inspect(User)
    word_inspect = inspect(Word)

    user_rels = {r.key for r in user_inspect.relationships}
    word_rels = {r.key for r in word_inspect.relationships}
    assert "words" in user_rels
    assert "owner" in word_rels

"""Тесты моделей базы данных (пакет database.models)."""

from database.models import Base, RefreshToken, User, Word
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


def test_user_unique_constraints() -> None:
    """Поля nickname и email имеют уникальность."""
    cols = User.__table__.columns
    assert cols["nickname"].unique is True
    assert cols["email"].unique is True


def test_word_cascade_delete_orphan() -> None:
    """Связь Word.owner имеет cascade delete-orphan."""
    from sqlalchemy import inspect

    user_inspect = inspect(User)
    words_rel = user_inspect.relationships["words"]
    assert "delete-orphan" in words_rel.cascade


def test_word_created_at_default_is_callable() -> None:
    """default для created_at — callable, а не фиксированное значение."""
    col = Word.__table__.columns["created_at"]
    assert callable(col.default.arg)


def test_refresh_token_table() -> None:
    """Модель RefreshToken имеет ожидаемую таблицу и поля."""
    assert RefreshToken.__tablename__ == "refresh_tokens"
    cols = RefreshToken.__table__.columns
    assert cols["jti"].unique is True
    assert cols["jti"].nullable is False
    assert cols["user_id"].nullable is False
    assert cols["expires_at"].nullable is False
    assert cols["revoked"].nullable is False


def test_user_refresh_token_relationship() -> None:
    """Связь User.refresh_tokens <-> RefreshToken.user настроена."""
    user_inspect = inspect(User)
    token_inspect = inspect(RefreshToken)
    user_rels = {r.key for r in user_inspect.relationships}
    token_rels = {r.key for r in token_inspect.relationships}
    assert "refresh_tokens" in user_rels
    assert "user" in token_rels

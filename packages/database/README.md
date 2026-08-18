# database

Асинхронный слой базы данных на SQLAlchemy.

## Особенности
- Поддержка async/await
- Готовые модели User и Word
- Асинхронные сессии и движок
- Функция инициализации БД

## Таблицы

### users
Основная таблица пользователей.

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ, автоинкремент |
| nickname | VARCHAR(255) | Никнейм пользователя (уникальный) |
| email | VARCHAR(255) | Email пользователя (уникальный) |
| telegram_nickname | VARCHAR(255) | Telegram никнейм (опционально) |

### words
Таблица слов для изучения.

| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER | Первичный ключ, автоинкремент |
| created_at | DATETIME | Дата создания записи |
| owner_id | INTEGER | Внешний ключ к users.id |
| word_en | VARCHAR(255) | Английское слово |

## Установка
```bash
poetry add "database @ file:///../../database"
```

## Использование
```python
from database import Base, engine, init_db, get_db

# Создание таблиц
await init_db()

# Получение сессии
async for db in get_db():
    # Работа с базой
    pass
```

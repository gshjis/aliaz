# API Aliaz

Базовый URL (локально): `http://localhost:8000`. Если перед приложением стоит nginx — `http://localhost`.

Все ответы — JSON. Текущая версия API имеет префикс **`/api/v1`**.

## Аутентификация

Защищённые эндпоинты требуют заголовок:

```
Authorization: Bearer <access_token>
```

При входе/регистрации выдаётся пара токенов:
- `access_token` — короткоживущий (по умолчанию 60 мин), используется для запросов.
- `refresh_token` — долгоживущий (по умолчанию 7 дней), используется только для обновления `access_token`.

Когда `access_token` истёк, отправьте `refresh_token` на `POST /api/v1/auth/refresh` и получите новую пару токенов (refresh ротируется).

## Эндпоинты

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| GET | `/` | нет | Проверка работоспособности |
| POST | `/api/v1/auth/register` | нет | Регистрация, возвращает токены |
| POST | `/api/v1/auth/login` | нет | Вход, возвращает токены |
| POST | `/api/v1/auth/refresh` | refresh-токен в теле | Обновление access-токена |
| GET | `/api/v1/auth/me` | access | Данные текущего пользователя |
| POST | `/api/v1/words` | access | Добавить слово (с переводом) |
| GET | `/api/v1/words` | access | Список слов пользователя |
| GET | `/api/v1/words/{id}` | access | Одно слово |
| DELETE | `/api/v1/words/{id}` | access | Удалить слово |

### GET /
```json
{ "status": "ok", "message": "Welcome to aliaz API" }
```

### POST /api/v1/auth/register
```json
// тело запроса
{ "nickname": "alice", "email": "alice@example.com", "password": "password123", "telegram_nickname": "@alice" }

// ответ 201
{ "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer" }
```

### POST /api/v1/auth/login
```json
// тело запроса
{ "email": "alice@example.com", "password": "password123" }

// ответ 200
{ "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer" }
```

### POST /api/v1/auth/refresh
```json
// тело запроса
{ "refresh_token": "<jwt>" }

// ответ 200 — новая пара токенов
{ "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer" }
```
Ошибки: `401`, если refresh-токен невалиден/просрочен или это не refresh-токен.

### GET /api/v1/auth/me
Заголовок: `Authorization: Bearer <access_token>`
```json
// ответ 200
{ "id": 1, "nickname": "alice", "email": "alice@example.com", "telegram_nickname": "@alice" }
```

### POST /api/v1/words
Заголовок: `Authorization: Bearer <access_token>`
```json
// тело запроса
{ "word_en": "hello" }

// ответ 201
{ "id": 1, "word_en": "hello", "translation": "[заглушка] hello", "created_at": "2026-08-19T12:00:00" }
```
> Перевод пока отдаётся заглушкой (`[заглушка] ...`).

### GET /api/v1/words
Заголовок: `Authorization: Bearer <access_token>`
```json
// ответ 200 — массив, новые сверху
[ { "id": 2, "word_en": "world", "translation": "[заглушка] world", "created_at": "..." },
  { "id": 1, "word_en": "hello", "translation": "[заглушка] hello", "created_at": "..." } ]
```

### GET /api/v1/words/{id} и DELETE /api/v1/words/{id}
Заголовок: `Authorization: Bearer <access_token>`. `GET` возвращает объект слова (200) или 404; `DELETE` возвращает 204 (без тела) или 404.

## Коды ошибок

- `401` — нет токена, он невалиден/просрочен или не того типа
- `409` — email или nickname уже заняты
- `404` — объект не найден или нет доступа
- `422` — невалидное тело запроса (не прошло валидацию)

## Пример (fetch)

```js
// 1. Вход — получаем обе пары токенов
const { access_token, refresh_token } = await fetch("/api/v1/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
}).then((r) => r.json());

// 2. Запрос с access-токеном
let words = await fetch("/api/v1/words", {
  headers: { Authorization: `Bearer ${access_token}` },
}).then((r) => r.json());

// 3. Когда access-токен истёк — обновляем через refresh-токен
const refreshed = await fetch("/api/v1/auth/refresh", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refresh_token }),
}).then((r) => r.json());
// refreshed.access_token / refreshed.refresh_token — используем дальше
```

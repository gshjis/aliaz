# Развёртывание на сервере: хостовый nginx + Cloudflare

Этот документ объясняет, как проект aliaz работает на боевом сервере, когда
перед ним стоит **хостовый (не Docker) nginx**, а домен обслуживается через
**Cloudflare**. Здесь описана архитектура, поток запросов, переменные окружения
и пошаговая настройка.

---

## 1. Общая схема

```
Пользователь (браузер)
        │
        ▼
   Cloudflare (DNS + прокси, TLS-терминация на edge)
        │  https://your-domain.com
        ▼
   Хостовый nginx (порт 443, TLS-сертификат)
        │
        ├── /api/*  ───────────────►  web:8000  (FastAPI, Docker)
        │
        └── /*      ───────────────►  frontend:3000  (nginx, статика React)
```

- **Cloudflare** — DNS-провайдер и (опционально) прокси. Он принимает HTTPS-запросы
  на своём edge и пересылает их на ваш сервер.
- **Хостовый nginx** — единая точка входа на сервере. Он завершает TLS
  (если сертификат на сервере) и маршрутизирует запросы:
  - пути `/api/*` → контейнер `web` (FastAPI, порт 8000);
  - все остальные пути → контейнер `frontend` (nginx, статика React, порт 3000).
- **Docker-контейнеры** (`web`, `frontend`, `db`) живут внутри docker-сети и
  **не должны быть доступны напрямую из интернета** — только через хостовый nginx.

---

## 2. Почему так, а не иначе

### 2.1. Единая точка входа (single origin)
Фронтенд обращается к API по относительному пути `/api/v1`
(см. [`frontend/.env.example`](frontend/.env.example:1) — `VITE_API_BASE_URL=/api/v1`).
Это значит, что браузер ходит на **тот же домен**, с которого загрузил страницу.
Хостовый nginx сам решает, куда направить `/api/*` (на `web`) и всё остальное (на `frontend`).

Преимущества:
- **Нет CORS-проблем**: браузер видит один origin (`https://your-domain.com`),
  а не два разных (фронт и API).
- **Один TLS-сертификат** на домен.
- **Одна точка управления** трафиком, кэшем, заголовками безопасности.

### 2.2. Два nginx: хостовый и в контейнере frontend
- **Хостовый nginx** — «внешний» шлюз. Он виден из интернета, слушает 80/443,
  терминирует TLS и проксирует на контейнеры.
- **nginx внутри `frontend`** — «внутренний» сервер статики. Он отдаёт собранный
  React (`dist/`) и тоже умеет проксировать `/api/` на `web:8000`
  (см. [`frontend/nginx.conf`](frontend/nginx.conf:9)). Это полезно, когда фронтенд
  открывают напрямую (например, в разработке), но в продакшене внешний шлюз
  перехватывает трафик раньше.

> В продакшене достаточно, чтобы хостовый nginx проксировал `/api/` на `web:8000`
> и статику на `frontend:3000`. Внутренний прокси в `frontend/nginx.conf` не мешает,
> но и не обязателен, если внешний шлюз уже маршрутизирует `/api/`.

---

## 3. Поток запроса (пошагово)

### 3.1. Запрос к главной странице
1. Браузер → `https://your-domain.com/`.
2. Cloudflare → хостовый nginx (порт 443).
3. Хостовый nginx: путь `/` не начинается с `/api/` → проксирует на `frontend:3000`.
4. `frontend` отдаёт `index.html` + JS/CSS бандлы.
5. Браузер рендерит React-приложение (главная страница с карточками).

### 3.2. Запрос к API (например, логин)
1. Браузер: `POST https://your-domain.com/api/v1/auth/login`.
2. Cloudflare → хостовый nginx.
3. Хостовый nginx: путь начинается с `/api/` → проксирует на `web:8000`.
4. FastAPI обрабатывает запрос, работает с Postgres, возвращает JSON.
5. Ответ возвращается тем же путём обратно в браузер.

### 3.3. SPA-маршруты (например, `/study`)
1. Браузер: `https://your-domain.com/study`.
2. Хостовый nginx: путь не `/api/` → проксирует на `frontend:3000`.
3. Внутренний nginx фронтенда: `try_files $uri $uri/ /index.html` — отдаёт
   `index.html` для любого пути (SPA fallback).
4. React-роутер сам показывает нужную страницу.

---

## 4. Переменные окружения для продакшена

### 4.1. Корневой `.env` (для контейнеров `web` и `db`)

| Переменная | Значение в продакшене |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://<user>:<pass>@db:5432/<db>` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | реальные учётные данные БД |
| `ALLOWED_HOSTS` | `["your-domain.com", "www.your-domain.com"]` |
| `ALLOWED_ORIGINS` | `["https://your-domain.com", "https://www.your-domain.com"]` |
| `JWT_SECRET` | **длинный случайный ключ (≥32 байта)** |
| `OPENAI_API_KEY` | реальный ключ (не утёкший) |
| `DEBUG` | `false` |
| `HOST` / `PORT` | `0.0.0.0` / `8000` |

> **Важно про CORS.** В [`main.py`](packages/api/api/main.py:33) CORS использует
> `settings.allowed_origins or settings.allowed_hosts`. Если `ALLOWED_ORIGINS` не задан,
> берутся `ALLOWED_HOSTS` **без схемы** (`your-domain.com`), а браузер шлёт Origin
> вида `https://your-domain.com` — совпадения не будет, и запросы заблокируются.
> Поэтому **обязательно** задайте `ALLOWED_ORIGINS` с полными `https://`-origin'ами.

### 4.2 `frontend/.env` (собирается в бандл)
| Переменная | Значение |
|---|---|
| `VITE_API_BASE_URL` | `/api/v1` (относительный путь — работает через хостовый nginx) |

> `VITE_*` переменные подставляются **на этапе сборки** (в `frontend/Dockerfile`).
> После изменения — пересобрать контейнер `frontend`.

---

## 5. Пошаговая настройка

### Шаг 1. Cloudflare: DNS
1. В панели Cloudflare добавьте домен (или зону).
2. Создайте A-запись: `@` → IP вашего сервера, `www` → IP сервера.
3. (Опционально) включите прокси Cloudflare (оранжевое облако) для кэша и защиты.
   - Если включён прокси, Cloudflare терминирует TLS своим сертификатом и шлёт
     на сервер по HTTP (или по HTTPS с Origin-сертификатом).

### Шаг 2. Хостовый nginx: TLS-сертификат
Вариант A — сертификат на сервере (Let's Encrypt):
```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot -d your-domain.com -d www.your-domain.com
```
Вариант B — Cloudflare Origin-сертификат (если прокси Cloudflare включён):
- Сгенерируйте Origin-сертификат в Cloudflare и укажите его в nginx.

### Шаг 3. Хостовый nginx: конфиг
Создайте `/etc/nginx/sites-available/aliaz`:

```nginx
# Редирект HTTP → HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}

# HTTPS-сервер
server {
    listen 443 ssl;
    http2 on;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Заголовки безопасности
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Проксирование API на контейнер web (FastAPI, порт 8000)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Статика фронтенда (контейнер frontend, порт 3000)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте и перезагрузите:
```bash
sudo ln -s /etc/nginx/sites-available/aliaz /etc/nginx/sites-enabled/aliaz
sudo nginx -t
sudo systemctl reload nginx
```

> **Почему `127.0.0.1:8000` и `127.0.0.1:3000`?** В [`docker-compose.yml`](docker-compose.yml:38)
> контейнеры `web` и `frontend` публикуются только на loopback
> (`127.0.0.1:${PORT}` и `127.0.0.1:${FRONTEND_PORT:-3000}`). Это безопасно:
> наружу смотрит только хостовый nginx, а контейнеры недоступны из интернет напрямую.

### Шаг 4. Переменные окружения
1. Скопируйте `.env.example` → `.env` и заполните продакшн-значения
   (см. таблицу выше). **Обязательно** смените `JWT_SECRET` и `OPENAI_API_KEY`.
2. Убедитесь, что `.env` не попал в git-историю (он в `.gitignore`).

### Шаг 5. Запуск контейнеров
```bash
docker compose up -d --build
```
- `web` поднимется, выполнит `init_db.py` (создаст таблицы) и запустит uvicorn.
- `frontend` соберёт React и отдаст статику.
- Проверьте healthcheck: `curl http://127.0.0.1:8000/health` → `200`.

### Шаг 6. Проверка через домен
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://your-domain.com/          # 200
curl -s -o /dev/null -w "%{http_code}\n" https://your-domain.com/health    # 200 (через /api? нет)
curl -s -o /dev/null -w "%{http_code}\n" https://your-domain.com/api/v1/health  # 200
```

---

## 6. Частые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| Браузер блокирует запросы к API | `ALLOWED_ORIGINS` не задан или не совпадает с Origin | Задать `ALLOWED_ORIGINS` с `https://`-origin'ами |
| `502 Bad Gateway` от хостового nginx | Контейнер не запущен или порт не совпадает | Проверить `docker compose ps`, порты в nginx |
| `404` на `/health` | Запрос ушёл не на `web` | Убедиться, что `/api/` проксируется на `web:8000` |
| `InsecureKeyLengthWarning` в логах | `JWT_SECRET` короче 32 байт | Сгенерировать длинный ключ |
| Данные теряются при пересборке | SQLite-файл в контейнере без volume | Использовать Postgres (уже настроен в compose) |

---

## 7. Безопасность (чек-лист перед запуском)

- [ ] `JWT_SECRET` — длинный случайный ключ (≥32 байт), не в git.
- [ ] `OPENAI_API_KEY` — новый, утёкший отозван.
- [ ] `ALLOWED_HOSTS` и `ALLOWED_ORIGINS` — реальный домен.
- [ ] `DEBUG=false`.
- [ ] HTTPS включён (Let's Encrypt или Cloudflare Origin).
- [ ] Контейнеры не открыты наружу (только loopback).
- [ ] Rate limiting на `/auth/login` и `/auth/register` усилен (сейчас глобальный лимит).
- [ ] Бэкапы БД настроены.
- [ ] Миграции БД — через Alembic или ручные `ALTER TABLE` (create_all не добавляет колонки к существующим таблицам).
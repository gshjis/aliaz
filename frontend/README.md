# Aliaz Frontend

Фронтенд-контейнер для FastAPI-бэкенда проекта Aliaz. SPA на React + Vite + TypeScript.

## Стек

- **React 18** + **TypeScript**
- **Vite** — сборка и dev-сервер
- **react-router-dom v6** — маршрутизация
- **Zustand** — управление состоянием (auth)
- **nginx** — раздача статики и reverse proxy на API

## Структура

```
frontend/
├── package.json
├── tsconfig.json / tsconfig.node.json
├── vite.config.ts
├── index.html
├── Dockerfile            # multi-stage: node build → nginx serve
├── nginx.conf            # proxy /api → web:8000, SPA fallback
├── .env.example
└── src/
    ├── main.tsx          # точка входа
    ├── App.tsx           # роутер
    ├── index.css         # стили
    ├── api/
    │   ├── client.ts     # fetch-обёртка: Authorization, refresh при 401
    │   ├── auth.ts       # register / login / refresh / me
    │   └── words.ts      # createWord / listWords / getWord / deleteWord
    ├── store/
    │   └── authStore.ts  # Zustand: токены, user, login/logout/register
    ├── types/
    │   └── index.ts      # типы API
    ├── components/
    │   ├── Layout.tsx
    │   ├── ProtectedRoute.tsx
    │   └── WordCard.tsx
    └── pages/
        ├── LoginPage.tsx
        ├── RegisterPage.tsx
        └── WordsPage.tsx
```

## Локальный запуск

```bash
cd frontend
npm install
npm run dev
```

Dev-сервер Vite поднимается на `http://localhost:5173`. В `vite.config.ts` настроен
proxy: запросы `/api/*` перенаправляются на `http://localhost:8000` (локальный uvicorn).

## Проксирование (production)

В Docker фронтенд отдаёт nginx, который:

- `location /api/` → `proxy_pass http://web:8000` (сервис API в docker-сети);
- `location /` → SPA fallback `try_files $uri $uri/ /index.html`.

Фронтенд обращается к API по относительному пути `/api/v1/...`, поэтому CORS не нужен —
единый origin.

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `VITE_API_BASE_URL` | Базовый URL API | `/api/v1` |

Переменные Vite подставляются на этапе сборки. Для локальной разработки скопируйте
`.env.example` в `.env` при необходимости.

## Docker

```bash
docker compose build frontend
docker compose up -d frontend
```

Фронтенд доступен на `http://localhost:${FRONTEND_PORT:-3000}`.
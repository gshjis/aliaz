# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Устанавливаем в системный site-packages (не в виртуальное окружение),
# чтобы упростить копирование зависимостей в runtime-слой.
RUN poetry config virtualenvs.create false

# Кэшируемый слой: только манифесты зависимостей.
# Пересобирается исключительно при изменении pyproject.toml / poetry.lock.
COPY pyproject.toml poetry.lock ./

# Poetry 2.x требует, чтобы path-зависимости были валидными Python-пакетами.
# Копируем только манифесты (pyproject.toml + README.md) каждого пакета —
# они меняются редко, поэтому слой внешних зависимостей остаётся кэшируемым.
COPY packages/config/pyproject.toml packages/config/README.md packages/config/
COPY packages/database/pyproject.toml packages/database/README.md packages/database/
COPY packages/auth/pyproject.toml packages/auth/README.md packages/auth/
COPY packages/translator/pyproject.toml packages/translator/README.md packages/translator/
COPY packages/schemas/pyproject.toml packages/schemas/README.md packages/schemas/
COPY packages/api/pyproject.toml packages/api/README.md packages/api/

# Создаём include-каталоги с __init__.py (детерминированная операция, не зависит
# от содержимого кода), чтобы Poetry мог собрать editable-пакеты на этом слое.
RUN mkdir -p packages/config/config packages/database/database packages/auth/auth \
        packages/translator/translator packages/schemas/schemas packages/api/api \
    && touch packages/config/config/__init__.py packages/database/database/__init__.py \
        packages/auth/auth/__init__.py packages/translator/translator/__init__.py \
        packages/schemas/schemas/__init__.py packages/api/api/__init__.py

RUN poetry install --no-root --no-interaction --no-ansi

# Слой внутренних пакетов: пересобирается только при изменении кода.
COPY packages/ ./packages/
COPY init_db.py .

# Повторная установка: переустанавливает path-пакеты (editable installs)
# с учётом скопированного кода.
RUN poetry install --no-root --no-interaction --no-ansi

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Создаём непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app

# Копируем установленные зависимости из builder (системный site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Копируем entry-point скрипты (uvicorn, fastapi и др.), чтобы команда
# `uvicorn ...` из docker-compose работала в runtime.
COPY --from=builder /usr/local/bin /usr/local/bin

# Path-пакеты установлены как editable installs: их .pth-файлы ссылаются
# на абсолютный путь /build/packages. Копируем код в тот же путь, чтобы
# импорты (packages.api.api.main, database) работали без переустановки.
COPY --from=builder /build/packages/ /build/packages/
COPY --from=builder /build/init_db.py /app/init_db.py

# Значения по умолчанию; при запуске через docker-compose переменные
# (HOST, PORT) переопределяются из .env через env_file.
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Код пакетов лежит в /build/packages (editable .pth ссылаются на этот путь).
# PYTHONPATH=/build делает доступным импорт packages.api.api.main.
ENV PYTHONPATH=/build

CMD ["uvicorn", "packages.api.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости и скрипт инициализации БД
COPY requirements.txt .
COPY packages/ ./packages/
COPY init_db.py .

# Устанавливаем зависимости и локальные пакеты из единого requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем приложение от непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Значения по умолчанию; при запуске через docker-compose переменные
# (HOST, PORT) переопределяются из .env через env_file.
ENV HOST=0.0.0.0
ENV PORT=8000
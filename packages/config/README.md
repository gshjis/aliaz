# config

Глобальная конфигурация проекта на базе Pydantic Settings.

## Поля конфигурации

| Поле | Тип | По умолчанию | Описание |
|------|-----|-------------|----------|
| database_url | str | sqlite+aiosqlite:///./aliaz.db | URL подключения к базе данных |
| app_name | str | aliaz | Название приложения |
| app_version | str | 0.1.0 | Версия приложения |
| debug | bool | False | Режим отладки |
| host | str | 0.0.0.0 | Хост для запуска сервера |
| port | int | 8000 | Порт для запуска сервера |

## Особенности
- Загрузка настроек из .env файла
- Поддержка асинхронных приложений
- Централизованное управление конфигурацией

## Установка
```bash
poetry add "config @ file:///../../config"
```

## Использование
```python
from config import settings
print(settings.database_url)
```

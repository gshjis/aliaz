"""Скрипт для инициализации БД.

Он импортирует функцию ``init_db`` из пакета ``database`` и запускает её.
Скрипт используется в Dockerfile как часть команды запуска.
"""

import asyncio

from database import init_db


async def main() -> None:
    await init_db()


if __name__ == "__main__":
    asyncio.run(main())

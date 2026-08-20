"""Нагрузочный скрипт для API проекта Aliaz.

Запускается против уже поднятого docker-compose стенда.

Что делает:
1. Регистрирует указанное число пользователей (по умолчанию 1000).
2. Логинит их и получает access-токены.
3. Каждый пользователь добавляет случайное число слов (в диапазоне).
4. Считает метрики: RPS, p50/p95/p99 задержек, количество ошибок по типам.

Использование:
    python scripts/load_test.py \\
        --base-url http://localhost:8000 \\
        --users 1000 \\
        --words-min 1 --words-max 5 \\
        --concurrency 50

Слова берутся из встроенного списка; можно передать свой файл через --words-file.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import string
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_WORDS: list[str] = [
    "hello",
    "world",
    "python",
    "fastapi",
    "translator",
    "service",
    "docker",
    "compose",
    "load",
    "test",
    "apple",
    "banana",
    "orange",
    "computer",
    "keyboard",
    "singleton",
    "factory",
    "strategy",
    "observer",
    "decorator",
    "love",
    "peace",
    "freedom",
    "music",
    "book",
    "cat",
    "dog",
    "fish",
    "bird",
    "tree",
    "river",
    "mountain",
    "ocean",
    "forest",
    "desert",
    "city",
    "village",
    "country",
    "planet",
    "galaxy",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "red",
    "green",
    "blue",
    "yellow",
    "purple",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "spring",
    "summer",
    "autumn",
    "winter",
    "weather",
    "кот",
    "собака",
    "птица",
    "рыба",
    "дом",
    "город",
    "страна",
    "планета",
    "книга",
    "музыка",
]


@dataclass
class Stats:
    """Сборщик статистики запросов."""

    total: int = 0
    success: int = 0
    failed: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    error_codes: Counter = field(default_factory=Counter)
    error_bodies: Counter = field(default_factory=Counter)

    def record(self, status: int, elapsed_ms: float, body: str) -> None:
        """Записать результат одного запроса."""
        self.total += 1
        self.latencies_ms.append(elapsed_ms)
        if 200 <= status < 300:
            self.success += 1
        else:
            self.failed += 1
            self.error_codes[status] += 1
            snippet = (body or "")[:120].replace("\n", " ")
            self.error_bodies[snippet] += 1

    def report(self, duration_s: float) -> str:
        """Сформировать текстовый отчёт."""
        if not self.latencies_ms:
            return "Нет данных."

        latencies = sorted(self.latencies_ms)
        n = len(latencies)

        def pct(p: float) -> float:
            idx = min(int(p * n), n - 1)
            return latencies[idx]

        avg = sum(latencies) / n
        rps = self.total / duration_s if duration_s > 0 else 0.0
        success_pct = (self.success / self.total) * 100 if self.total else 0.0

        lines = [
            "=" * 60,
            "ОТЧЁТ НАГРУЗОЧНОГО ТЕСТА",
            "=" * 60,
            f"Всего запросов:    {self.total}",
            f"Успешных:           {self.success} ({success_pct:.1f}%)",
            f"Ошибочных:         {self.failed}",
            f"Длительность:      {duration_s:.2f} с",
            f"Средний RPS:       {rps:.2f}",
            f"Среднее время:     {avg:.1f} мс",
            f"p50:               {pct(0.50):.1f} мс",
            f"p95:               {pct(0.95):.1f} мс",
            f"p99:               {pct(0.99):.1f} мс",
            f"Мин:               {latencies[0]:.1f} мс",
            f"Макс:              {latencies[-1]:.1f} мс",
        ]

        if self.error_codes:
            lines.append("-" * 60)
            lines.append("Коды ошибок:")
            for code, count in self.error_codes.most_common():
                lines.append(f"  HTTP {code}: {count}")

        if self.error_bodies:
            lines.append("-" * 60)
            lines.append("Топ тел ошибок (до 5):")
            for body, count in self.error_bodies.most_common(5):
                lines.append(f"  [{count}x] {body}")

        lines.append("=" * 60)
        return "\n".join(lines)


def _rand_suffix(n: int = 6) -> str:
    """Сгенерировать короткий случайный суффикс."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _load_words(path: Path | None) -> list[str]:
    """Загрузить слова из файла (по одному на строку) или вернуть дефолтные."""
    if path is None:
        return DEFAULT_WORDS
    if not path.exists():
        print(f"[!] Файл со словами {path} не найден, использую дефолтный список.")
        return DEFAULT_WORDS
    with path.open("r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    return words or DEFAULT_WORDS


def _extract_token(body: str) -> str:
    """Безопасно извлечь access_token из тела JSON-ответа."""
    try:
        return json.loads(body).get("access_token", "") or ""
    except Exception:
        return ""


async def _register(
    client: httpx.AsyncClient, base_url: str, nickname: str, email: str, password: str, max_retries: int = 3
) -> httpx.Response:
    """Зарегистрировать пользователя с retry logic."""
    url = f"{base_url}/api/v1/auth/register"
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await client.post(
                url,
                json={"nickname": nickname, "email": email, "password": password},
            )
        except httpx.HTTPError as e:
            last_error = e
            logger.warning(f"Register attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(0.5 * attempt)  # exponential backoff

    raise last_error or httpx.HTTPError("All register attempts failed")


async def _login(
    client: httpx.AsyncClient, base_url: str, email: str, password: str, max_retries: int = 3
) -> httpx.Response:
    """Залогинить пользователя с retry logic."""
    url = f"{base_url}/api/v1/auth/login"
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await client.post(url, json={"email": email, "password": password})
        except httpx.HTTPError as e:
            last_error = e
            logger.warning(f"Login attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(0.5 * attempt)  # exponential backoff

    raise last_error or httpx.HTTPError("All login attempts failed")


async def _create_word(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    word: str,
    source_lang: str = "en",
    target_lang: str = "ru",
    max_retries: int = 3,
) -> httpx.Response:
    """Создать слово через /words с retry logic."""
    url = f"{base_url}/api/v1/words"
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "word_en": word,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                },
            )
        except httpx.HTTPError as e:
            last_error = e
            logger.warning(f"Create word attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(0.5 * attempt)  # exponential backoff

    raise last_error or httpx.HTTPError("All create word attempts failed")


async def _time_request(coro_factory) -> tuple[int, float, str]:
    """Выполнить запрос и вернуть (status, elapsed_ms, body)."""
    start = time.perf_counter()
    try:
        resp = await coro_factory()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return resp.status_code, elapsed_ms, resp.text
    except httpx.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return 0, elapsed_ms, f"httpx error: {e!s}"
    except Exception as e:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return 0, elapsed_ms, f"unexpected error: {e!s}"


async def _user_scenario(
    client: httpx.AsyncClient,
    base_url: str,
    user_index: int,
    password: str,
    words: list[str],
    words_min: int,
    words_max: int,
    stats: Stats,
) -> None:
    """Сценарий одного пользователя: регистрация → создание слов."""
    suffix = _rand_suffix()
    nickname = f"u{user_index}_{suffix}"
    email = f"u{user_index}_{suffix}@example.com"

    # Регистрация
    resp = await _register(client, base_url, nickname, email, password)
    status = resp.status_code
    body = resp.text
    stats.record(status, 0, body)  # elapsed будет в _time_request
    token = _extract_token(body) if status == 201 else ""

    # Если не зарегистрировались (например, юзер уже есть) — попробуем залогиниться
    if not token:
        resp = await _login(client, base_url, email, password)
        status = resp.status_code
        body = resp.text
        stats.record(status, 0, body)
        token = _extract_token(body) if status == 200 else ""

    if not token:
        return

    # Создание слов
    words_to_add = random.randint(words_min, words_max)
    for _ in range(words_to_add):
        word = random.choice(words)
        status, elapsed, body = await _time_request(
            lambda w=word: _create_word(client, base_url, token, w)
        )
        stats.record(status, elapsed, body)


async def _run(
    base_url: str,
    users: int,
    words_min: int,
    words_max: int,
    concurrency: int,
    password: str,
    words: list[str],
) -> Stats:
    """Запустить нагрузочный сценарий."""
    stats = Stats()
    sem = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(
        max_connections=concurrency * 2, max_keepalive_connections=concurrency
    )

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:

        async def one_user(idx: int) -> None:
            async with sem:
                await _user_scenario(
                    client=client,
                    base_url=base_url,
                    user_index=idx,
                    password=password,
                    words=words,
                    words_min=words_min,
                    words_max=words_max,
                    stats=stats,
                )

        start = time.perf_counter()
        await asyncio.gather(*(one_user(i) for i in range(users)))
        duration = time.perf_counter() - start

    print(stats.report(duration))
    return stats


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Нагрузочный тест API Aliaz")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Базовый URL API (по умолчанию http://localhost:8000)",
    )
    parser.add_argument(
        "--users", type=int, default=1000, help="Сколько пользователей зарегистрировать"
    )
    parser.add_argument(
        "--words-min", type=int, default=1, help="Минимум слов на пользователя"
    )
    parser.add_argument(
        "--words-max", type=int, default=5, help="Максимум слов на пользователя"
    )
    parser.add_argument(
        "--concurrency", type=int, default=50, help="Максимум одновременных запросов"
    )
    parser.add_argument(
        "--password",
        default="Password123!",
        help="Пароль для всех регистрируемых пользователей",
    )
    parser.add_argument(
        "--words-file",
        type=Path,
        default=None,
        help="Путь к файлу со словами (по одному на строку). По умолчанию встроенный список.",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Сид для генератора случайных чисел"
    )
    return parser.parse_args(list(argv))


def main(argv: list[str] | None = None) -> int:
    """Точка входа."""
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.seed is not None:
        random.seed(args.seed)

    words = _load_words(args.words_file)

    print(
        f"Запуск нагрузочного теста: users={args.users}, "
        f"words=[{args.words_min}..{args.words_max}], "
        f"concurrency={args.concurrency}, base_url={args.base_url}"
    )

    try:
        asyncio.run(
            _run(
                base_url=args.base_url,
                users=args.users,
                words_min=args.words_min,
                words_max=args.words_max,
                concurrency=args.concurrency,
                password=args.password,
                words=words,
            )
        )
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Общая обвязка для CLI-входов: превращает известные ошибки в понятные
сообщения и корректный код возврата вместо трейсбэка."""

from __future__ import annotations

import sys
from typing import Callable

import requests

from infrastructure.omsu_api import OmsuApiError
from infrastructure.omsu_directory import AmbiguousEntityError, EntityNotFoundError


def run_cli(entrypoint: Callable[[], None]) -> None:
    try:
        entrypoint()
    except (EntityNotFoundError, AmbiguousEntityError, OmsuApiError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print(f"Не найден файл: {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"Сеть недоступна или eservice.omsu.ru не отвечает: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПрервано.", file=sys.stderr)
        sys.exit(130)

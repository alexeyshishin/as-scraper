"""Порты (интерфейсы) слоя приложения.

Слой application зависит только от этих Protocol'ов, а не от конкретных
классов infrastructure — так стрелка зависимостей смотрит внутрь, к ядру.
Конкретные адаптеры в infrastructure/ удовлетворяют портам структурно
(duck typing), наследование не требуется. Проверяется mypy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from domain.models import (
    CalendarEvent,
    ChangeEvent,
    Lesson,
    ScheduleSnapshotEntry,
)


class SchedulePort(Protocol):
    """Источник расписания сущности (группа/преподаватель/аудитория)."""

    def fetch_lessons(self) -> list[Lesson]: ...


class DirectoryPort(Protocol):
    """Справочник: соответствие id аудитории → корпус."""

    def get_building_map(self) -> dict[int, str]: ...


class CalendarPort(Protocol):
    """Идемпотентная синхронизация событий во внешний календарь."""

    def sync(self, events: list[CalendarEvent]) -> dict[str, int]: ...


class SnapshotStorePort(Protocol):
    """Хранилище снепшота расписания и журнала изменений."""

    def load_snapshot(self) -> tuple[dict[str, ScheduleSnapshotEntry], datetime | None]: ...

    def save_snapshot(self, entries: dict[str, ScheduleSnapshotEntry], captured_at: datetime) -> None: ...

    def append_change_events(self, events: list[ChangeEvent]) -> None: ...

    def load_change_log(self) -> list[ChangeEvent]: ...

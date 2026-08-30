from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

ScheduleType = Literal["group", "tutor", "auditory"]

SCHEDULE_TYPES: tuple[ScheduleType, ...] = ("group", "tutor", "auditory")

SCHEDULE_TYPE_LABELS: dict[ScheduleType, str] = {
    "group": "группа",
    "tutor": "преподаватель",
    "auditory": "аудитория",
}


@dataclass(frozen=True)
class DirectoryEntry:
    id: int
    name: str
    building: str | None = None


@dataclass(frozen=True)
class Lesson:
    external_id: int
    date: date
    time_slot: int
    discipline: str
    type_work: str
    teacher: str
    teacher_id: int | None
    group: str
    group_id: int | None
    room: str
    auditory_id: int | None
    subgroup: str | None


@dataclass(frozen=True)
class CalendarEvent:
    sync_key: str
    summary: str
    location: str
    description: str
    start: datetime
    end: datetime
    reminders_minutes: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class ScheduleSnapshotEntry:
    date: date
    time_slot: int
    discipline: str
    group: str
    subgroup: str | None
    teacher: str
    room: str


ChangeKind = Literal["cancelled", "moved"]


@dataclass(frozen=True)
class ChangeEvent:
    kind: ChangeKind
    detected_at: datetime
    date: date
    time_slot: int
    discipline: str
    details: str

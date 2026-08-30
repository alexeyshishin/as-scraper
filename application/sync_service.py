from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from application.ports import CalendarPort, SchedulePort
from domain.event_factory import build_event
from domain.models import ScheduleType
from domain.resolver import resolve_day_slots, summarize_ambiguous


@dataclass
class SyncResult:
    stats: dict[str, int] | None
    ambiguous: list[tuple[str, list[str]]]
    total_events: int


class ScheduleSyncService:
    def __init__(
        self,
        omsu_client: SchedulePort,
        calendar_gateway: CalendarPort,
        schedule_type: ScheduleType,
        subgroup: str,
        teacher_overrides: dict[str, str],
        sync_from_today: bool,
        timezone: str,
        reminders_minutes: list[int] | None = None,
    ):
        self._omsu_client = omsu_client
        self._calendar_gateway = calendar_gateway
        self._schedule_type = schedule_type
        self._subgroup = subgroup
        self._teacher_overrides = teacher_overrides
        self._sync_from_today = sync_from_today
        self._timezone = timezone
        self._reminders_minutes = reminders_minutes or []

    def run(self, dry_run: bool = False) -> SyncResult:
        lessons = self._omsu_client.fetch_lessons()

        if self._sync_from_today:
            today = date.today()
            lessons = [lesson for lesson in lessons if lesson.date >= today]

        resolved, ambiguous = resolve_day_slots(
            lessons, self._schedule_type, self._subgroup, self._teacher_overrides
        )
        events = [
            build_event(lesson, self._reminders_minutes, self._timezone) for lesson in resolved
        ]

        stats = None
        if not dry_run:
            stats = self._calendar_gateway.sync(events)

        return SyncResult(
            stats=stats,
            ambiguous=summarize_ambiguous(ambiguous),
            total_events=len(events),
        )

from __future__ import annotations

import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

from domain.bell_schedule import slot_to_times
from domain.models import CalendarEvent, Lesson

TZ_NAME = "Asia/Omsk"


def make_sync_key(lesson: Lesson) -> str:
    raw = "|".join(
        [
            lesson.date.isoformat(),
            str(lesson.time_slot),
            lesson.discipline,
            lesson.group or "",
            lesson.subgroup or "",
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def build_event(
    lesson: Lesson,
    reminders_minutes: list[int] | None = None,
    timezone: str = TZ_NAME,
) -> CalendarEvent:
    start_t, end_t = slot_to_times(lesson.time_slot)
    tz = ZoneInfo(timezone)
    start_dt = datetime.combine(lesson.date, start_t, tzinfo=tz)
    end_dt = datetime.combine(lesson.date, end_t, tzinfo=tz)

    summary = f"{lesson.discipline} ({lesson.type_work})" if lesson.type_work else lesson.discipline

    desc_lines = [f"Преподаватель: {lesson.teacher or '—'}"]
    if lesson.subgroup:
        desc_lines.append(f"Подгруппа: {lesson.subgroup}")
    desc_lines.append(f"Группа: {lesson.group}")
    desc_lines.append(f"Источник: eservice.omsu.ru (lesson id {lesson.external_id})")

    return CalendarEvent(
        sync_key=make_sync_key(lesson),
        summary=summary,
        location=lesson.room,
        description="\n".join(desc_lines),
        start=start_dt,
        end=end_dt,
        reminders_minutes=list(reminders_minutes or []),
    )

from __future__ import annotations

from datetime import date, datetime, timedelta

from domain.models import ChangeEvent, Lesson, ScheduleSnapshotEntry


def snapshot_key(entry: ScheduleSnapshotEntry) -> str:
    return "|".join(
        [
            entry.date.isoformat(),
            str(entry.time_slot),
            entry.discipline,
            entry.group,
            entry.subgroup or "",
        ]
    )


def lesson_to_snapshot_entry(lesson: Lesson) -> ScheduleSnapshotEntry:
    return ScheduleSnapshotEntry(
        date=lesson.date,
        time_slot=lesson.time_slot,
        discipline=lesson.discipline,
        group=lesson.group,
        subgroup=lesson.subgroup,
        teacher=lesson.teacher,
        room=lesson.room,
    )


def build_snapshot(lessons: list[Lesson], today: date, horizon_days: int) -> dict[str, ScheduleSnapshotEntry]:
    cutoff = today + timedelta(days=horizon_days)
    snapshot: dict[str, ScheduleSnapshotEntry] = {}
    for lesson in lessons:
        if today <= lesson.date <= cutoff:
            entry = lesson_to_snapshot_entry(lesson)
            snapshot[snapshot_key(entry)] = entry
    return snapshot


def diff_snapshots(
    previous: dict[str, ScheduleSnapshotEntry],
    current: dict[str, ScheduleSnapshotEntry],
    today: date,
    detected_at: datetime,
) -> list[ChangeEvent]:
    events: list[ChangeEvent] = []

    for key, prev_entry in previous.items():
        if prev_entry.date < today:
            continue

        cur_entry = current.get(key)
        if cur_entry is None:
            events.append(
                ChangeEvent(
                    kind="cancelled",
                    detected_at=detected_at,
                    date=prev_entry.date,
                    time_slot=prev_entry.time_slot,
                    discipline=prev_entry.discipline,
                    details=(
                        f"пропала из расписания (была {prev_entry.date.strftime('%d.%m.%Y')}, "
                        f"{prev_entry.teacher or '—'}, ауд. {prev_entry.room or '—'})"
                    ),
                )
            )
            continue

        diffs = []
        if cur_entry.teacher != prev_entry.teacher:
            diffs.append(f"преподаватель: {prev_entry.teacher or '—'} → {cur_entry.teacher or '—'}")
        if cur_entry.room != prev_entry.room:
            diffs.append(f"аудитория: {prev_entry.room or '—'} → {cur_entry.room or '—'}")
        if diffs:
            events.append(
                ChangeEvent(
                    kind="moved",
                    detected_at=detected_at,
                    date=prev_entry.date,
                    time_slot=prev_entry.time_slot,
                    discipline=prev_entry.discipline,
                    details="; ".join(diffs),
                )
            )

    return events

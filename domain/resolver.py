from __future__ import annotations

from collections import defaultdict

from domain.models import Lesson, ScheduleType


def matches_subgroup(lesson: Lesson, subgroup: str) -> bool:
    if not lesson.subgroup:
        return True
    if not subgroup:
        return False
    return lesson.subgroup.strip().endswith(f"/{subgroup}")


def resolve_day_slots(
    lessons: list[Lesson],
    schedule_type: ScheduleType,
    subgroup: str,
    teacher_overrides: dict[str, str],
) -> tuple[list[Lesson], list[list[Lesson]]]:
    if schedule_type != "group":
        return lessons, []

    buckets: dict[tuple, list[Lesson]] = defaultdict(list)
    for lesson in lessons:
        buckets[(lesson.date, lesson.time_slot)].append(lesson)

    resolved: list[Lesson] = []
    ambiguous: list[list[Lesson]] = []

    for entries in buckets.values():
        if len(entries) == 1:
            resolved.append(entries[0])
            continue

        by_subgroup = [e for e in entries if matches_subgroup(e, subgroup)]
        if by_subgroup and len(by_subgroup) < len(entries):
            entries = by_subgroup
        if len(entries) == 1:
            resolved.append(entries[0])
            continue

        base = entries[0].discipline
        override = teacher_overrides.get(base)
        if override:
            by_teacher = [e for e in entries if override.lower() in e.teacher.lower()]
            if len(by_teacher) == 1:
                resolved.append(by_teacher[0])
                continue
            if by_teacher:
                entries = by_teacher

        ambiguous.append(entries)

    return resolved, ambiguous


def summarize_ambiguous(ambiguous: list[list[Lesson]]) -> list[tuple[str, list[str]]]:
    seen: dict[str, set[str]] = defaultdict(set)
    for group in ambiguous:
        base = group[0].discipline
        for e in group:
            seen[base].add(e.teacher or "—")
    return [(base, sorted(teachers)) for base, teachers in sorted(seen.items())]

from __future__ import annotations

from datetime import date

from domain.models import Lesson


def make_lesson(
    *,
    external_id: int = 1,
    day: date = date(2025, 9, 1),
    time_slot: int = 1,
    discipline: str = "Матанализ",
    type_work: str = "Лек",
    teacher: str = "Иванов И.И.",
    teacher_id: int | None = 100,
    group: str = "МИБ-401-О-02",
    group_id: int | None = 10,
    room: str = "2-корпус-305",
    auditory_id: int | None = 500,
    subgroup: str | None = None,
) -> Lesson:
    return Lesson(
        external_id=external_id,
        date=day,
        time_slot=time_slot,
        discipline=discipline,
        type_work=type_work,
        teacher=teacher,
        teacher_id=teacher_id,
        group=group,
        group_id=group_id,
        room=room,
        auditory_id=auditory_id,
        subgroup=subgroup,
    )

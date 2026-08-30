from __future__ import annotations

from datetime import date

from domain.models import Lesson


def detect_current_period(lessons: list[Lesson], today: date, gap_days: int = 21) -> tuple[date, date]:
    """
    Найти границы "текущего семестра" по самим данным, без привязки к
    конкретному учебному календарю: расписание группируется в непрерывные
    блоки дат, разрыв между блоками — любой промежуток без пар длиннее
    gap_days (каникулы/сессия). Возвращает блок, в который попадает today,
    либо ближайший будущий блок, если сейчас каникулы.
    """
    dates = sorted({lesson.date for lesson in lessons})
    if not dates:
        return today, today

    blocks: list[tuple[date, date]] = []
    block_start = dates[0]
    prev = dates[0]
    for d in dates[1:]:
        if (d - prev).days > gap_days:
            blocks.append((block_start, prev))
            block_start = d
        prev = d
    blocks.append((block_start, prev))

    for start, end in blocks:
        if start <= today <= end:
            return start, end

    upcoming = [b for b in blocks if b[0] >= today]
    if upcoming:
        return min(upcoming, key=lambda b: b[0])

    return max(blocks, key=lambda b: b[1])

from __future__ import annotations

from datetime import date

from domain.semester import detect_current_period
from tests.conftest import make_lesson


def _lessons_on(days: list[date]):
    return [make_lesson(external_id=i, day=d) for i, d in enumerate(days)]


def test_empty_returns_today():
    today = date(2025, 9, 1)
    assert detect_current_period([], today) == (today, today)


def test_single_block_today_inside():
    days = [date(2025, 9, 1), date(2025, 9, 8), date(2025, 9, 15)]
    start, end = detect_current_period(_lessons_on(days), date(2025, 9, 8), gap_days=21)
    assert start == date(2025, 9, 1)
    assert end == date(2025, 9, 15)


def test_gap_splits_into_two_blocks_picks_current():
    # осенний блок, большой разрыв (каникулы), весенний блок
    autumn = [date(2025, 9, 1), date(2025, 9, 15), date(2025, 10, 1)]
    spring = [date(2026, 2, 1), date(2026, 2, 15)]
    lessons = _lessons_on(autumn + spring)
    start, end = detect_current_period(lessons, date(2026, 2, 10), gap_days=21)
    assert start == date(2026, 2, 1)
    assert end == date(2026, 2, 15)


def test_during_vacation_picks_next_upcoming_block():
    autumn = [date(2025, 9, 1), date(2025, 10, 1)]
    spring = [date(2026, 2, 1), date(2026, 2, 15)]
    lessons = _lessons_on(autumn + spring)
    # сегодня — в каникулах между блоками
    start, _ = detect_current_period(lessons, date(2026, 1, 10), gap_days=21)
    assert start == date(2026, 2, 1)


def test_after_all_blocks_picks_last():
    # один непрерывный блок (шаг < gap_days), сегодня — далеко в будущем
    autumn = [date(2025, 9, 1), date(2025, 9, 15), date(2025, 9, 29)]
    start, end = detect_current_period(_lessons_on(autumn), date(2027, 1, 1), gap_days=21)
    assert (start, end) == (date(2025, 9, 1), date(2025, 9, 29))

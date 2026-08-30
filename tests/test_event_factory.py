from __future__ import annotations

from datetime import date

from domain.event_factory import build_event, make_sync_key
from tests.conftest import make_lesson


def test_sync_key_stable_and_short():
    lesson = make_lesson()
    key = make_sync_key(lesson)
    assert key == make_sync_key(lesson)
    assert len(key) == 20


def test_sync_key_differs_on_slot():
    a = make_lesson(time_slot=1)
    b = make_lesson(time_slot=2)
    assert make_sync_key(a) != make_sync_key(b)


def test_build_event_times_use_configured_timezone():
    lesson = make_lesson(day=date(2025, 9, 1), time_slot=1)
    event = build_event(lesson, timezone="Europe/Moscow")
    assert event.start.tzinfo is not None
    assert getattr(event.start.tzinfo, "key", None) == "Europe/Moscow"
    assert event.start.hour == 8 and event.start.minute == 45


def test_build_event_summary_and_description():
    lesson = make_lesson(discipline="Матанализ", type_work="Лек", teacher="Иванов", subgroup="G/1")
    event = build_event(lesson, reminders_minutes=[10])
    assert event.summary == "Матанализ (Лек)"
    assert "Преподаватель: Иванов" in event.description
    assert "Подгруппа: G/1" in event.description
    assert event.reminders_minutes == [10]


def test_build_event_summary_without_type():
    lesson = make_lesson(discipline="Консультация", type_work="")
    assert build_event(lesson).summary == "Консультация"

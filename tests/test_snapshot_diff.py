from __future__ import annotations

from datetime import date, datetime

from domain.snapshot_diff import build_snapshot, diff_snapshots, snapshot_key
from tests.conftest import make_lesson


def test_build_snapshot_respects_horizon():
    today = date(2025, 9, 1)
    inside = make_lesson(external_id=1, day=date(2025, 9, 10))
    outside = make_lesson(external_id=2, day=date(2025, 12, 30))
    snap = build_snapshot([inside, outside], today, horizon_days=90)
    assert len(snap) == 1
    assert snapshot_key(next(iter(snap.values()))) in snap


def test_diff_detects_cancellation():
    today = date(2025, 9, 1)
    lesson = make_lesson(day=date(2025, 9, 10))
    prev = build_snapshot([lesson], today, 90)
    events = diff_snapshots(prev, {}, today, datetime(2025, 9, 1, 12, 0))
    assert len(events) == 1
    assert events[0].kind == "cancelled"


def test_diff_detects_move_on_teacher_and_room():
    today = date(2025, 9, 1)
    before = make_lesson(day=date(2025, 9, 10), teacher="Иванов", room="A-1")
    after = make_lesson(day=date(2025, 9, 10), teacher="Петров", room="B-2")
    prev = build_snapshot([before], today, 90)
    cur = build_snapshot([after], today, 90)
    events = diff_snapshots(prev, cur, today, datetime(2025, 9, 1, 12, 0))
    assert len(events) == 1
    assert events[0].kind == "moved"
    assert "Иванов" in events[0].details and "Петров" in events[0].details


def test_diff_ignores_unchanged():
    today = date(2025, 9, 1)
    lesson = make_lesson(day=date(2025, 9, 10))
    snap = build_snapshot([lesson], today, 90)
    assert diff_snapshots(snap, snap, today, datetime(2025, 9, 1, 12, 0)) == []


def test_diff_ignores_past_dates():
    today = date(2025, 9, 15)
    past = make_lesson(day=date(2025, 9, 1))
    # снепшот из будущего снят раньше — но в prev дата уже прошла
    prev = {snapshot_key_of(past): _entry(past)}
    events = diff_snapshots(prev, {}, today, datetime(2025, 9, 15, 12, 0))
    assert events == []


# --- helpers -------------------------------------------------------------

def snapshot_key_of(lesson):
    from domain.snapshot_diff import lesson_to_snapshot_entry

    return snapshot_key(lesson_to_snapshot_entry(lesson))


def _entry(lesson):
    from domain.snapshot_diff import lesson_to_snapshot_entry

    return lesson_to_snapshot_entry(lesson)

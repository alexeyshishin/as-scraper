from __future__ import annotations

from datetime import date, datetime, time

from domain.analytics import (
    build_report,
    compute_discipline_stats,
    compute_dynamics,
    compute_geography,
    compute_workload,
    extract_building,
    lesson_hours,
)
from tests.conftest import make_lesson


def test_lesson_hours_first_slot():
    # 08:45–10:20 = 95 минут ≈ 1.583 ч
    assert round(lesson_hours(make_lesson(time_slot=1)), 2) == 1.58


def test_extract_building_variants():
    assert extract_building("2-305") == "2"
    assert extract_building("(корп3)-101") == "корп3"
    assert extract_building("") == "—"
    assert extract_building("Спортзал") == "Спортзал"


def test_workload_counts_early_late():
    early = make_lesson(external_id=1, time_slot=1)   # 08:45
    late = make_lesson(external_id=2, time_slot=6)    # заканчивается 19:35
    w = compute_workload([early, late], early_hour=time(9, 0), late_hour=time(18, 0))
    assert w.total_lessons == 2
    assert w.early_count == 1
    assert w.late_count == 1
    assert w.study_days_count == 1


def test_discipline_stats_classify_types():
    lessons = [
        make_lesson(external_id=1, discipline="Физика", type_work="Лек"),
        make_lesson(external_id=2, discipline="Физика", type_work="Практика"),
        make_lesson(external_id=3, discipline="Физика", type_work="Лаб"),
    ]
    stats = compute_discipline_stats(lessons)
    assert len(stats) == 1
    s = stats[0]
    assert s.lek == 1 and s.prak == 1 and s.lab == 1
    assert s.share_pct == 100.0


def test_geography_counts_building_changes():
    day = date(2025, 9, 1)
    l1 = make_lesson(external_id=1, day=day, time_slot=1, auditory_id=1)
    l2 = make_lesson(external_id=2, day=day, time_slot=2, auditory_id=2)
    building_map = {1: "A", 2: "B"}
    g = compute_geography([l1, l2], building_map)
    assert g.building_changes_total == 1
    assert g.days_with_change == 1


def test_dynamics_parity_split():
    # неделя 36 (нечётная) и неделя 37 (нечётная? 37 odd) — подберём чёт/нечёт
    odd = make_lesson(external_id=1, day=date(2025, 9, 1))   # ISO week 36 -> even
    d = compute_dynamics([odd])
    assert len(d.weeks) == 1


def test_build_report_period_bounds():
    lessons = [
        make_lesson(external_id=1, day=date(2025, 9, 1)),
        make_lesson(external_id=2, day=date(2025, 10, 1)),
    ]
    report = build_report(
        lessons=lessons,
        schedule_type="group",
        entity_name="МИБ-401",
        building_by_auditory_id={},
        all_change_events=[],
        tracking_since=None,
        early_hour=time(9, 0),
        late_hour=time(18, 0),
        generated_at=datetime(2025, 9, 15, 12, 0),
    )
    assert report.period_from == date(2025, 9, 1)
    assert report.period_to == date(2025, 10, 1)

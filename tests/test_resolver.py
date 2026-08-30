from __future__ import annotations

from datetime import date

from domain.resolver import matches_subgroup, resolve_day_slots, summarize_ambiguous
from tests.conftest import make_lesson


def test_non_group_type_passes_through():
    lessons = [make_lesson(subgroup="anything")]
    resolved, ambiguous = resolve_day_slots(lessons, "tutor", "1", {})
    assert resolved == lessons
    assert ambiguous == []


def test_matches_subgroup_rules():
    lesson = make_lesson(subgroup="МИБ-401-О-02/1")
    assert matches_subgroup(lesson, "1") is True
    assert matches_subgroup(lesson, "2") is False
    # без подгруппы у пары — подходит всем
    assert matches_subgroup(make_lesson(subgroup=None), "1") is True


def test_single_entry_slot_resolved():
    lessons = [make_lesson()]
    resolved, ambiguous = resolve_day_slots(lessons, "group", "1", {})
    assert len(resolved) == 1
    assert ambiguous == []


def test_subgroup_filter_disambiguates():
    day = date(2025, 9, 1)
    lab1 = make_lesson(external_id=1, day=day, time_slot=3, discipline="Физика", type_work="Лаб", subgroup="G/1")
    lab2 = make_lesson(external_id=2, day=day, time_slot=3, discipline="Физика", type_work="Лаб", subgroup="G/2")
    resolved, ambiguous = resolve_day_slots([lab1, lab2], "group", "1", {})
    assert [r.external_id for r in resolved] == [1]
    assert ambiguous == []


def test_teacher_override_disambiguates():
    day = date(2025, 9, 1)
    a = make_lesson(external_id=1, day=day, time_slot=2, discipline="Иностранный язык", teacher="Рогова Е.", subgroup=None)
    b = make_lesson(external_id=2, day=day, time_slot=2, discipline="Иностранный язык", teacher="Вихрова Н.", subgroup=None)
    resolved, ambiguous = resolve_day_slots([a, b], "group", "1", {"Иностранный язык": "Рогова"})
    assert [r.external_id for r in resolved] == [1]
    assert ambiguous == []


def test_ambiguous_reported_when_unresolvable():
    day = date(2025, 9, 1)
    a = make_lesson(external_id=1, day=day, time_slot=2, discipline="Физкультура", teacher="Ерёмин", subgroup=None)
    b = make_lesson(external_id=2, day=day, time_slot=2, discipline="Физкультура", teacher="Урамаев", subgroup=None)
    resolved, ambiguous = resolve_day_slots([a, b], "group", "1", {})
    assert resolved == []
    assert len(ambiguous) == 1
    summary = summarize_ambiguous(ambiguous)
    assert summary[0][0] == "Физкультура"
    assert set(summary[0][1]) == {"Ерёмин", "Урамаев"}

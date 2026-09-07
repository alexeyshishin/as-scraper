from __future__ import annotations

from datetime import datetime

from domain.admission import EnrollmentRow, build_enrollment_report
from domain.admission_plan import EnrollmentCategory


def _row(
    code: str,
    name: str,
    label: str,
    places: int | None,
    enrolled: int | None,
    category: EnrollmentCategory,
    level: str = "Бакалавриат",
) -> EnrollmentRow:
    return EnrollmentRow(
        direction_code=code,
        direction_name=name,
        level=level,
        label=label,
        places=places,
        enrolled=enrolled,
        category=category,
    )


SAMPLE_ROWS = [
    _row("01.03.02", "ПМИ", "Основные места (бюджет)", 50, 49, "budget"),
    _row("01.03.02", "ПМИ", "Особая квота", 1, 1, "budget"),
    _row("01.03.02", "ПМИ", "Целевая квота (АО ЦКБА)", 3, 1, "budget"),
    _row("01.03.02", "ПМИ", "Платные места (договор)", 100, 8, "paid"),
    _row("09.03.01", "ИВТ", "Основные места (бюджет)", 20, 20, "budget"),
    _row("09.03.01", "ИВТ", "Особая квота", 2, 2, "budget"),
    _row("09.03.01", "ИВТ", "Отдельная квота", 1, 1, "budget"),
    _row("09.03.01", "ИВТ", "Целевая квота (АО ОНИИП)", 3, 1, "budget"),
    _row("09.03.01", "ИВТ", "Целевая квота (АО ЦКБА)", 3, 1, "budget"),
    _row("09.03.01", "ИВТ", "Платные места (договор)", 100, 5, "paid"),
    _row("09.03.03", "ПИ", "Основные места (бюджет)", 20, 20, "budget"),
    _row("09.03.03", "ПИ", "Особая квота", 1, 1, "budget"),
    _row("09.03.03", "ПИ", "Отдельная квота", 3, 3, "budget"),
    _row("09.03.03", "ПИ", "Целевая квота (Радиозавод им. Попова)", 3, 1, "budget"),
    _row("09.03.03", "ПИ", "Платные места (договор)", 100, 9, "paid"),
    _row("10.05.01", "КБ", "Основные места (бюджет)", 20, 20, "budget", level="Специалитет"),
    _row("10.05.01", "КБ", "Особая квота", 2, 2, "budget", level="Специалитет"),
    _row("10.05.01", "КБ", "Отдельная квота", 2, 2, "budget", level="Специалитет"),
    _row("10.05.01", "КБ", "Целевая квота (АО ОНИИП)", 2, 2, "budget", level="Специалитет"),
    _row("10.05.01", "КБ", "Платные места (договор)", 100, 11, "paid", level="Специалитет"),
]


def _report():
    return build_enrollment_report(SAMPLE_ROWS, datetime(2026, 9, 7, 12, 0), "https://distabit.omsu.ru")


def test_grand_totals_reproduce_source():
    r = _report()
    assert r.total_budget == 127
    assert r.total_paid == 33
    assert r.total_all == 160


def test_per_direction_aggregation():
    r = _report()
    by_code = {d.code: d for d in r.directions}
    assert (by_code["01.03.02"].budget_enrolled, by_code["01.03.02"].paid_enrolled, by_code["01.03.02"].total_enrolled) == (51, 8, 59)
    assert (by_code["09.03.01"].budget_enrolled, by_code["09.03.01"].paid_enrolled, by_code["09.03.01"].total_enrolled) == (25, 5, 30)
    assert (by_code["09.03.03"].budget_enrolled, by_code["09.03.03"].paid_enrolled, by_code["09.03.03"].total_enrolled) == (25, 9, 34)
    assert (by_code["10.05.01"].budget_enrolled, by_code["10.05.01"].paid_enrolled, by_code["10.05.01"].total_enrolled) == (26, 11, 37)


def test_direction_order_preserved():
    r = _report()
    assert [d.code for d in r.directions] == ["01.03.02", "09.03.01", "09.03.03", "10.05.01"]


def test_fill_rate_and_remaining():
    r = _report()
    d = next(d for d in r.directions if d.code == "01.03.02")
    assert d.budget_places == 54
    assert d.fill_rate == round(51 / 54 * 100, 1)
    assert d.remaining_budget_places == 54 - 51
    kb = next(d for d in r.directions if d.code == "10.05.01")
    assert kb.budget_places == 26
    assert kb.fill_rate == 100.0
    assert kb.remaining_budget_places == 0


def test_shares_and_ranking():
    r = _report()
    assert r.budget_share == round(127 / 160 * 100, 1)
    assert r.paid_share == round(33 / 160 * 100, 1)
    assert r.ranking_by_fill[0].code == "10.05.01"
    fills = [d.fill_rate for d in r.ranking_by_fill]
    assert fills == sorted(fills, reverse=True)


def test_none_enrolled_counts_as_zero():
    rows = [
        _row("00.00.00", "X", "Основные места (бюджет)", 10, None, "budget"),
        _row("00.00.00", "X", "Платные места (договор)", 5, None, "paid"),
    ]
    r = build_enrollment_report(rows, datetime(2026, 9, 7), "https://distabit.omsu.ru")
    d = r.directions[0]
    assert d.budget_enrolled == 0
    assert d.paid_enrolled == 0
    assert d.total_enrolled == 0
    assert d.fill_rate == 0.0


def test_none_places_gives_no_fill_rate():
    rows = [_row("00.00.00", "X", "Основные места (бюджет)", None, 5, "budget")]
    r = build_enrollment_report(rows, datetime(2026, 9, 7), "https://distabit.omsu.ru")
    d = r.directions[0]
    assert d.budget_places is None
    assert d.fill_rate is None
    assert d.remaining_budget_places is None

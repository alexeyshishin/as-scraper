from __future__ import annotations

from datetime import datetime

from domain.admission import build_enrollment_report
from presentation.enrollment_report import build_html
from tests.test_admission import SAMPLE_ROWS


def _html():
    report = build_enrollment_report(SAMPLE_ROWS, datetime(2026, 9, 7, 12, 0), "https://distabit.omsu.ru")
    return build_html(report)


def test_html_has_headers_and_totals():
    html = _html()
    assert "<!doctype html>" in html
    assert "Поступление в ОмГУ" in html
    assert "Всего поступило" in html
    assert "160" in html
    assert "127" in html
    assert "33" in html


def test_html_has_direction_tables():
    html = _html()
    assert "01.03.02" in html
    assert "10.05.01" in html
    assert "ВСЕГО поступило" in html
    assert "Бюджет, всего" in html


def test_html_is_self_contained():
    html = _html()
    assert "http" not in html.lower()
    assert "<link" not in html.lower()
    assert "src=" not in html.lower()
    assert "@import" not in html.lower()

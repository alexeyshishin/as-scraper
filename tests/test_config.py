from __future__ import annotations

from datetime import time

import pytest

from config import AdmissionConfig, AnalyticsConfig, AppConfig


def _write(tmp_path, text: str) -> str:
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_minimal_config_defaults(tmp_path):
    path = _write(tmp_path, "schedule:\n  type: group\n  query: МИБ-401\n")
    cfg = AppConfig.load(path)
    assert cfg.schedule_type == "group"
    assert cfg.query == "МИБ-401"
    assert cfg.timezone == "Asia/Omsk"
    assert cfg.sync_from_today is True
    assert isinstance(cfg.analytics, AnalyticsConfig)


def test_invalid_type_raises(tmp_path):
    path = _write(tmp_path, "schedule:\n  type: nonsense\n  query: X\n")
    with pytest.raises(ValueError):
        AppConfig.load(path)


def test_missing_query_raises(tmp_path):
    path = _write(tmp_path, "schedule:\n  type: group\n")
    with pytest.raises(ValueError):
        AppConfig.load(path)


def test_analytics_time_parsing():
    cfg = AnalyticsConfig.load({"early_hour": "08:30", "late_hour": "19:00", "semester_gap_days": 14})
    assert cfg.early_hour == time(8, 30)
    assert cfg.late_hour == time(19, 0)
    assert cfg.semester_gap_days == 14


def test_analytics_defaults_when_empty():
    cfg = AnalyticsConfig.load({})
    assert cfg.early_hour == time(9, 0)
    assert cfg.late_hour == time(18, 0)
    assert cfg.snapshot_horizon_days == 90


def test_admission_defaults():
    cfg = AdmissionConfig.load({})
    assert cfg.base_url == "https://distabit.omsu.ru"
    assert cfg.verify_tls is False
    assert cfg.timeout == 60
    assert cfg.report_path == "admission_report.html"


def test_admission_overrides():
    cfg = AdmissionConfig.load({"verify_tls": True, "timeout": 15, "report_path": "out.html"})
    assert cfg.verify_tls is True
    assert cfg.timeout == 15
    assert cfg.report_path == "out.html"


def test_app_config_has_admission(tmp_path):
    path = _write(tmp_path, "schedule:\n  type: group\n  query: МИБ-401\n")
    cfg = AppConfig.load(path)
    assert isinstance(cfg.admission, AdmissionConfig)
    assert cfg.admission.base_url == "https://distabit.omsu.ru"

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

import yaml

from domain.models import SCHEDULE_TYPES, ScheduleType


@dataclass
class AnalyticsConfig:
    early_hour: time = time(9, 0)
    late_hour: time = time(18, 0)
    snapshot_horizon_days: int = 90
    semester_gap_days: int = 21
    report_path: str = "report.html"
    snapshot_path: str = "data/schedule_snapshot.json"
    change_log_path: str = "data/change_log.jsonl"

    @staticmethod
    def load(raw: dict) -> AnalyticsConfig:
        return AnalyticsConfig(
            early_hour=_parse_time(raw.get("early_hour"), time(9, 0)),
            late_hour=_parse_time(raw.get("late_hour"), time(18, 0)),
            snapshot_horizon_days=int(raw.get("snapshot_horizon_days", 90)),
            semester_gap_days=int(raw.get("semester_gap_days", 21)),
            report_path=raw.get("report_path", "report.html"),
            snapshot_path=raw.get("snapshot_path", "data/schedule_snapshot.json"),
            change_log_path=raw.get("change_log_path", "data/change_log.jsonl"),
        )


def _parse_time(value: str | None, default: time) -> time:
    if not value:
        return default
    return time.fromisoformat(str(value))


@dataclass
class AppConfig:
    schedule_type: ScheduleType
    query: str
    subgroup: str
    teacher_overrides: dict[str, str]
    calendar_name: str | None
    timezone: str
    sync_from_today: bool
    reminders_minutes: list[int]
    credentials_file: str
    token_file: str
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)

    @staticmethod
    def load(path: str) -> AppConfig:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        schedule = raw.get("schedule") or {}
        schedule_type = schedule.get("type", "group")
        if schedule_type not in SCHEDULE_TYPES:
            raise ValueError(f"schedule.type должен быть одним из {SCHEDULE_TYPES}, получено {schedule_type!r}")
        query = schedule.get("query")
        if not query:
            raise ValueError("schedule.query обязателен (имя группы/преподавателя/аудитории или числовой id)")

        return AppConfig(
            schedule_type=schedule_type,
            query=str(query),
            subgroup=str(raw.get("subgroup") or ""),
            teacher_overrides=raw.get("teacher_overrides") or {},
            calendar_name=raw.get("calendar_name") or None,
            timezone=raw.get("timezone", "Asia/Omsk"),
            sync_from_today=bool(raw.get("sync_from_today", True)),
            reminders_minutes=raw.get("reminders_minutes") or [],
            credentials_file=raw.get("credentials_file", "credentials.json"),
            token_file=raw.get("token_file", "token.json"),
            analytics=AnalyticsConfig.load(raw.get("analytics") or {}),
        )

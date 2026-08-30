from __future__ import annotations

from datetime import datetime, time

from application.ports import DirectoryPort, SchedulePort, SnapshotStorePort
from domain.analytics import AnalyticsReport, build_report
from domain.models import ScheduleType
from domain.semester import detect_current_period
from domain.snapshot_diff import build_snapshot, diff_snapshots


class AnalyticsService:
    def __init__(
        self,
        omsu_client: SchedulePort,
        directory_client: DirectoryPort,
        snapshot_store: SnapshotStorePort,
        schedule_type: ScheduleType,
        entity_name: str,
        early_hour: time,
        late_hour: time,
        snapshot_horizon_days: int = 90,
        semester_gap_days: int = 21,
    ):
        self._omsu_client = omsu_client
        self._directory_client = directory_client
        self._snapshot_store = snapshot_store
        self._schedule_type = schedule_type
        self._entity_name = entity_name
        self._early_hour = early_hour
        self._late_hour = late_hour
        self._snapshot_horizon_days = snapshot_horizon_days
        self._semester_gap_days = semester_gap_days

    def run(self) -> AnalyticsReport:
        now = datetime.now()
        today = now.date()

        lessons = self._omsu_client.fetch_lessons()

        previous_snapshot, tracking_since = self._snapshot_store.load_snapshot()
        current_snapshot = build_snapshot(lessons, today, self._snapshot_horizon_days)
        new_events = diff_snapshots(previous_snapshot, current_snapshot, today, now)
        self._snapshot_store.append_change_events(new_events)
        self._snapshot_store.save_snapshot(current_snapshot, now)
        all_events = self._snapshot_store.load_change_log()

        building_by_auditory_id = self._directory_client.get_building_map()

        period_start, period_end = detect_current_period(lessons, today, self._semester_gap_days)
        period_lessons = [lesson for lesson in lessons if period_start <= lesson.date <= period_end]

        return build_report(
            lessons=period_lessons,
            schedule_type=self._schedule_type,
            entity_name=self._entity_name,
            building_by_auditory_id=building_by_auditory_id,
            all_change_events=all_events,
            tracking_since=tracking_since,
            early_hour=self._early_hour,
            late_hour=self._late_hour,
            generated_at=now,
        )

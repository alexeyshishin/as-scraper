#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import webbrowser

from application.analytics_service import AnalyticsService
from config import AppConfig
from infrastructure.omsu_api import OmsuScheduleClient
from infrastructure.omsu_directory import OmsuDirectoryClient
from infrastructure.snapshot_store import SnapshotStore
from presentation.cli import run_cli
from presentation.html_report import build_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("omsu_analytics")


def main() -> None:
    parser = argparse.ArgumentParser(description="Собрать HTML-отчёт по расписанию ОмГУ")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out", default=None, help="Куда сохранить report.html (по умолчанию — из config.yaml)")
    parser.add_argument("--no-open", action="store_true", help="Не открывать отчёт в браузере после сборки")
    args = parser.parse_args()

    config = AppConfig.load(args.config)

    directory = OmsuDirectoryClient()
    entity = directory.resolve(config.schedule_type, config.query)
    logger.info("Расписание: %s %r (id=%s)", config.schedule_type, entity.name, entity.id)

    omsu_client = OmsuScheduleClient(config.schedule_type, entity.id)
    snapshot_store = SnapshotStore(config.analytics.snapshot_path, config.analytics.change_log_path)

    service = AnalyticsService(
        omsu_client=omsu_client,
        directory_client=directory,
        snapshot_store=snapshot_store,
        schedule_type=config.schedule_type,
        entity_name=entity.name,
        early_hour=config.analytics.early_hour,
        late_hour=config.analytics.late_hour,
        snapshot_horizon_days=config.analytics.snapshot_horizon_days,
        semester_gap_days=config.analytics.semester_gap_days,
    )

    report = service.run()
    html = build_html(report)

    out_path = args.out or config.analytics.report_path
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(
        "Отчёт сохранён в %s (период %s — %s, %d пар)",
        out_path,
        report.period_from.isoformat(),
        report.period_to.isoformat(),
        report.workload.total_lessons,
    )

    if not args.no_open:
        opened = webbrowser.open(f"file://{os.path.abspath(out_path)}")
        if not opened:
            logger.warning("Не удалось автоматически открыть браузер, открой %s вручную", out_path)


if __name__ == "__main__":
    run_cli(main)

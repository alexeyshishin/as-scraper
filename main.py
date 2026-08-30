#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging

from application.sync_service import ScheduleSyncService
from config import AppConfig
from domain.models import SCHEDULE_TYPE_LABELS
from infrastructure.google_calendar import GoogleCalendarGateway
from infrastructure.omsu_api import OmsuScheduleClient
from infrastructure.omsu_directory import OmsuDirectoryClient
from presentation.cli import run_cli

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("omsu_sync")

DEFAULT_CALENDAR_PREFIX = "ОмГУ"


def print_ambiguous_report(ambiguous: list[tuple[str, list[str]]]) -> None:
    if not ambiguous:
        return
    print(
        "\n⚠️  Пропущены пары с несколькими вариантами преподавателя/секции — "
        "добавь teacher_overrides в config.yaml:"
    )
    for base, teachers in ambiguous:
        print(f"  - {base}:")
        for t in teachers:
            print(f"      · {t}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync OmSU schedule to Google Calendar")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = AppConfig.load(args.config)

    directory = OmsuDirectoryClient()
    entity = directory.resolve(config.schedule_type, config.query)
    label = SCHEDULE_TYPE_LABELS[config.schedule_type]
    logger.info("Расписание: %s %r (id=%s)", label, entity.name, entity.id)

    calendar_name = config.calendar_name or f"{DEFAULT_CALENDAR_PREFIX}: {entity.name}"

    omsu_client = OmsuScheduleClient(config.schedule_type, entity.id)
    calendar_gateway = GoogleCalendarGateway(
        credentials_path=config.credentials_file,
        token_path=config.token_file,
        calendar_name=calendar_name,
        timezone=config.timezone,
    )
    service = ScheduleSyncService(
        omsu_client=omsu_client,
        calendar_gateway=calendar_gateway,
        schedule_type=config.schedule_type,
        subgroup=config.subgroup,
        teacher_overrides=config.teacher_overrides,
        sync_from_today=config.sync_from_today,
        timezone=config.timezone,
        reminders_minutes=config.reminders_minutes,
    )

    result = service.run(dry_run=args.dry_run)
    print_ambiguous_report(result.ambiguous)

    if args.dry_run:
        print(f"[dry-run] Событий к синхронизации: {result.total_events}. Google Calendar не тронут.")
        return

    stats = result.stats
    assert stats is not None  # stats заполняется всегда, кроме dry-run (обработан выше)
    logger.info(
        "Готово: создано %d, обновлено %d, удалено %d, без изменений %d",
        stats["created"],
        stats["updated"],
        stats["deleted"],
        stats["unchanged"],
    )


if __name__ == "__main__":
    run_cli(main)

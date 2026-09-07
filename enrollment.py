#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
import webbrowser

from application.enrollment_service import EnrollmentService
from config import AppConfig
from infrastructure.distabit_api import DistabitEnrollmentClient
from presentation.cli import run_cli
from presentation.enrollment_report import build_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("omsu_admission")


def main() -> None:
    parser = argparse.ArgumentParser(description="Собрать HTML-отчёт по поступившим в ОмГУ")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out", default=None, help="Куда сохранить admission_report.html (по умолчанию — из config.yaml)")
    parser.add_argument("--no-open", action="store_true", help="Не открывать отчёт в браузере после сборки")
    args = parser.parse_args()

    config = AppConfig.load(args.config)

    client = DistabitEnrollmentClient(
        base_url=config.admission.base_url,
        verify_tls=config.admission.verify_tls,
        timeout=config.admission.timeout,
    )
    service = EnrollmentService(client, source_url=config.admission.base_url)

    report = service.run()
    html = build_html(report)

    out_path = args.out or config.admission.report_path
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(
        "Отчёт сохранён в %s (всего поступило %d: бюджет %d, платно %d)",
        out_path,
        report.total_all,
        report.total_budget,
        report.total_paid,
    )

    if not args.no_open:
        opened = webbrowser.open(f"file://{os.path.abspath(out_path)}")
        if not opened:
            logger.warning("Не удалось автоматически открыть браузер, открой %s вручную", out_path)


if __name__ == "__main__":
    run_cli(main)

from __future__ import annotations

from datetime import datetime

from application.ports import EnrollmentPort
from domain.admission import EnrollmentReport, build_enrollment_report


class EnrollmentService:
    def __init__(self, enrollment_client: EnrollmentPort, source_url: str):
        self._enrollment_client = enrollment_client
        self._source_url = source_url

    def run(self) -> EnrollmentReport:
        rows = self._enrollment_client.fetch_rows()
        return build_enrollment_report(rows, datetime.now(), self._source_url)

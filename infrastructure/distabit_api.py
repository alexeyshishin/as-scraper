from __future__ import annotations

import html
import logging
import re
import warnings

import requests
from urllib3.exceptions import InsecureRequestWarning

from domain.admission import EnrollmentRow
from domain.admission_plan import ADMISSION_PLAN, PlanDirection

logger = logging.getLogger("omsu_admission")

BASE_URL = "https://distabit.omsu.ru"
USER_AGENT = "omsu-schedule-scraper/1.0 (personal admission report script)"
REPORT_ID_RE = re.compile(r"reportId=([a-f0-9]{32})")

ENDPOINT_IDS: dict[tuple[str, str], tuple[int, int]] = {
    ("01.03.02", "Основные места (бюджет)"): (612, 1),
    ("01.03.02", "Особая квота"): (612, 5),
    ("01.03.02", "Целевая квота (АО ЦКБА)"): (760, 2),
    ("01.03.02", "Платные места (договор)"): (612, 3),
    ("09.03.01", "Основные места (бюджет)"): (614, 1),
    ("09.03.01", "Особая квота"): (614, 5),
    ("09.03.01", "Отдельная квота"): (614, 7),
    ("09.03.01", "Целевая квота (АО ОНИИП)"): (762, 2),
    ("09.03.01", "Целевая квота (АО ЦКБА)"): (763, 2),
    ("09.03.01", "Платные места (договор)"): (614, 3),
    ("09.03.03", "Основные места (бюджет)"): (616, 1),
    ("09.03.03", "Особая квота"): (616, 5),
    ("09.03.03", "Отдельная квота"): (616, 7),
    ("09.03.03", "Целевая квота (Радиозавод им. Попова)"): (764, 2),
    ("09.03.03", "Платные места (договор)"): (616, 3),
    ("10.05.01", "Основные места (бюджет)"): (613, 1),
    ("10.05.01", "Особая квота"): (613, 5),
    ("10.05.01", "Отдельная квота"): (613, 7),
    ("10.05.01", "Целевая квота (АО ОНИИП)"): (778, 2),
    ("10.05.01", "Платные места (договор)"): (613, 3),
}


class DistabitApiError(RuntimeError):
    pass


class DistabitEnrollmentClient:
    def __init__(
        self,
        plan: list[PlanDirection] | None = None,
        base_url: str = BASE_URL,
        verify_tls: bool = False,
        timeout: int = 60,
        endpoint_ids: dict[tuple[str, str], tuple[int, int]] | None = None,
        retries: int = 2,
    ):
        self._plan = plan if plan is not None else ADMISSION_PLAN
        self._base_url = base_url.rstrip("/")
        self._verify_tls = verify_tls
        self._timeout = timeout
        self._endpoint_ids = endpoint_ids if endpoint_ids is not None else ENDPOINT_IDS
        self._retries = max(1, retries)
        if not verify_tls:
            logger.warning(
                "TLS-проверка сертификата distabit ОТКЛЮЧЕНА (verify_tls=false) — "
                "трафик уязвим к MITM. Включите verify_tls: true в config.yaml, "
                "если сертификат сайта проходит проверку."
            )

    def fetch_rows(self) -> list[EnrollmentRow]:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        rows: list[EnrollmentRow] = []
        for direction in self._plan:
            for condition in direction.conditions:
                ids = self._endpoint_ids.get((direction.code, condition.label))
                if ids is None:
                    raise DistabitApiError(
                        f"Нет транспортных id для {direction.code} / {condition.label!r}"
                    )
                spec_id, source_id = ids
                places, enrolled, summary = self._fetch_condition(session, spec_id, source_id)
                if summary is not None and enrolled is not None and summary != enrolled:
                    logger.warning(
                        "%s / %s: счётчик «Зачислен» (%s) расходится с итоговой строкой (%s)",
                        direction.code,
                        condition.label,
                        enrolled,
                        summary,
                    )
                rows.append(
                    EnrollmentRow(
                        direction_code=direction.code,
                        direction_name=direction.name,
                        level=direction.level,
                        label=condition.label,
                        places=places,
                        enrolled=enrolled,
                        category=condition.category,
                    )
                )
        return rows

    def _fetch_condition(
        self, session: requests.Session, spec_id: int, source_id: int
    ) -> tuple[int | None, int | None, int | None]:
        report_id = self._create_report(session, spec_id, source_id)
        body = self._get_report_body(session, report_id)
        return self.parse_report_body(body)

    def _create_report(self, session: requests.Session, spec_id: int, source_id: int) -> str:
        url = f"{self._base_url}/api/freports/list/{spec_id}/{source_id}/3"
        text = self._request(session, "GET", url)
        matches = REPORT_ID_RE.findall(text)
        if not matches:
            raise DistabitApiError(f"Не удалось получить reportId для {spec_id}/{source_id}")
        if len(set(matches)) > 1:
            logger.warning("Несколько reportId для %s/%s, беру первый", spec_id, source_id)
        return matches[0]

    def _get_report_body(self, session: requests.Session, report_id: str) -> str:
        url = f"{self._base_url}/_fr/preview.getReport?reportId={report_id}&renderBody=yes"
        return self._request(
            session,
            "POST",
            url,
            data=b"",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def _request(self, session: requests.Session, method: str, url: str, **kwargs: object) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                with warnings.catch_warnings():
                    if not self._verify_tls:
                        warnings.simplefilter("ignore", InsecureRequestWarning)
                    resp = session.request(
                        method,
                        url,
                        timeout=self._timeout,
                        verify=self._verify_tls,
                        **kwargs,  # type: ignore[arg-type]
                    )
                resp.raise_for_status()
                return resp.content.decode("utf-8", "replace")
            except requests.RequestException as exc:
                last_exc = exc
                logger.warning("Запрос %s не удался (попытка %d/%d): %s", url, attempt, self._retries, exc)
        raise DistabitApiError(f"Запрос {url} не удался: {last_exc}") from last_exc

    @staticmethod
    def parse_report_body(body: str) -> tuple[int | None, int | None, int | None]:
        body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S)
        body = re.sub(r"<[^>]+>", " ", html.unescape(body))
        body = re.sub(r"\s+", " ", body)

        summ_places: int | None = None
        summ_enrolled: int | None = None
        m = re.search(r"Количество мест:\s*([0-9]+)\s*,\s*из них зачислено:\s*([0-9]+)", body)
        if m:
            summ_places, summ_enrolled = int(m.group(1)), int(m.group(2))

        target_places = sum(int(x) for x in re.findall(r"количество мест:\s*([0-9]+)", body))
        enrolled = len(re.findall(r"Зачислен(?![а-яё])", body))

        if summ_places is not None:
            places: int | None = summ_places
        else:
            places = target_places or None

        return places, enrolled, summ_enrolled

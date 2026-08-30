from __future__ import annotations

from datetime import date, datetime

import requests

from domain.models import Lesson, ScheduleType

API_URL_TEMPLATE = "https://eservice.omsu.ru/schedule/backend/schedule/{schedule_type}/{entity_id}"
USER_AGENT = "omsu-schedule-scraper/1.0 (personal calendar sync script)"


class OmsuApiError(RuntimeError):
    pass


class OmsuScheduleClient:
    def __init__(self, schedule_type: ScheduleType, entity_id: int, timeout: int = 20):
        self._schedule_type = schedule_type
        self._entity_id = entity_id
        self._timeout = timeout

    def fetch_lessons(self) -> list[Lesson]:
        url = API_URL_TEMPLATE.format(schedule_type=self._schedule_type, entity_id=self._entity_id)
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success", False):
            raise OmsuApiError(f"API вернул success=false: {payload.get('message')!r}")
        return self._parse(payload.get("data", []))

    def _parse(self, days: list[dict]) -> list[Lesson]:
        lessons: list[Lesson] = []
        for day in days:
            try:
                day_date: date = datetime.strptime(day["day"], "%d.%m.%Y").date()
            except (KeyError, ValueError):
                continue
            for raw in day.get("lessons", []):
                lesson = self._to_lesson(raw, day_date)
                if lesson is not None:
                    lessons.append(lesson)
        return lessons

    @staticmethod
    def _to_lesson(raw: dict, day_date: date) -> Lesson | None:
        time_slot = raw.get("time")
        external_id = raw.get("id")
        # Пара без номера слота или без id непредставима (её нельзя разложить
        # по звонкам/дедуплицировать) — пропускаем, а не роняем весь прогон.
        if not isinstance(time_slot, int) or not isinstance(external_id, int):
            return None
        name = (raw.get("lesson") or "").strip()
        type_work = (raw.get("type_work") or "").strip()
        discipline = name[: -len(type_work)].strip() if type_work and name.endswith(type_work) else name
        return Lesson(
            external_id=external_id,
            date=day_date,
            time_slot=time_slot,
            discipline=discipline,
            type_work=type_work,
            teacher=(raw.get("teacher") or "").strip(),
            teacher_id=raw.get("teacher_id"),
            group=raw.get("group") or "",
            group_id=raw.get("group_id"),
            room=raw.get("auditCorps") or "",
            auditory_id=raw.get("auditory_id"),
            subgroup=raw.get("subgroupName"),
        )

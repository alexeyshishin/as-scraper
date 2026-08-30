from __future__ import annotations

import requests

from domain.models import SCHEDULE_TYPES, DirectoryEntry, ScheduleType

DIRECTORY_URL_TEMPLATE = "https://eservice.omsu.ru/schedule/backend/dict/{dict_key}"
USER_AGENT = "omsu-schedule-scraper/1.0"

DICT_KEY_BY_TYPE: dict[ScheduleType, str] = {
    "group": "groups",
    "tutor": "tutors",
    "auditory": "auditories",
}


class EntityNotFoundError(RuntimeError):
    pass


class AmbiguousEntityError(RuntimeError):
    def __init__(self, query: str, candidates: list[DirectoryEntry]):
        self.candidates = candidates
        names = "; ".join(f"{c.name!r} (id={c.id})" for c in candidates[:20])
        super().__init__(f"По запросу {query!r} нашлось несколько совпадений: {names}")


class OmsuDirectoryClient:
    def __init__(self, timeout: int = 20):
        self._timeout = timeout
        self._cache: dict[ScheduleType, list[DirectoryEntry]] = {}

    def list_entities(self, schedule_type: ScheduleType) -> list[DirectoryEntry]:
        if schedule_type not in SCHEDULE_TYPES:
            raise ValueError(f"Неизвестный schedule_type: {schedule_type!r}, ожидается один из {SCHEDULE_TYPES}")

        if schedule_type in self._cache:
            return self._cache[schedule_type]

        dict_key = DICT_KEY_BY_TYPE[schedule_type]
        url = DIRECTORY_URL_TEMPLATE.format(dict_key=dict_key)
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success", False):
            raise RuntimeError(f"API вернул success=false: {payload.get('message')!r}")

        entries = [
            DirectoryEntry(id=item["id"], name=item["name"], building=item.get("building"))
            for item in payload.get("data", [])
        ]
        self._cache[schedule_type] = entries
        return entries

    def get_building_map(self) -> dict[int, str]:
        return {e.id: e.building for e in self.list_entities("auditory") if e.building}

    def resolve(self, schedule_type: ScheduleType, query: str) -> DirectoryEntry:
        query = str(query).strip()
        if query.isdigit():
            return DirectoryEntry(id=int(query), name=query)

        entries = self.list_entities(schedule_type)
        query_lower = query.lower()

        exact = [e for e in entries if e.name.lower() == query_lower]
        if len(exact) == 1:
            return exact[0]

        partial = [e for e in entries if query_lower in e.name.lower()]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            raise AmbiguousEntityError(query, partial)

        raise EntityNotFoundError(f"По запросу {query!r} ничего не найдено среди {schedule_type}")

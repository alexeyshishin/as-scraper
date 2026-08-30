from __future__ import annotations

import json
import os
from datetime import date, datetime

from domain.models import ChangeEvent, ScheduleSnapshotEntry


class SnapshotStore:
    def __init__(self, snapshot_path: str, change_log_path: str):
        self._snapshot_path = snapshot_path
        self._change_log_path = change_log_path

    def load_snapshot(self) -> tuple[dict[str, ScheduleSnapshotEntry], datetime | None]:
        if not os.path.exists(self._snapshot_path):
            return {}, None
        with open(self._snapshot_path, encoding="utf-8") as f:
            raw = json.load(f)
        entries = {
            key: ScheduleSnapshotEntry(
                date=date.fromisoformat(v["date"]),
                time_slot=v["time_slot"],
                discipline=v["discipline"],
                group=v["group"],
                subgroup=v.get("subgroup"),
                teacher=v["teacher"],
                room=v["room"],
            )
            for key, v in raw.get("entries", {}).items()
        }
        captured_at = datetime.fromisoformat(raw["captured_at"]) if raw.get("captured_at") else None
        return entries, captured_at

    def save_snapshot(self, entries: dict[str, ScheduleSnapshotEntry], captured_at: datetime) -> None:
        self._ensure_dir(self._snapshot_path)
        raw = {
            "captured_at": captured_at.isoformat(),
            "entries": {
                key: {
                    "date": e.date.isoformat(),
                    "time_slot": e.time_slot,
                    "discipline": e.discipline,
                    "group": e.group,
                    "subgroup": e.subgroup,
                    "teacher": e.teacher,
                    "room": e.room,
                }
                for key, e in entries.items()
            },
        }
        with open(self._snapshot_path, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)

    def append_change_events(self, events: list[ChangeEvent]) -> None:
        if not events:
            return
        self._ensure_dir(self._change_log_path)
        with open(self._change_log_path, "a", encoding="utf-8") as f:
            for e in events:
                f.write(
                    json.dumps(
                        {
                            "kind": e.kind,
                            "detected_at": e.detected_at.isoformat(),
                            "date": e.date.isoformat(),
                            "time_slot": e.time_slot,
                            "discipline": e.discipline,
                            "details": e.details,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    def load_change_log(self) -> list[ChangeEvent]:
        if not os.path.exists(self._change_log_path):
            return []
        events: list[ChangeEvent] = []
        with open(self._change_log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                events.append(
                    ChangeEvent(
                        kind=raw["kind"],
                        detected_at=datetime.fromisoformat(raw["detected_at"]),
                        date=date.fromisoformat(raw["date"]),
                        time_slot=raw["time_slot"],
                        discipline=raw["discipline"],
                        details=raw["details"],
                    )
                )
        return events

    @staticmethod
    def _ensure_dir(path: str) -> None:
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

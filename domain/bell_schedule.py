from datetime import time

BELL_SCHEDULE: dict[int, tuple[str, str]] = {
    1: ("08:45", "10:20"),
    2: ("10:30", "12:05"),
    3: ("12:45", "14:20"),
    4: ("14:30", "16:05"),
    5: ("16:15", "17:50"),
    6: ("18:00", "19:35"),
    7: ("19:45", "21:20"),
    8: ("21:30", "23:05"),
}


def slot_to_times(slot: int) -> tuple[time, time]:
    try:
        start_str, end_str = BELL_SCHEDULE[slot]
    except KeyError as exc:
        raise ValueError(f"Неизвестный номер пары: {slot}") from exc
    return time.fromisoformat(start_str), time.fromisoformat(end_str)

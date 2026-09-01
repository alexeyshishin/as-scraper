from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from domain.bell_schedule import slot_to_times
from domain.models import ChangeEvent, Lesson, ScheduleType

WEEKDAY_NAMES_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

# Одна пара = 2 академических часа (по регламенту ОмГУ), независимо от реальной
# длительности слота по звонку (~95 мин). Все агрегаты часов считаются в акад. часах.
ACADEMIC_HOURS_PER_LESSON = 2.0


def lesson_hours(lesson: Lesson) -> float:
    return ACADEMIC_HOURS_PER_LESSON


def extract_building(room: str) -> str:
    room = (room or "").strip()
    if not room:
        return "—"
    if room.startswith("(") and ")" in room:
        room = room[1 : room.index(")")]
    if "-" in room:
        return room.split("-", 1)[0].strip()
    return room


@dataclass
class TypeStat:
    type_work: str
    lessons: int
    hours: float


@dataclass
class WorkloadMetrics:
    by_type: list[TypeStat]
    total_lessons: int
    total_hours: float
    study_days_count: int
    weeks_count: int
    study_days_per_week_avg: float
    lessons_by_weekday: list[tuple[str, int]]
    days_by_weekday: list[tuple[str, int]]
    early_count: int
    early_threshold: str
    late_count: int
    late_threshold: str


@dataclass
class DisciplineStat:
    discipline: str
    lessons: int
    hours: float
    lek: int
    prak: int
    lab: int
    other: int
    teachers: list[str]
    share_pct: float


@dataclass
class TeacherStat:
    teacher: str
    lessons: int
    hours: float
    disciplines: list[str]
    share_pct: float


@dataclass
class GeographyMetrics:
    building_changes_total: int
    building_changes_avg_per_day: float
    days_with_change: int
    top_rooms: list[tuple[str, int, float]]
    top_buildings: list[tuple[str, int, float]]


@dataclass
class WeekLoad:
    iso_year: int
    iso_week: int
    label: str
    start_date: date
    hours: float
    parity: str


@dataclass
class DynamicsMetrics:
    weeks: list[WeekLoad]
    odd_weeks_avg_hours: float
    even_weeks_avg_hours: float


@dataclass
class ChangesMetrics:
    cancelled_total: int
    moved_total: int
    recent_events: list[ChangeEvent]
    tracking_since: datetime | None


@dataclass
class AnalyticsReport:
    generated_at: datetime
    schedule_type: ScheduleType
    entity_name: str
    period_from: date
    period_to: date
    workload: WorkloadMetrics
    disciplines: list[DisciplineStat]
    teachers: list[TeacherStat]
    geography: GeographyMetrics
    dynamics: DynamicsMetrics
    changes: ChangesMetrics


def compute_workload(lessons: list[Lesson], early_hour: time, late_hour: time) -> WorkloadMetrics:
    by_type_counter: Counter[str] = Counter()
    by_type_hours: dict[str, float] = defaultdict(float)
    lessons_by_day: dict[date, list[Lesson]] = defaultdict(list)
    early_count = 0
    late_count = 0
    total_hours = 0.0

    for lesson in lessons:
        start, end = slot_to_times(lesson.time_slot)
        hours = lesson_hours(lesson)
        total_hours += hours
        type_key = lesson.type_work or "—"
        by_type_counter[type_key] += 1
        by_type_hours[type_key] += hours
        lessons_by_day[lesson.date].append(lesson)
        if start < early_hour:
            early_count += 1
        if end >= late_hour:
            late_count += 1

    study_days = sorted(lessons_by_day.keys())
    study_days_count = len(study_days)

    weeks: dict[tuple[int, int], set[int]] = defaultdict(set)
    for d in study_days:
        iso_year, iso_week, _ = d.isocalendar()
        weeks[(iso_year, iso_week)].add(d.weekday())
    weeks_count = len(weeks)

    lessons_by_weekday_counter = Counter(lesson.date.weekday() for lesson in lessons)
    days_by_weekday_counter = Counter(d.weekday() for d in study_days)

    by_type = [
        TypeStat(type_work=t, lessons=by_type_counter[t], hours=round(by_type_hours[t], 1))
        for t in sorted(by_type_counter, key=lambda k: -by_type_counter[k])
    ]

    return WorkloadMetrics(
        by_type=by_type,
        total_lessons=len(lessons),
        total_hours=round(total_hours, 1),
        study_days_count=study_days_count,
        weeks_count=weeks_count,
        study_days_per_week_avg=round(study_days_count / weeks_count, 2) if weeks_count else 0.0,
        lessons_by_weekday=[(WEEKDAY_NAMES_RU[i], lessons_by_weekday_counter.get(i, 0)) for i in range(7)],
        days_by_weekday=[(WEEKDAY_NAMES_RU[i], days_by_weekday_counter.get(i, 0)) for i in range(7)],
        early_count=early_count,
        early_threshold=early_hour.strftime("%H:%M"),
        late_count=late_count,
        late_threshold=late_hour.strftime("%H:%M"),
    )


def compute_discipline_stats(lessons: list[Lesson]) -> list[DisciplineStat]:
    total_hours = sum(lesson_hours(lesson) for lesson in lessons) or 1.0
    agg: dict[str, dict] = {}

    for lesson in lessons:
        st = agg.setdefault(
            lesson.discipline,
            {"lessons": 0, "hours": 0.0, "lek": 0, "prak": 0, "lab": 0, "other": 0, "teachers": set()},
        )
        st["lessons"] += 1
        st["hours"] += lesson_hours(lesson)
        type_lower = (lesson.type_work or "").lower()
        if type_lower.startswith("лек"):
            st["lek"] += 1
        elif type_lower.startswith("прак") or type_lower == "ипракт":
            st["prak"] += 1
        elif type_lower.startswith("лаб"):
            st["lab"] += 1
        else:
            st["other"] += 1
        if lesson.teacher:
            st["teachers"].add(lesson.teacher)

    result = [
        DisciplineStat(
            discipline=discipline,
            lessons=v["lessons"],
            hours=round(v["hours"], 1),
            lek=v["lek"],
            prak=v["prak"],
            lab=v["lab"],
            other=v["other"],
            teachers=sorted(v["teachers"]),
            share_pct=round(v["hours"] / total_hours * 100, 1),
        )
        for discipline, v in agg.items()
    ]
    result.sort(key=lambda s: -s.hours)
    return result


def compute_teacher_stats(lessons: list[Lesson]) -> list[TeacherStat]:
    total_hours = sum(lesson_hours(lesson) for lesson in lessons) or 1.0
    agg: dict[str, dict] = {}

    for lesson in lessons:
        if not lesson.teacher:
            continue
        st = agg.setdefault(lesson.teacher, {"lessons": 0, "hours": 0.0, "disciplines": set()})
        st["lessons"] += 1
        st["hours"] += lesson_hours(lesson)
        st["disciplines"].add(lesson.discipline)

    result = [
        TeacherStat(
            teacher=teacher,
            lessons=v["lessons"],
            hours=round(v["hours"], 1),
            disciplines=sorted(v["disciplines"]),
            share_pct=round(v["hours"] / total_hours * 100, 1),
        )
        for teacher, v in agg.items()
    ]
    result.sort(key=lambda s: -s.hours)
    return result


def compute_geography(lessons: list[Lesson], building_by_auditory_id: dict[int, str]) -> GeographyMetrics:
    def building_of(lesson: Lesson) -> str:
        if lesson.auditory_id is not None and lesson.auditory_id in building_by_auditory_id:
            return building_by_auditory_id[lesson.auditory_id]
        return extract_building(lesson.room)

    room_counter: Counter[str] = Counter()
    room_hours: dict[str, float] = defaultdict(float)
    building_counter: Counter[str] = Counter()
    building_hours: dict[str, float] = defaultdict(float)
    lessons_by_day: dict[date, list[Lesson]] = defaultdict(list)

    for lesson in lessons:
        room = lesson.room or "—"
        hours = lesson_hours(lesson)
        room_counter[room] += 1
        room_hours[room] += hours
        building = building_of(lesson)
        building_counter[building] += 1
        building_hours[building] += hours
        lessons_by_day[lesson.date].append(lesson)

    building_changes_total = 0
    days_with_change = 0
    for day_lessons in lessons_by_day.values():
        ordered = sorted(day_lessons, key=lambda lsn: lsn.time_slot)
        sequence = [building_of(lesson) for lesson in ordered]
        changes = sum(1 for a, b in zip(sequence, sequence[1:]) if a != b)
        building_changes_total += changes
        if changes > 0:
            days_with_change += 1

    days_count = len(lessons_by_day) or 1
    top_rooms = sorted(
        ((room, count, round(room_hours[room], 1)) for room, count in room_counter.items()),
        key=lambda t: -t[2],
    )[:10]
    top_buildings = sorted(
        ((b, count, round(building_hours[b], 1)) for b, count in building_counter.items()),
        key=lambda t: -t[2],
    )[:10]

    return GeographyMetrics(
        building_changes_total=building_changes_total,
        building_changes_avg_per_day=round(building_changes_total / days_count, 2),
        days_with_change=days_with_change,
        top_rooms=top_rooms,
        top_buildings=top_buildings,
    )


def compute_dynamics(lessons: list[Lesson]) -> DynamicsMetrics:
    weeks_hours: dict[tuple[int, int], float] = defaultdict(float)
    weeks_start: dict[tuple[int, int], date] = {}

    for lesson in lessons:
        iso_year, iso_week, _ = lesson.date.isocalendar()
        key = (iso_year, iso_week)
        weeks_hours[key] += lesson_hours(lesson)
        weeks_start[key] = lesson.date - timedelta(days=lesson.date.weekday())

    week_loads = []
    for key in sorted(weeks_hours.keys()):
        iso_year, iso_week = key
        parity = "even" if iso_week % 2 == 0 else "odd"
        week_loads.append(
            WeekLoad(
                iso_year=iso_year,
                iso_week=iso_week,
                label=f"{iso_year}-W{iso_week:02d}",
                start_date=weeks_start[key],
                hours=round(weeks_hours[key], 1),
                parity=parity,
            )
        )

    odd_hours = [w.hours for w in week_loads if w.parity == "odd"]
    even_hours = [w.hours for w in week_loads if w.parity == "even"]

    return DynamicsMetrics(
        weeks=week_loads,
        odd_weeks_avg_hours=round(sum(odd_hours) / len(odd_hours), 1) if odd_hours else 0.0,
        even_weeks_avg_hours=round(sum(even_hours) / len(even_hours), 1) if even_hours else 0.0,
    )


def compute_changes(all_events: list[ChangeEvent], tracking_since: datetime | None) -> ChangesMetrics:
    cancelled = sum(1 for e in all_events if e.kind == "cancelled")
    moved = sum(1 for e in all_events if e.kind == "moved")
    recent = sorted(all_events, key=lambda e: e.detected_at, reverse=True)[:20]
    return ChangesMetrics(cancelled_total=cancelled, moved_total=moved, recent_events=recent, tracking_since=tracking_since)


def build_report(
    lessons: list[Lesson],
    schedule_type: ScheduleType,
    entity_name: str,
    building_by_auditory_id: dict[int, str],
    all_change_events: list[ChangeEvent],
    tracking_since: datetime | None,
    early_hour: time,
    late_hour: time,
    generated_at: datetime,
) -> AnalyticsReport:
    if lessons:
        period_from = min(lesson.date for lesson in lessons)
        period_to = max(lesson.date for lesson in lessons)
    else:
        period_from = period_to = generated_at.date()

    return AnalyticsReport(
        generated_at=generated_at,
        schedule_type=schedule_type,
        entity_name=entity_name,
        period_from=period_from,
        period_to=period_to,
        workload=compute_workload(lessons, early_hour, late_hour),
        disciplines=compute_discipline_stats(lessons),
        teachers=compute_teacher_stats(lessons),
        geography=compute_geography(lessons, building_by_auditory_id),
        dynamics=compute_dynamics(lessons),
        changes=compute_changes(all_change_events, tracking_since),
    )

from __future__ import annotations

from datetime import date

from infrastructure.omsu_api import OmsuScheduleClient


def _client() -> OmsuScheduleClient:
    return OmsuScheduleClient("group", 123)


def test_parse_extracts_lessons_and_strips_type_from_name():
    days = [
        {
            "day": "01.09.2025",
            "lessons": [
                {
                    "id": 1,
                    "time": 1,
                    "lesson": "Матанализ Лек",
                    "type_work": "Лек",
                    "teacher": " Иванов И.И. ",
                    "teacher_id": 5,
                    "group": "МИБ-401",
                    "group_id": 10,
                    "auditCorps": "2-305",
                    "auditory_id": 500,
                    "subgroupName": None,
                }
            ],
        }
    ]
    lessons = _client()._parse(days)
    assert len(lessons) == 1
    lesson = lessons[0]
    assert lesson.date == date(2025, 9, 1)
    assert lesson.discipline == "Матанализ"
    assert lesson.type_work == "Лек"
    assert lesson.teacher == "Иванов И.И."
    assert lesson.room == "2-305"


def test_parse_skips_malformed_lessons():
    days = [
        {
            "day": "01.09.2025",
            "lessons": [
                {"id": 1, "time": None, "lesson": "Без слота", "type_work": ""},
                {"id": None, "time": 2, "lesson": "Без id", "type_work": ""},
                {"id": 2, "time": 3, "lesson": "Норм", "type_work": ""},
            ],
        }
    ]
    lessons = _client()._parse(days)
    assert [lesson.external_id for lesson in lessons] == [2]


def test_parse_skips_day_with_bad_date():
    days = [{"day": "не дата", "lessons": [{"id": 1, "time": 1, "lesson": "X", "type_work": ""}]}]
    assert _client()._parse(days) == []

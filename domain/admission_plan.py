from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EnrollmentCategory = Literal["budget", "paid"]


@dataclass(frozen=True)
class PlanCondition:
    label: str
    category: EnrollmentCategory


@dataclass(frozen=True)
class PlanDirection:
    code: str
    name: str
    level: str
    conditions: list[PlanCondition]


ADMISSION_PLAN: list[PlanDirection] = [
    PlanDirection(
        code="01.03.02",
        name="Прикладная математика и информатика",
        level="Бакалавриат",
        conditions=[
            PlanCondition("Основные места (бюджет)", "budget"),
            PlanCondition("Особая квота", "budget"),
            PlanCondition("Целевая квота (АО ЦКБА)", "budget"),
            PlanCondition("Платные места (договор)", "paid"),
        ],
    ),
    PlanDirection(
        code="09.03.01",
        name="Информатика и вычислительная техника",
        level="Бакалавриат",
        conditions=[
            PlanCondition("Основные места (бюджет)", "budget"),
            PlanCondition("Особая квота", "budget"),
            PlanCondition("Отдельная квота", "budget"),
            PlanCondition("Целевая квота (АО ОНИИП)", "budget"),
            PlanCondition("Целевая квота (АО ЦКБА)", "budget"),
            PlanCondition("Платные места (договор)", "paid"),
        ],
    ),
    PlanDirection(
        code="09.03.03",
        name="Прикладная информатика",
        level="Бакалавриат",
        conditions=[
            PlanCondition("Основные места (бюджет)", "budget"),
            PlanCondition("Особая квота", "budget"),
            PlanCondition("Отдельная квота", "budget"),
            PlanCondition("Целевая квота (Радиозавод им. Попова)", "budget"),
            PlanCondition("Платные места (договор)", "paid"),
        ],
    ),
    PlanDirection(
        code="10.05.01",
        name="Компьютерная безопасность",
        level="Специалитет",
        conditions=[
            PlanCondition("Основные места (бюджет)", "budget"),
            PlanCondition("Особая квота", "budget"),
            PlanCondition("Отдельная квота", "budget"),
            PlanCondition("Целевая квота (АО ОНИИП)", "budget"),
            PlanCondition("Платные места (договор)", "paid"),
        ],
    ),
]

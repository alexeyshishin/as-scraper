from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.admission_plan import EnrollmentCategory


@dataclass(frozen=True)
class EnrollmentRow:
    direction_code: str
    direction_name: str
    level: str
    label: str
    places: int | None
    enrolled: int | None
    category: EnrollmentCategory


@dataclass
class DirectionEnrollment:
    code: str
    name: str
    level: str
    rows: list[EnrollmentRow]
    budget_enrolled: int
    paid_enrolled: int
    total_enrolled: int
    budget_places: int | None
    fill_rate: float | None
    remaining_budget_places: int | None


@dataclass
class EnrollmentReport:
    directions: list[DirectionEnrollment]
    total_budget: int
    total_paid: int
    total_all: int
    total_budget_places: int | None
    overall_fill_rate: float | None
    budget_share: float
    paid_share: float
    ranking_by_fill: list[DirectionEnrollment]
    generated_at: datetime
    source_url: str


def _z(value: int | None) -> int:
    return value or 0


def build_enrollment_report(
    rows: list[EnrollmentRow],
    generated_at: datetime,
    source_url: str,
) -> EnrollmentReport:
    order: list[str] = []
    grouped: dict[str, list[EnrollmentRow]] = {}
    for row in rows:
        if row.direction_code not in grouped:
            grouped[row.direction_code] = []
            order.append(row.direction_code)
        grouped[row.direction_code].append(row)

    directions: list[DirectionEnrollment] = []
    for code in order:
        direction_rows = grouped[code]
        first = direction_rows[0]
        budget_enrolled = sum(_z(r.enrolled) for r in direction_rows if r.category == "budget")
        paid_enrolled = sum(_z(r.enrolled) for r in direction_rows if r.category == "paid")

        budget_place_values = [r.places for r in direction_rows if r.category == "budget" and r.places is not None]
        budget_places = sum(budget_place_values) if budget_place_values else None

        if budget_places:
            fill_rate: float | None = round(budget_enrolled / budget_places * 100, 1)
            remaining_budget_places: int | None = budget_places - budget_enrolled
        else:
            fill_rate = None
            remaining_budget_places = None

        directions.append(
            DirectionEnrollment(
                code=code,
                name=first.direction_name,
                level=first.level,
                rows=direction_rows,
                budget_enrolled=budget_enrolled,
                paid_enrolled=paid_enrolled,
                total_enrolled=budget_enrolled + paid_enrolled,
                budget_places=budget_places,
                fill_rate=fill_rate,
                remaining_budget_places=remaining_budget_places,
            )
        )

    total_budget = sum(d.budget_enrolled for d in directions)
    total_paid = sum(d.paid_enrolled for d in directions)
    total_all = total_budget + total_paid

    place_totals = [d.budget_places for d in directions if d.budget_places is not None]
    total_budget_places = sum(place_totals) if place_totals else None
    overall_fill_rate = (
        round(total_budget / total_budget_places * 100, 1) if total_budget_places else None
    )

    budget_share = round(total_budget / total_all * 100, 1) if total_all else 0.0
    paid_share = round(total_paid / total_all * 100, 1) if total_all else 0.0

    ranking_by_fill = sorted(
        (d for d in directions if d.fill_rate is not None),
        key=lambda d: d.fill_rate or 0.0,
        reverse=True,
    )

    return EnrollmentReport(
        directions=directions,
        total_budget=total_budget,
        total_paid=total_paid,
        total_all=total_all,
        total_budget_places=total_budget_places,
        overall_fill_rate=overall_fill_rate,
        budget_share=budget_share,
        paid_share=paid_share,
        ranking_by_fill=ranking_by_fill,
        generated_at=generated_at,
        source_url=source_url,
    )

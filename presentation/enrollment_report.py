from __future__ import annotations

from domain.admission import DirectionEnrollment, EnrollmentReport
from presentation.html_report import CSS, esc, render_rank_list, render_stat_tile


def _num(value: int | None) -> str:
    return "—" if value is None else str(value)


def render_direction_table(direction: DirectionEnrollment) -> str:
    rows = "".join(
        f"""
        <tr>
          <td>{esc(row.label)}</td>
          <td class="num">{_num(row.enrolled)}</td>
          <td class="num">{_num(row.places)}</td>
        </tr>"""
        for row in direction.rows
    )
    fill_note = (
        f" · заполнено {direction.fill_rate}%" if direction.fill_rate is not None else ""
    )
    return f"""
    <div class="card">
      <h2>{esc(direction.name)} — {esc(direction.code)}</h2>
      <p class="card-note">{esc(direction.level)} · бюджет {direction.budget_enrolled} · платно {direction.paid_enrolled}{fill_note}</p>
      <div class="table-wrap">
      <table>
        <thead><tr><th>Условие обучения</th><th>Зачислено</th><th>Мест</th></tr></thead>
        <tbody>{rows}
        <tr><td><strong>Бюджет, всего</strong></td><td class="num"><strong>{direction.budget_enrolled}</strong></td><td class="num">{_num(direction.budget_places)}</td></tr>
        <tr><td><strong>ВСЕГО поступило</strong></td><td class="num"><strong>{direction.total_enrolled}</strong></td><td class="num"></td></tr>
        </tbody>
      </table>
      </div>
    </div>"""


def build_html(report: EnrollmentReport) -> str:
    source_host = report.source_url.split("://")[-1].strip("/")
    generated_str = report.generated_at.strftime("%d.%m.%Y %H:%M")

    fill_note = f"{report.overall_fill_rate}%" if report.overall_fill_rate is not None else "—"

    directions_sorted = sorted(report.directions, key=lambda d: d.total_enrolled, reverse=True)
    by_direction_bars = render_rank_list(
        [(f"{d.name} ({d.code})", float(d.total_enrolled), f"{d.level}") for d in directions_sorted],
        unit="чел.",
    )
    budget_paid_bars = render_rank_list(
        [
            ("Бюджет", float(report.total_budget), f"{report.budget_share}%"),
            ("Платно", float(report.total_paid), f"{report.paid_share}%"),
        ],
        unit="чел.",
    )
    fill_bars = render_rank_list(
        [
            (f"{d.name} ({d.code})", d.fill_rate or 0.0, f"{d.budget_enrolled}/{_num(d.budget_places)}")
            for d in report.ranking_by_fill
        ],
        unit="%",
    )

    detail_cards = "".join(render_direction_table(d) for d in report.directions)

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Поступление в ОмГУ — IT-направления</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>Поступление в ОмГУ — IT-направления</h1>
    <div class="subtitle">очная форма · бакалавриат и специалитет · сформировано {generated_str} · данные {esc(source_host)}</div>
  </header>

  <div class="tiles">
    {render_stat_tile("Всего поступило", str(report.total_all))}
    {render_stat_tile("Бюджет", str(report.total_budget), f"{report.budget_share}% от всех")}
    {render_stat_tile("Платно", str(report.total_paid), f"{report.paid_share}% от всех")}
    {render_stat_tile("Заполнение бюджета", fill_note, "зачислено / объявлено мест")}
    {render_stat_tile("Направлений", str(len(report.directions)))}
  </div>

  <div class="section-grid">
    <div class="card">
      <h2>Поступило по направлениям</h2>
      <p class="card-note">Число фактически зачисленных (статус «Зачислен»), бюджет + платно</p>
      {by_direction_bars}
    </div>
    <div class="card">
      <h2>Бюджет и платное</h2>
      <p class="card-note">Соотношение зачисленных на бюджет и на договор</p>
      {budget_paid_bars}
    </div>
  </div>

  <div class="card">
    <h2>Заполняемость бюджетных мест</h2>
    <p class="card-note">
      Процент заполнения бюджетных мест (зачислено / объявлено). По целевым квотам
      объявленных мест обычно больше, чем фактически прошедших — отсюда неполное заполнение.
    </p>
    {fill_bars}
  </div>

  {detail_cards}

  <footer>omsu-schedule-scraper · модуль поступления · данные {esc(source_host)}</footer>
</div>
</body>
</html>
"""

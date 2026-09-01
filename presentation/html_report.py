from __future__ import annotations

import html

from domain.analytics import AnalyticsReport, DisciplineStat, TeacherStat, TypeStat, WeekLoad
from domain.models import SCHEDULE_TYPE_LABELS, ChangeEvent

FIXED_TYPE_SLOTS = {
    "Лек": "--series-1",
    "Прак": "--series-2",
    "Лаб": "--series-3",
    "ИПракт": "--series-4",
    "ПРК_Р": "--series-5",
}
FALLBACK_SLOTS = ["--series-6", "--series-7", "--series-8"]


def esc(value: object) -> str:
    return html.escape(str(value))


def assign_type_colors(by_type: list[TypeStat]) -> dict[str, str]:
    colors: dict[str, str] = {}
    fallback_idx = 0
    for t in by_type:
        if t.type_work in FIXED_TYPE_SLOTS:
            colors[t.type_work] = FIXED_TYPE_SLOTS[t.type_work]
        else:
            colors[t.type_work] = FALLBACK_SLOTS[fallback_idx % len(FALLBACK_SLOTS)]
            fallback_idx += 1
    return colors


def render_stat_tile(label: str, value: str, note: str = "") -> str:
    note_html = f'<div class="tile-note">{esc(note)}</div>' if note else ""
    return f"""
    <div class="tile">
      <div class="tile-label">{esc(label)}</div>
      <div class="tile-value">{esc(value)}</div>
      {note_html}
    </div>"""


def render_type_chart(by_type: list[TypeStat]) -> str:
    if not by_type:
        return '<p class="muted">Нет данных.</p>'
    colors = assign_type_colors(by_type)
    max_hours = max(t.hours for t in by_type) or 1.0

    legend = "".join(
        f'<span class="legend-item"><span class="swatch" style="background:var({colors[t.type_work]})"></span>{esc(t.type_work)}</span>'
        for t in by_type
    )
    rows = "".join(
        f"""
        <div class="bar-row">
          <div class="bar-label">{esc(t.type_work)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{t.hours / max_hours * 100:.1f}%; background: var({colors[t.type_work]})" title="{esc(t.type_work)}: {t.hours} акад. ч., {t.lessons} пар"></div></div>
          <div class="bar-value">{t.hours} акад. ч. · {t.lessons} пар</div>
        </div>"""
        for t in by_type
    )
    return f'<div class="legend">{legend}</div><div class="bar-chart">{rows}</div>'


def render_rank_list(items: list[tuple[str, float, str]], unit: str = "акад. ч.") -> str:
    if not items:
        return '<p class="muted">Нет данных.</p>'
    max_v = max(v for _, v, _ in items) or 1.0
    rows = "".join(
        f"""
        <div class="bar-row">
          <div class="bar-label" title="{esc(label)}">{esc(label)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{v / max_v * 100:.1f}%; background: var(--series-1)" title="{esc(label)}: {v} {unit}{(' · ' + esc(extra)) if extra else ''}"></div></div>
          <div class="bar-value">{v} {unit}</div>
        </div>"""
        for label, v, extra in items
    )
    return f'<div class="bar-chart">{rows}</div>'


def render_weekday_chart(items: list[tuple[str, int]]) -> str:
    max_v = max((v for _, v in items), default=0) or 1
    rows = "".join(
        f"""
        <div class="bar-row">
          <div class="bar-label">{esc(day)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:{v / max_v * 100:.1f}%; background: var(--series-1)" title="{esc(day)}: {v}"></div></div>
          <div class="bar-value">{v}</div>
        </div>"""
        for day, v in items
    )
    return f'<div class="bar-chart">{rows}</div>'


def render_week_timeline(weeks: list[WeekLoad]) -> str:
    if not weeks:
        return '<p class="muted">Нет данных.</p>'
    max_v = max(w.hours for w in weeks) or 1.0
    show_label_every = 1 if len(weeks) <= 16 else 2

    bars = "".join(
        f"""
        <div class="week-col">
          <div class="week-bar" style="height:{max(w.hours / max_v * 100, 2):.1f}%" title="{esc(w.label)} ({w.start_date.strftime('%d.%m')}): {w.hours} акад. ч., {'нечётная' if w.parity == 'odd' else 'чётная'} неделя"></div>
          <div class="week-tick">{esc(f'W{w.iso_week}') if i % show_label_every == 0 else ''}</div>
        </div>"""
        for i, w in enumerate(weeks)
    )
    return f'<div class="week-chart">{bars}</div>'


def render_parity_comparison(odd_avg: float, even_avg: float) -> str:
    max_v = max(odd_avg, even_avg) or 1.0
    return f"""
    <div class="legend">
      <span class="legend-item"><span class="swatch" style="background:var(--series-1)"></span>Нечётные недели</span>
      <span class="legend-item"><span class="swatch" style="background:var(--series-2)"></span>Чётные недели</span>
    </div>
    <div class="bar-chart">
      <div class="bar-row">
        <div class="bar-label">Нечётные</div>
        <div class="bar-track"><div class="bar-fill" style="width:{odd_avg / max_v * 100:.1f}%; background: var(--series-1)" title="В среднем {odd_avg} акад. ч."></div></div>
        <div class="bar-value">{odd_avg} акад. ч.</div>
      </div>
      <div class="bar-row">
        <div class="bar-label">Чётные</div>
        <div class="bar-track"><div class="bar-fill" style="width:{even_avg / max_v * 100:.1f}%; background: var(--series-2)" title="В среднем {even_avg} акад. ч."></div></div>
        <div class="bar-value">{even_avg} акад. ч.</div>
      </div>
    </div>"""


def render_discipline_table(disciplines: list[DisciplineStat]) -> str:
    if not disciplines:
        return '<p class="muted">Нет данных.</p>'
    rows = "".join(
        f"""
        <tr>
          <td>{esc(d.discipline)}</td>
          <td class="num">{d.hours}</td>
          <td class="num">{d.share_pct}%</td>
          <td class="num">{d.lek}</td>
          <td class="num">{d.prak}</td>
          <td class="num">{d.lab}</td>
          <td>{esc(', '.join(d.teachers) if d.teachers else '—')}</td>
        </tr>"""
        for d in disciplines
    )
    return f"""
    <div class="table-wrap">
    <table>
      <thead><tr><th>Дисциплина</th><th>Акад. ч.</th><th>Доля</th><th>Лек</th><th>Прак</th><th>Лаб</th><th>Преподаватели</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def render_teacher_table(teachers: list[TeacherStat]) -> str:
    if not teachers:
        return '<p class="muted">Нет данных.</p>'
    rows = "".join(
        f"""
        <tr>
          <td>{esc(t.teacher)}</td>
          <td class="num">{t.hours}</td>
          <td class="num">{t.share_pct}%</td>
          <td>{esc(', '.join(t.disciplines))}</td>
        </tr>"""
        for t in teachers[:25]
    )
    return f"""
    <div class="table-wrap">
    <table>
      <thead><tr><th>Преподаватель</th><th>Акад. ч.</th><th>Доля</th><th>Дисциплины</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def render_changes_table(events: list[ChangeEvent]) -> str:
    if not events:
        return '<p class="muted">Изменений пока не зафиксировано.</p>'
    rows = []
    for e in events:
        if e.kind == "cancelled":
            chip = '<span class="chip chip-critical">✕ отменена</span>'
        else:
            chip = '<span class="chip chip-warning">↺ перенос</span>'
        rows.append(
            f"""
        <tr>
          <td>{chip}</td>
          <td>{e.date.strftime('%d.%m.%Y')}</td>
          <td>{esc(e.discipline)}</td>
          <td>{esc(e.details)}</td>
          <td class="muted">{e.detected_at.strftime('%d.%m.%Y %H:%M')}</td>
        </tr>"""
        )
    return f"""
    <div class="table-wrap">
    <table>
      <thead><tr><th>Тип</th><th>Дата пары</th><th>Дисциплина</th><th>Что изменилось</th><th>Замечено</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </div>"""


CSS = """
:root {
  color-scheme: light;
  --page:           #f9f9f7;
  --surface-1:      #fcfcfb;
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --text-muted:     #898781;
  --gridline:       #e1e0d9;
  --baseline:       #c3c2b7;
  --border:         rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --series-3: #1baf7a; --series-4: #eda100;
  --series-5: #e87ba4; --series-6: #008300; --series-7: #4a3aa7; --series-8: #e34948;
  --status-good: #0ca30c; --status-warning: #fab219; --status-serious: #ec835a; --status-critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page:           #0d0d0d;
    --surface-1:      #1a1a19;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
    --series-5: #d55181; --series-6: #008300; --series-7: #9085e9; --series-8: #e66767;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page:           #0d0d0d;
  --surface-1:      #1a1a19;
  --text-primary:   #ffffff;
  --text-secondary: #c3c2b7;
  --text-muted:     #898781;
  --gridline:       #2c2c2a;
  --baseline:       #383835;
  --border:         rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --series-3: #199e70; --series-4: #c98500;
  --series-5: #d55181; --series-6: #008300; --series-7: #9085e9; --series-8: #e66767;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 16px 64px;
  background: var(--page);
  color: var(--text-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
}
.wrap { max-width: 980px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
header h1 { font-size: 24px; margin: 0 0 4px; }
header .subtitle { color: var(--text-secondary); font-size: 14px; }
.card {
  background: var(--surface-1);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
}
.card h2 { font-size: 16px; margin: 0 0 4px; }
.card .card-note { color: var(--text-muted); font-size: 13px; margin: 0 0 16px; }
.card + .card { }
.section-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 24px; }

.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.tile { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; }
.tile-label { color: var(--text-secondary); font-size: 12px; margin-bottom: 6px; }
.tile-value { font-size: 26px; font-weight: 600; }
.tile-note { color: var(--text-muted); font-size: 12px; margin-top: 4px; }

.legend { display: flex; flex-wrap: wrap; gap: 12px 16px; margin-bottom: 14px; font-size: 13px; color: var(--text-secondary); }
.legend-item { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }

.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: grid; grid-template-columns: 220px 1fr 110px; align-items: center; gap: 10px; }
.bar-label { font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { background: var(--gridline); border-radius: 4px; height: 14px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; min-width: 2px; }
.bar-value { font-size: 13px; color: var(--text-primary); text-align: right; font-variant-numeric: tabular-nums; }

.week-chart { display: flex; align-items: flex-end; gap: 4px; height: 160px; border-bottom: 1px solid var(--baseline); padding-bottom: 2px; overflow-x: auto; }
.week-col { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; min-width: 20px; }
.week-bar { width: 16px; background: var(--series-1); border-radius: 4px 4px 0 0; }
.week-tick { font-size: 10px; color: var(--text-muted); margin-top: 4px; writing-mode: vertical-rl; text-orientation: mixed; height: 34px; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--gridline); white-space: nowrap; }
td:not(:last-child), th:not(:last-child) { white-space: nowrap; }
td:last-child, th:last-child { white-space: normal; }
th { color: var(--text-muted); font-weight: 500; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.muted { color: var(--text-muted); }

.chip { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.chip-critical { background: color-mix(in srgb, var(--status-critical) 18%, transparent); color: var(--status-critical); }
.chip-warning { background: color-mix(in srgb, var(--status-warning) 22%, transparent); color: var(--text-primary); }

footer { color: var(--text-muted); font-size: 12px; text-align: center; margin-top: 8px; }
"""


def build_html(report: AnalyticsReport) -> str:
    w = report.workload
    g = report.geography
    d = report.dynamics
    c = report.changes

    entity_label = SCHEDULE_TYPE_LABELS.get(report.schedule_type, report.schedule_type)
    period_str = f"{report.period_from.strftime('%d.%m.%Y')} — {report.period_to.strftime('%d.%m.%Y')}"
    tracking_note = (
        f"Отслеживание изменений с {c.tracking_since.strftime('%d.%m.%Y %H:%M')}"
        if c.tracking_since
        else "Первый запуск — база для отслеживания изменений заложена сейчас, отчёты по отменам/переносам появятся со следующего запуска"
    )

    top_disciplines_bars = render_rank_list(
        [(d_.discipline, d_.hours, f"{d_.lessons} пар") for d_ in report.disciplines[:12]]
    )
    top_teachers_bars = render_rank_list(
        [(t.teacher, t.hours, f"{t.lessons} пар") for t in report.teachers[:12]]
    )
    top_rooms_bars = render_rank_list([(room, hours, f"{count} пар") for room, count, hours in g.top_rooms])
    top_buildings_bars = render_rank_list(
        [(f"Корпус {b}", hours, f"{count} пар") for b, count, hours in g.top_buildings]
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Аналитика расписания — {esc(report.entity_name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>Аналитика расписания — {esc(report.entity_name)}</h1>
    <div class="subtitle">{esc(entity_label)} · период {period_str} · сформировано {report.generated_at.strftime('%d.%m.%Y %H:%M')}</div>
  </header>

  <div class="tiles">
    {render_stat_tile("Всего часов за период", f"{w.total_hours} акад. ч.")}
    {render_stat_tile("Учебных дней", f"{w.study_days_count}", f"~{w.study_days_per_week_avg} дней/нед.")}
    {render_stat_tile(f"Пар раньше {w.early_threshold}", str(w.early_count))}
    {render_stat_tile(f"Пар после {w.late_threshold}", str(w.late_count))}
    {render_stat_tile("Смен корпусов за день", f"~{g.building_changes_avg_per_day}", f"{g.days_with_change} дней со сменой")}
  </div>

  <div class="section-grid">
    <div class="card">
      <h2>Типы занятий</h2>
      <p class="card-note">Часы по видам работы (лекции/практики/лабораторные и т.д.)</p>
      {render_type_chart(w.by_type)}
    </div>
    <div class="card">
      <h2>Нагрузка по дням недели</h2>
      <p class="card-note">Число пар, приходящихся на каждый день недели за период</p>
      {render_weekday_chart(w.lessons_by_weekday)}
    </div>
  </div>

  <div class="section-grid">
    <div class="card">
      <h2>Частота предметов</h2>
      <p class="card-note">Топ дисциплин по суммарным часам</p>
      {top_disciplines_bars}
    </div>
    <div class="card">
      <h2>Нагрузка по преподавателям</h2>
      <p class="card-note">Топ преподавателей по суммарным часам</p>
      {top_teachers_bars}
    </div>
  </div>

  <div class="card">
    <h2>Дисциплины подробно</h2>
    <p class="card-note">
      Форма контроля (экзамен/зачёт) не передаётся открытым API расписания ОмГУ — вместо неё показана
      структура нагрузки по видам занятий на дисциплину, которая обычно коррелирует со сложностью сессии.
    </p>
    {render_discipline_table(report.disciplines)}
  </div>

  <div class="card">
    <h2>Преподаватели подробно</h2>
    {render_teacher_table(report.teachers)}
  </div>

  <div class="section-grid">
    <div class="card">
      <h2>Популярные аудитории</h2>
      <p class="card-note">Топ аудиторий по суммарным часам</p>
      {top_rooms_bars}
    </div>
    <div class="card">
      <h2>Загруженность корпусов</h2>
      <p class="card-note">Топ корпусов по суммарным часам</p>
      {top_buildings_bars}
    </div>
  </div>

  <div class="card">
    <h2>Нагрузка по неделям семестра</h2>
    <p class="card-note">
      ОмГУ публикует расписание конкретными датами, без деления на числитель/знаменатель — вместо этого
      сравниваются недели по фактическим часам и по чётности номера недели.
    </p>
    {render_week_timeline(d.weeks)}
    <div style="height:16px"></div>
    {render_parity_comparison(d.odd_weeks_avg_hours, d.even_weeks_avg_hours)}
  </div>

  <div class="card">
    <h2>Отмены и переносы</h2>
    <p class="card-note">{esc(tracking_note)}</p>
    <div class="tiles" style="margin-bottom:16px">
      {render_stat_tile("Отменено пар", str(c.cancelled_total))}
      {render_stat_tile("Перенесено (препод./ауд.)", str(c.moved_total))}
    </div>
    {render_changes_table(c.recent_events)}
  </div>

  <footer>omsu-schedule-scraper · данные eservice.omsu.ru</footer>
</div>
</body>
</html>
"""

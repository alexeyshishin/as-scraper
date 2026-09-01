# Build: academic-hours-stats

Plan: `swarm-report/academic-hours-stats-plan.md`. No routing table (`AGENTS.md`) or scope
executor agents present → executed directly (single-layer Python change, 3 files).

## Changed files

### domain/analytics.py
- Added `ACADEMIC_HOURS_PER_LESSON = 2.0` (named domain constant, with RU comment).
- `lesson_hours()` now returns that constant instead of computing clock duration from
  `slot_to_times`. Signature unchanged (`(lesson: Lesson) -> float`).
- **Untouched (intentional):** `compute_workload` early/late detection and `gap_hours`
  math still use real bell times via `slot_to_times`; `event_factory` / `bell_schedule`
  not modified.

### presentation/html_report.py
- Lesson-derived hour labels «ч» → «акад. ч.»: `render_type_chart` (bar-value + title),
  `render_rank_list` default `unit`, `render_parity_comparison` (both bars + titles),
  `render_week_timeline` (title), "Всего часов за период" tile.
- Discipline & teacher table headers «Часы» → «Акад. ч.».
- "Часов в окнах" (gap) tile relabeled «ч» → «астр. ч» (value + note) so astronomical
  gap hours aren't conflated with academic hours under one label. *(skeptic MED)*

### tests/test_analytics.py
- `test_lesson_hours_first_slot` → `test_lesson_hours_is_two_academic_hours`: asserts
  `lesson_hours(...) == 2.0` for slots 1 and 6.
- `test_workload_counts_early_late`: added invariant `total_hours == 2 * total_lessons`.

## Test results (real output)

```
$ venv/bin/python -m pytest
39 passed, 1 warning in 1.43s

$ venv/bin/ruff check . --exclude venv
All checks passed!

$ venv/bin/mypy
Success: no issues found in 23 source files
```

## Environment note (pre-existing, NOT caused by this change)
- The committed `venv/` had a stale shebang pointing at `.../as-parser/...` (repo was
  renamed `as-parser` → `as-scraper`), so `make test`/`make lint` failed with
  `bad interpreter`. Recreated the venv to verify.
- `make install-dev` runs `pip install -e ".[dev]"`, which fails because `pyproject.toml`
  has no `[build-system]` table (editable install needs one). Verification therefore
  installed the dev tools directly and ran pytest/ruff/mypy as the Makefile does.
  Fixing the Makefile/pyproject is out of scope for this feature — flag for the user.

## Status: PASS — all acceptance criteria met, tests + lint green.

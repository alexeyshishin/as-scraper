# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Scraper of OmSU (Omsk State University) class schedules from `eservice.omsu.ru`, with two outputs: idempotent sync into a dedicated Google Calendar, and a self-contained HTML analytics report. Works for any group, tutor, or auditory. Most user-facing strings, comments, and docs are in Russian; keep that language when editing them.

## Skills
You should use skill `/caveman` at every session. Everytime. 

## Commands

```bash
make install-dev   # venv + runtime + dev tools (pytest/ruff/mypy)
make test          # pytest (domain logic, no network)
make lint          # ruff check . --exclude venv  &&  mypy
make check         # main.py --dry-run — never touches the calendar
make sync          # main.py — real Google Calendar sync (opens browser on first auth)
make report        # analytics.py — build report.html and open it (ARGS=--no-open to skip)
```

Run a single test: `venv/bin/python -m pytest tests/test_resolver.py::test_name`. `pyproject.toml` sets `pythonpath = ["."]`, so imports resolve from the repo root without installing.

## Architecture

Clean/hexagonal layering with a **flat package layout** — the layer packages (`domain/`, `application/`, `infrastructure/`, `presentation/`) live directly in the repo root, alongside the module-level entry points (`config.py`, `main.py`, `analytics.py`).

The dependency arrow points strictly **inward**. `application/ports.py` defines `Protocol` ports (`SchedulePort`, `DirectoryPort`, `CalendarPort`, `SnapshotStorePort`). Infrastructure adapters satisfy these ports **structurally** (duck typing, no inheritance), so `application` and `domain` never import `requests` or Google libraries. This is enforced by mypy — do not add infrastructure imports to those inner layers.

- `domain/` — pure business logic, no external deps. Key pieces: `resolver.py` (picks one lesson per slot, `type: group` only), `event_factory.py` (`Lesson` → `CalendarEvent` + `sync_key`), `semester.py` (infers current-semester bounds from gaps in the data itself), `snapshot_diff.py` (two snapshots → cancellations/reschedules), `analytics.py` (load/subject/geography/dynamics metrics), `bell_schedule.py` (hardcoded slot→time from OmSU order №01-18/44; the API does not return times).
- `infrastructure/` — `omsu_api.py` and `omsu_directory.py` (undocumented public endpoints under `/schedule/backend/`), `google_calendar.py` (OAuth2 + event CRUD), `snapshot_store.py` (on-disk snapshot + change log).
- `application/` — `sync_service.py` (fetch→resolve→build→sync) and `analytics_service.py` (fetch→diff→metrics).
- `presentation/` — `html_report.py` (report generation), `cli.py` (`run_cli` wraps entry points, mapping known errors to friendly messages + exit codes).
- `main.py` / `analytics.py` are the **composition roots**: they instantiate concrete infrastructure adapters and wire them into services. New external dependencies get injected here, not reached for inside services.

Tests cover domain logic without network; `tests/conftest.py` provides a `make_lesson(...)` factory for building `Lesson` fixtures.

## Notes

- Config lives in `config.yaml` (gitignored; copy from `config.example.yaml`). Google OAuth needs `credentials.json` in the repo root; `token.json` is written after first login. All three, plus `data/` and `report.html`, are gitignored — do not commit them.
- Sync is idempotent via `sync_key`: reruns create new lessons, update changed ones (substitutions), and delete lessons that vanished from the schedule.
- The analytics "cancellations/reschedules" section compares the live schedule against `data/schedule_snapshot.json` and accrues history in `data/change_log.jsonl` — it is empty on the very first `make report` run (nothing to diff against yet).

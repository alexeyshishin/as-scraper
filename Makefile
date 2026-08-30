VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install install-dev check sync report test lint clean

help:
	@echo "make install     - создать venv и поставить зависимости"
	@echo "make install-dev - доустановить dev-инструменты (pytest/ruff/mypy)"
	@echo "make check       - проверить расписание (dry-run, календарь не трогается)"
	@echo "make sync        - синхронизировать расписание с Google Calendar"
	@echo "make report      - собрать HTML-отчёт с аналитикой расписания"
	@echo "make test        - прогнать тесты (pytest)"
	@echo "make lint        - ruff + mypy"
	@echo "make clean       - удалить venv"

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt

install: $(VENV)/bin/activate

install-dev: install
	$(PIP) install --quiet -e ".[dev]"

check: install
	$(PYTHON) main.py --dry-run

sync: install
	$(PYTHON) main.py

report: install
	$(PYTHON) analytics.py $(ARGS)

test: install-dev
	$(PYTHON) -m pytest

lint: install-dev
	$(VENV)/bin/ruff check . --exclude venv
	$(VENV)/bin/mypy

clean:
	rm -rf $(VENV)

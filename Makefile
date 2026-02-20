.PHONY: dev test lint up down venv

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
RUFF := $(VENV)/bin/ruff
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

dev: venv
	$(UVICORN) app.main:app --host 0.0.0.0 --port 8080 --reload

test: venv
	$(PYTEST) -q

lint: venv
	$(RUFF) check .
	$(RUFF) format --check .

up:
	docker compose up -d --build

down:
	docker compose down

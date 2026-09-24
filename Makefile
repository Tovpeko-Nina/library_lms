SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help setup run test quality migrate backup restore verify up down container-check

help:
	@echo "Доступные команды:"
	@echo "  make setup            первоначальная настройка"
	@echo "  make run              локальный запуск"
	@echo "  make test             автоматические тесты (будут добавлены в ЛР3)"
	@echo "  make quality          доступные статические проверки"
	@echo "  make migrate          применение текущей схемы БД"
	@echo "  make backup           резервная копия PostgreSQL"
	@echo "  make restore BACKUP_FILE=... CONFIRM_RESTORE=yes"
	@echo "  make verify           полный набор локальных проверок"
	@echo "  make up               запуск Docker Compose"
	@echo "  make down             остановка Docker Compose"
	@echo "  make container-check  проверка контейнерного окружения"

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	if [[ ! -f .env ]]; then
		cp .env.example .env
		echo "Создан .env. Замените тестовые секреты перед запуском."
	else
		echo ".env уже существует — файл оставлен без изменений."
	fi

run:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	test -x $(UVICORN) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	@echo "Автоматические тесты будут реализованы в ЛР3; цель намеренно не имитирует успешную проверку."
	@exit 2

quality:
	$(PYTHON) -m compileall -q app
	if command -v node >/dev/null 2>&1; then
		node --check static/js/main.js
	else
		echo "Предупреждение: Node.js не найден, проверка синтаксиса JavaScript пропущена."
	fi

migrate:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	$(VENV_PYTHON) -c 'from app.core.database import init_db; init_db()'
	@echo "Текущая схема применена. Версионируемые миграции Alembic появятся в ЛР3."

backup:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	command -v pg_dump >/dev/null 2>&1 || { echo "Не найден pg_dump (установите клиент PostgreSQL)"; exit 2; }
	set -a
	source .env
	set +a
	mkdir -p backups
	backup_file="backups/lms_$$(date +%Y%m%d_%H%M%S).dump"
	pg_dump --format=custom --file="$$backup_file" --dbname="$$DATABASE_URL"
	echo "Резервная копия: $$backup_file"

restore:
	test -n "$(BACKUP_FILE)" || { echo "Укажите BACKUP_FILE: make restore BACKUP_FILE=backups/file.dump CONFIRM_RESTORE=yes"; exit 2; }
	test "$(CONFIRM_RESTORE)" = "yes" || { echo "Восстановление изменит БД. Добавьте CONFIRM_RESTORE=yes"; exit 2; }
	test -f "$(BACKUP_FILE)" || { echo "Файл не найден: $(BACKUP_FILE)"; exit 2; }
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	command -v pg_restore >/dev/null 2>&1 || { echo "Не найден pg_restore (установите клиент PostgreSQL)"; exit 2; }
	set -a
	source .env
	set +a
	pg_restore --clean --if-exists --no-owner --dbname="$$DATABASE_URL" "$(BACKUP_FILE)"

verify: quality test

up:
	docker compose up --build --detach

down:
	docker compose down

container-check:
	docker compose config --quiet
	docker compose up --build --detach --wait
	curl --fail --silent --show-error http://127.0.0.1:8000/health
	@echo
	@echo "Контейнерное окружение работает. Остановить: make down"

.PHONY: help install dev test lint format migrate upgrade-db downgrade-db run docker-build docker-up docker-down docker-logs shell create-superuser

help:
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar dependencias"
	@echo "  make dev           - Servidor de desarrollo"
	@echo "  make test          - Ejecutar tests"
	@echo "  make lint          - Ejecutar linters"
	@echo "  make format        - Formatear código"
	@echo "  make migrate       - Crear migración (uso: make migrate msg='descripción')"
	@echo "  make upgrade-db    - Aplicar migraciones"
	@echo "  make downgrade-db  - Revertir migración"
	@echo "  make run           - Servidor producción"
	@echo "  make docker-build  - Construir imagen Docker"
	@echo "  make docker-up     - Iniciar servicios Docker"
	@echo "  make docker-down   - Detener servicios Docker"
	@echo "  make docker-logs   - Ver logs Docker"
	@echo "  make shell         - Shell de Python"
	@echo "  make create-superuser - Crear superusuario"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

lint:
	ruff check app/
	mypy app/

format:
	ruff format app/
	ruff check --fix app/

migrate:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Debes proporcionar un mensaje. Uso: make migrate msg='descripción'"; \
		exit 1; \
	fi
	alembic revision --autogenerate -m "$(msg)"

upgrade-db:
	alembic upgrade head

downgrade-db:
	alembic downgrade -1

run:
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

docker-build:
	docker build -t incapacidades-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-restart:
	docker-compose restart api

shell:
	python -c "from app.db.session import SessionLocal; from app.models import *; db = SessionLocal(); print('Database session available as db')"

create-superuser:
	python scripts/create_superuser.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

celery-worker:
	celery -A app.tasks.celery_app worker --loglevel=info

celery-beat:
	celery -A app.tasks.celery_app beat --loglevel=info

celery-flower:
	celery -A app.tasks.celery_app flower --port=5555

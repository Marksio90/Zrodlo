.PHONY: up down build logs ps shell-backend shell-frontend migrate pull-model health clean

up:
	cp -n .env.example .env 2>/dev/null || true
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

shell-backend:
	docker compose exec backend bash

shell-frontend:
	docker compose exec frontend sh

migrate:
	docker compose exec backend alembic upgrade head

pull-model:
	docker compose exec ollama ollama pull $(or $(MODEL),gemma2:2b)

health:
	@echo "=== Health Checks ==="
	@curl -sf http://localhost/health && echo "✓ Nginx OK" || echo "✗ Nginx FAIL"
	@curl -sf http://localhost/api/health && echo "✓ Backend OK" || echo "✗ Backend FAIL"
	@curl -sf http://localhost && echo "✓ Frontend OK" || echo "✗ Frontend FAIL"

clean:
	docker compose down -v --remove-orphans

restart:
	docker compose restart $(SERVICE)

test-backend:
	docker compose exec backend pytest -v

format-backend:
	docker compose exec backend ruff format app/
	docker compose exec backend ruff check --fix app/

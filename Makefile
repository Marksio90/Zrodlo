.PHONY: up down build logs ps shell-backend shell-frontend migrate health clean restart test-backend format-backend \
        prod-up prod-down prod-build prod-logs prod-migrate prod-health \
        ssl-init backup restore backup-check

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

# ── Produkcja ──────────────────────────────────────────────────────────────────

PROD_COMPOSE = docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml

prod-up:
	@test -f .env.prod || (echo "Brak .env.prod – skopiuj .env.prod.example i wypełnij" && exit 1)
	$(PROD_COMPOSE) up -d

prod-down:
	$(PROD_COMPOSE) down

prod-build:
	$(PROD_COMPOSE) build

prod-logs:
	$(PROD_COMPOSE) logs -f

prod-migrate:
	$(PROD_COMPOSE) exec backend alembic upgrade head

prod-health:
	@echo "=== Health Checks (prod) ==="
	@curl -sf https://${DOMAIN}/health && echo "✓ Backend OK" || echo "✗ Backend FAIL"
	@curl -sf https://${DOMAIN} && echo "✓ Frontend OK" || echo "✗ Frontend FAIL"

ssl-init:
	@test -n "$(DOMAIN)" || (echo "Użycie: make ssl-init DOMAIN=zrodlo.pl EMAIL=admin@zrodlo.pl" && exit 1)
	@test -n "$(EMAIL)"  || (echo "Użycie: make ssl-init DOMAIN=zrodlo.pl EMAIL=admin@zrodlo.pl" && exit 1)
	DOMAIN=$(DOMAIN) EMAIL=$(EMAIL) ./infra/certbot/init-ssl.sh

# ── Backup ────────────────────────────────────────────────────────────────────

backup:
	@test -f .env.prod && export $$(grep -v '^#' .env.prod | xargs) || true
	./infra/backup/backup.sh

backup-check:
	@test -f .env.prod && export $$(grep -v '^#' .env.prod | xargs) || true
	./infra/backup/check_backup.sh

restore:
	@test -n "$(DIR)" || (echo "Użycie: make restore DIR=/backup/zrodlo/daily/20250601_030000" && exit 1)
	@test -f .env.prod && export $$(grep -v '^#' .env.prod | xargs) || true
	./infra/backup/restore.sh $(DIR) $(MODE)

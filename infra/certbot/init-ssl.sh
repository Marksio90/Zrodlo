#!/usr/bin/env bash
# init-ssl.sh – pierwsza konfiguracja certyfikatu Let's Encrypt
#
# Uruchom PRZED startem pełnego stacku produkcyjnego:
#   DOMAIN=zrodlo.parafia.pl EMAIL=admin@parafia.pl ./infra/certbot/init-ssl.sh
#
# Wymagania: Docker uruchomiony, porty 80/443 dostępne z Internetu

set -euo pipefail

DOMAIN="${DOMAIN:?Ustaw zmienną DOMAIN, np. DOMAIN=zrodlo.parafia.pl}"
EMAIL="${EMAIL:?Ustaw zmienną EMAIL, np. EMAIL=admin@parafia.pl}"
STAGING="${STAGING:-0}"  # STAGING=1 dla testów (unika limitu Let's Encrypt)

CERTBOT_DIR="$(cd "$(dirname "$0")" && pwd)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Upewnij się że katalogi istnieją
mkdir -p "$CERTBOT_DIR/conf" "$CERTBOT_DIR/www"

STAGING_FLAG=""
if [[ "$STAGING" == "1" ]]; then
    STAGING_FLAG="--staging"
    log "Tryb staging (certyfikat testowy)"
fi

# Uruchom nginx tylko do obsługi ACME challenge (bez SSL)
log "Uruchamiam tymczasowy nginx na port 80..."
docker run -d --rm \
    --name certbot_nginx_tmp \
    -p 80:80 \
    -v "$CERTBOT_DIR/www:/var/www/certbot:ro" \
    nginx:1.27-alpine \
    nginx -g "daemon off; events{} http{ server{ listen 80; location /.well-known/acme-challenge/{ root /var/www/certbot; } location /{ return 200 'ok'; } } }" \
    2>/dev/null || true

sleep 2

log "Pobieranie certyfikatu dla $DOMAIN..."
docker run --rm \
    -v "$CERTBOT_DIR/conf:/etc/letsencrypt" \
    -v "$CERTBOT_DIR/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $STAGING_FLAG \
    -d "$DOMAIN"

docker stop certbot_nginx_tmp 2>/dev/null || true

log ""
log "✅ Certyfikat wygenerowany dla $DOMAIN"
log ""
log "Następny krok – uruchom produkcyjny stack:"
log "  cp .env.prod.example .env.prod"
log "  # Wypełnij .env.prod"
log "  docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d"

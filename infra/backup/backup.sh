#!/usr/bin/env bash
# backup.sh – pełny backup systemu Źródło
#
# Backupuje:
#   - PostgreSQL  → pg_dump (skompresowany gzip)
#   - Qdrant      → snapshot przez REST API
#   - MinIO       → mirror przez mc (MinIO Client)
#
# Rotacja: 7 backupów dziennych, 4 tygodniowe (uruchamiaj przez cron)
# Cron: 0 3 * * * /opt/zrodlo/infra/backup/backup.sh >> /var/log/zrodlo-backup.log 2>&1

set -euo pipefail

# ── Konfiguracja ───────────────────────────────────────────────────────────────

BACKUP_ROOT="${BACKUP_ROOT:-/backup/zrodlo}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DAY_OF_WEEK=$(date +%u)  # 1=poniedziałek, 7=niedziela
KEEP_DAILY=7
KEEP_WEEKLY=4

# PostgreSQL
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-zrodlo}"
POSTGRES_DB="${POSTGRES_DB:-zrodlo}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}"

# Qdrant
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-zrodlo_openai}"

# MinIO
MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:?MINIO_ROOT_USER not set}"
MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD not set}"
MINIO_BUCKET="${MINIO_BUCKET:-zrodlo-docs}"

# Opcjonalne powiadomienia przez Slack/webhook
NOTIFY_URL="${BACKUP_NOTIFY_URL:-}"

# ── Funkcje pomocnicze ─────────────────────────────────────────────────────────

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

die() {
    log "ERROR: $*"
    [[ -n "$NOTIFY_URL" ]] && \
        curl -sf -X POST "$NOTIFY_URL" \
            -H 'Content-type: application/json' \
            -d "{\"text\":\"🔴 Backup Źródło FAILED: $*\"}" || true
    exit 1
}

notify_ok() {
    [[ -z "$NOTIFY_URL" ]] && return 0
    curl -sf -X POST "$NOTIFY_URL" \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"✅ Backup Źródło OK: $TIMESTAMP – $*\"}" || true
}

# ── Przygotowanie katalogów ────────────────────────────────────────────────────

DAILY_DIR="$BACKUP_ROOT/daily/$TIMESTAMP"
mkdir -p "$DAILY_DIR/postgres" "$DAILY_DIR/qdrant" "$DAILY_DIR/minio"
log "Backup dir: $DAILY_DIR"

# ── 1. PostgreSQL ──────────────────────────────────────────────────────────────

log "=== PostgreSQL backup ==="
PG_FILE="$DAILY_DIR/postgres/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -Fp \
    --no-owner \
    --no-acl \
    "$POSTGRES_DB" \
    | gzip -9 > "$PG_FILE" \
    || die "pg_dump failed"

PG_SIZE=$(du -sh "$PG_FILE" | cut -f1)
log "PostgreSQL backup OK: $PG_FILE ($PG_SIZE)"

# ── 2. Qdrant snapshot ─────────────────────────────────────────────────────────

log "=== Qdrant snapshot ==="
QDRANT_DIR="$DAILY_DIR/qdrant"

# Utwórz snapshot
SNAPSHOT_RESP=$(curl -sf -X POST \
    "$QDRANT_URL/collections/$QDRANT_COLLECTION/snapshots" \
    -H 'Content-Type: application/json') \
    || die "Qdrant snapshot creation failed"

SNAPSHOT_NAME=$(echo "$SNAPSHOT_RESP" | grep -oP '"name":\s*"\K[^"]+' | head -1)
[[ -z "$SNAPSHOT_NAME" ]] && die "Could not parse Qdrant snapshot name from: $SNAPSHOT_RESP"

log "Qdrant snapshot created: $SNAPSHOT_NAME"

# Pobierz snapshot
curl -sf \
    "$QDRANT_URL/collections/$QDRANT_COLLECTION/snapshots/$SNAPSHOT_NAME" \
    -o "$QDRANT_DIR/$SNAPSHOT_NAME" \
    || die "Qdrant snapshot download failed"

QDRANT_SIZE=$(du -sh "$QDRANT_DIR/$SNAPSHOT_NAME" | cut -f1)
log "Qdrant snapshot OK: $SNAPSHOT_NAME ($QDRANT_SIZE)"

# Usuń stare snapshoty z Qdrant (zostaw 3 ostatnie)
SNAPSHOTS=$(curl -sf "$QDRANT_URL/collections/$QDRANT_COLLECTION/snapshots" \
    | grep -oP '"name":\s*"\K[^"]+' | head -n -3)
for old_snap in $SNAPSHOTS; do
    curl -sf -X DELETE "$QDRANT_URL/collections/$QDRANT_COLLECTION/snapshots/$old_snap" || true
    log "Deleted old Qdrant snapshot: $old_snap"
done

# ── 3. MinIO mirror ───────────────────────────────────────────────────────────

log "=== MinIO mirror ==="
MINIO_BACKUP_DIR="$DAILY_DIR/minio"

# Sprawdź mc
if ! command -v mc &> /dev/null; then
    log "MinIO Client (mc) not found, downloading..."
    curl -sf https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
    chmod +x /usr/local/bin/mc
fi

mc alias set zrodlo_backup \
    "$MINIO_ENDPOINT" \
    "$MINIO_ACCESS_KEY" \
    "$MINIO_SECRET_KEY" \
    --quiet

mc mirror \
    "zrodlo_backup/$MINIO_BUCKET" \
    "$MINIO_BACKUP_DIR/$MINIO_BUCKET" \
    --quiet \
    || die "MinIO mirror failed"

MINIO_SIZE=$(du -sh "$MINIO_BACKUP_DIR" | cut -f1)
log "MinIO mirror OK: $MINIO_BACKUP_DIR ($MINIO_SIZE)"

# ── 4. Tygodniowy hard-link (bez kopiowania) ──────────────────────────────────

if [[ "$DAY_OF_WEEK" -eq 7 ]]; then
    log "=== Tygodniowy backup ==="
    WEEK_NUM=$(date +%Y-W%V)
    WEEKLY_DIR="$BACKUP_ROOT/weekly/$WEEK_NUM"
    cp -al "$DAILY_DIR" "$WEEKLY_DIR"
    log "Weekly backup link: $WEEKLY_DIR"
fi

# ── 5. Rotacja ─────────────────────────────────────────────────────────────────

log "=== Rotacja backupów ==="

# Dzienny – zostaw $KEEP_DAILY
DAILY_COUNT=$(find "$BACKUP_ROOT/daily" -mindepth 1 -maxdepth 1 -type d | wc -l)
if [[ "$DAILY_COUNT" -gt "$KEEP_DAILY" ]]; then
    find "$BACKUP_ROOT/daily" -mindepth 1 -maxdepth 1 -type d \
        | sort | head -n $(( DAILY_COUNT - KEEP_DAILY )) \
        | xargs rm -rf
    log "Rotated daily: kept $KEEP_DAILY, removed $(( DAILY_COUNT - KEEP_DAILY ))"
fi

# Tygodniowy – zostaw $KEEP_WEEKLY
WEEKLY_DIR="$BACKUP_ROOT/weekly"
if [[ -d "$WEEKLY_DIR" ]]; then
    WEEKLY_COUNT=$(find "$WEEKLY_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [[ "$WEEKLY_COUNT" -gt "$KEEP_WEEKLY" ]]; then
        find "$WEEKLY_DIR" -mindepth 1 -maxdepth 1 -type d \
            | sort | head -n $(( WEEKLY_COUNT - KEEP_WEEKLY )) \
            | xargs rm -rf
        log "Rotated weekly: kept $KEEP_WEEKLY"
    fi
fi

# ── Podsumowanie ───────────────────────────────────────────────────────────────

TOTAL_SIZE=$(du -sh "$DAILY_DIR" | cut -f1)
log "=== Backup zakończony: $TIMESTAMP ($TOTAL_SIZE) ==="
notify_ok "$TOTAL_SIZE"

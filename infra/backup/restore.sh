#!/usr/bin/env bash
# restore.sh – przywracanie systemu Źródło z backupu
#
# Użycie:
#   ./restore.sh /backup/zrodlo/daily/20250601_030000
#   ./restore.sh /backup/zrodlo/daily/20250601_030000 --postgres-only
#   ./restore.sh /backup/zrodlo/daily/20250601_030000 --qdrant-only

set -euo pipefail

BACKUP_DIR="${1:?Usage: restore.sh <backup-dir> [--postgres-only|--qdrant-only|--minio-only]}"
MODE="${2:-all}"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-zrodlo}"
POSTGRES_DB="${POSTGRES_DB:-zrodlo}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD not set}"

QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"
QDRANT_COLLECTION="${QDRANT_COLLECTION:-zrodlo_openai}"

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:?MINIO_ROOT_USER not set}"
MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD not set}"
MINIO_BUCKET="${MINIO_BUCKET:-zrodlo-docs}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

[[ -d "$BACKUP_DIR" ]] || { log "ERROR: $BACKUP_DIR nie istnieje"; exit 1; }

# ── PostgreSQL ─────────────────────────────────────────────────────────────────

restore_postgres() {
    log "=== Przywracanie PostgreSQL ==="
    PG_FILE=$(find "$BACKUP_DIR/postgres" -name "*.sql.gz" | head -1)
    [[ -z "$PG_FILE" ]] && { log "Brak pliku PostgreSQL w $BACKUP_DIR/postgres"; return 1; }

    log "Plik: $PG_FILE"
    read -rp "⚠️  UWAGA: nadpiszesz bazę '$POSTGRES_DB'. Kontynuować? [tak/N] " confirm
    [[ "$confirm" != "tak" ]] && { log "Przerwano."; return 0; }

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$POSTGRES_DB' AND pid <> pg_backend_pid();" \
        > /dev/null

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" postgres \
        -c "DROP DATABASE IF EXISTS ${POSTGRES_DB}_restore;"

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" postgres \
        -c "CREATE DATABASE ${POSTGRES_DB}_restore OWNER $POSTGRES_USER;"

    zcat "$PG_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        "${POSTGRES_DB}_restore"

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" postgres \
        -c "ALTER DATABASE $POSTGRES_DB RENAME TO ${POSTGRES_DB}_old;"

    PGPASSWORD="$POSTGRES_PASSWORD" psql \
        -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" postgres \
        -c "ALTER DATABASE ${POSTGRES_DB}_restore RENAME TO $POSTGRES_DB;"

    log "PostgreSQL przywrócony. Stara baza: ${POSTGRES_DB}_old (usuń ręcznie po weryfikacji)"
}

# ── Qdrant ─────────────────────────────────────────────────────────────────────

restore_qdrant() {
    log "=== Przywracanie Qdrant ==="
    SNAP_FILE=$(find "$BACKUP_DIR/qdrant" -name "*.snapshot" | head -1)
    [[ -z "$SNAP_FILE" ]] && { log "Brak pliku snapshot w $BACKUP_DIR/qdrant"; return 1; }
    log "Plik: $SNAP_FILE"

    # Prześlij snapshot do Qdrant
    curl -sf -X POST \
        "$QDRANT_URL/collections/$QDRANT_COLLECTION/snapshots/upload?priority=snapshot" \
        -H 'Content-Type: multipart/form-data' \
        -F "snapshot=@$SNAP_FILE" \
        || { log "ERROR: Qdrant restore failed"; return 1; }

    log "Qdrant przywrócony z: $SNAP_FILE"
}

# ── MinIO ──────────────────────────────────────────────────────────────────────

restore_minio() {
    log "=== Przywracanie MinIO ==="
    MINIO_SRC="$BACKUP_DIR/minio/$MINIO_BUCKET"
    [[ -d "$MINIO_SRC" ]] || { log "Brak katalogu MinIO w $BACKUP_DIR/minio/$MINIO_BUCKET"; return 1; }

    mc alias set zrodlo_restore \
        "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" --quiet

    mc mirror \
        "$MINIO_SRC" \
        "zrodlo_restore/$MINIO_BUCKET" \
        --overwrite --quiet

    log "MinIO przywrócony z: $MINIO_SRC"
}

# ── Dispatch ───────────────────────────────────────────────────────────────────

case "$MODE" in
    --postgres-only) restore_postgres ;;
    --qdrant-only)   restore_qdrant   ;;
    --minio-only)    restore_minio    ;;
    all)
        restore_postgres
        restore_qdrant
        restore_minio
        ;;
    *)
        echo "Nieznany tryb: $MODE"
        echo "Użycie: restore.sh <backup-dir> [--postgres-only|--qdrant-only|--minio-only]"
        exit 1
        ;;
esac

log "=== Restore zakończony ==="

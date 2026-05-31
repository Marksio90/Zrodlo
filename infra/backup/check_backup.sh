#!/usr/bin/env bash
# check_backup.sh – weryfikuje że backup z dzisiaj istnieje i powiadamia jeśli nie
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/backup/zrodlo}"
NOTIFY_URL="${BACKUP_NOTIFY_URL:-}"
TODAY=$(date +"%Y%m%d")

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

LATEST=$(find "$BACKUP_ROOT/daily" -mindepth 1 -maxdepth 1 -type d \
    | sort | tail -1)

if [[ -z "$LATEST" ]] || [[ "$LATEST" != *"$TODAY"* ]]; then
    MSG="🔴 Brak backupu Źródło z dnia $TODAY! Ostatni: ${LATEST:-brak}"
    log "$MSG"
    [[ -n "$NOTIFY_URL" ]] && \
        curl -sf -X POST "$NOTIFY_URL" \
            -H 'Content-type: application/json' \
            -d "{\"text\":\"$MSG\"}" || true
    exit 1
fi

PG_SIZE=$(du -sh "$LATEST/postgres" 2>/dev/null | cut -f1 || echo "?")
log "Backup OK: $LATEST (postgres: $PG_SIZE)"

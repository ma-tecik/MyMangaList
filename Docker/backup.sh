#!/bin/sh
set -e

DB_PATH=/app/data/mml.sqlite3
BACKUP_DIR=/app/data/backups
TIMESTAMP=$(date +%F)

mkdir -p "$BACKUP_DIR"

sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/mml_$TIMESTAMP.sqlite3'"

echo "Backup created: $BACKUP_DIR/mml_$TIMESTAMP.db"
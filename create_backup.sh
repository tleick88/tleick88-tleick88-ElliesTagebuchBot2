#!/bin/bash
# Backup-Script für Tochter-Erinnerungen Bot

BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

# .env Datei sichern (ohne sensible Daten)
cp .env "$BACKUP_DIR/env_backup.txt"

# Logs sichern falls vorhanden
if [ -f "bot.log" ]; then
    cp bot.log "$BACKUP_DIR/"
fi

# Google Sheets ID für Referenz
echo "Google Sheets ID: $GOOGLE_SHEETS_ID" > "$BACKUP_DIR/sheets_info.txt"

echo "✅ Backup erstellt in: $BACKUP_DIR"

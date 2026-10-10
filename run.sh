#!/bin/sh
# Führt check_changes.py in einer Endlosschleife aus (Standard: einmal pro Stunde).
#   CHECK_INTERVAL_SECONDS  Pause zwischen zwei Läufen (Standard: 3600)
#   CHECK_ARGS              Optionen für check_changes.py (Standard: "--alert -q -n")
set -u

INTERVAL="${CHECK_INTERVAL_SECONDS:-3600}"
ARGS="${CHECK_ARGS:---alert -q -n}"

echo "untis-alert gestartet – Intervall ${INTERVAL}s, Optionen: ${ARGS}"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Check läuft"
    # shellcheck disable=SC2086  # ARGS bewusst in einzelne Optionen aufteilen
    python check_changes.py $ARGS || echo "[$(date '+%Y-%m-%d %H:%M:%S')] Check fehlgeschlagen (Exit $?)"
    sleep "$INTERVAL"
done

# WebUntis Alert (untis_alert)

Ein Python-Skript, das regelmäßig (z.B. stündlich über Docker) den Stundenplan eines WebUntis-Accounts auf Änderungen (Entfall, Vertretung, Zusatz, Raumänderung) für die nächsten 14 Tage prüft.

Neue Änderungen können per **E-Mail** (mit übersichtlicher HTML-Formatierung) und optional per **HomeAssistant Webhook** gemeldet werden.

## Features
- Abruf des Stundenplans über die inoffizielle JSON-RPC-Schnittstelle von WebUntis.
- Erkennt: `ENTFALL`, `VERTRETUNG`, `ZUSATZ` und `RAUMÄNDERUNG`.
- Status-Speicherung (`data/last_changes.json`), um nur *neue* Änderungen zu melden.
- Docker-ready für den 24/7 Betrieb (z.B. auf einem Raspberry Pi).
- Detailliertes Logging.

## Installation & Setup

1. **Repository klonen**
   ```bash
   git clone https://github.com/mkoderer/untis_alert.git
   cd untis_alert
   ```

2. **Rechte für den Data-Ordner anpassen** (Wichtig für Docker)
   Docker führt das Skript als User mit UID 1000 aus. Der `data/`-Ordner muss für diesen beschreibbar sein:
   ```bash
   sudo chown -R 1000:1000 data
   ```

3. **Konfiguration anlegen**
   Kopiere die `.env.example` zu `.env` und trage deine Daten ein:
   ```bash
   cp .env.example .env
   nano .env
   ```
   *(Tipp: Für mehrere E-Mail-Empfänger diese einfach per Komma getrennt bei `EMAIL_TO` eintragen).*

4. **Starten**
   ```bash
   docker compose up -d --build
   ```

5. **Logs prüfen**
   ```bash
   docker compose logs -f
   ```

## Projekt-Status & Nächste Schritte
(Siehe `CONTEXT.md` für interne Entwicklungs-Details und anstehende Aufgaben).

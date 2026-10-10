# Project Context & History

This document serves to capture the current state of development for future sessions.

## Current Status (As of October 2026)
- **Core Functionality:** The WebUntis crawler (`check_changes.py`) successfully fetches the timetable for the next 14 days via JSON-RPC and detects changes (Cancellations, Substitutions, Additions, Room Changes).
- **State Persistence:** The last known state is saved as JSON in `data/last_changes.json`. Docker permission issues were resolved by tracking a `data/.gitkeep` file and using `chown` during setup.
- **Alerting:**
  - **E-Mail:** Fully implemented. Uses SMTP, sends HTML emails with color-coded change types and a dynamic subject (e.g., "Stundenplan-Änderungen (14.10. - 16.10.)"). Supports multiple recipients (comma-separated).
  - **HomeAssistant:** Prepared in `alert.py` (via POST to `HA_WEBHOOK_URL`), but not yet activated or tested.
  - **WhatsApp (CallMeBot):** Evaluated but temporarily discarded in favor of E-Mail.
- **Deployment:** Docker Compose setup (`Dockerfile`, `docker-compose.yml`, `run.sh`) runs successfully on a Raspberry Pi. Executes the check hourly (`CHECK_INTERVAL_SECONDS=3600`) with clean logging.

## Open Points / Next Steps (for the next session)
1. **HomeAssistant Integration:**
   - Configure Webhook URL in `.env`.
   - Test if the JSON payload (`{"message": "..."}`) arrives correctly in HomeAssistant and triggers an automation.
   - Adjust the payload if HomeAssistant requires a different HTML/Text structure.
2. **Enhancements / Feature Ideas (Optional):**
   - **Pushover / Telegram:** If E-Mail and HomeAssistant are not enough, other messengers could easily be added in `alert.py`.
   - **Exam Dates (Klassenarbeiten):** Initially investigated, but the current "Class" account in WebUntis (personType=1) lacks permissions (403 Error). If a parent/student account with more privileges becomes available, this feature could be reactivated.
   - **Finer Filtering:** Currently, only `ENTFALL` (Cancellation) and `VERTRETUNG` (Substitution) trigger an alert (`ALERT_TYPES` in `alert.py`). This could be made configurable via `.env` if notifications for mere room changes are also desired.

## Technical Details Reminder
- The WebUntis API requires the school name, username, and password for login. The session ID must be passed in subsequent requests.
- Timestamps from Untis are formatted as `YYYYMMDD` (Date) and `HHMM` (Time).
- To detect modifications, `check_changes.py` generates a unique hash key (`d|st|en|status|text`) to recognize if, for example, only the room of an existing substitution has changed.

"""Alarm-Funktion für neue Stundenplan-Änderungen.

VORBEREITET, NOCH NICHT IMPLEMENTIERT.
Wird von check_changes.py mit allen neuen ENTFALL-/VERTRETUNG-Einträgen aufgerufen.
Später hier z.B. Telegram, Discord, E-Mail oder macOS-Benachrichtigung einbauen.
"""

# Status-Arten, die einen Alarm auslösen
ALERT_TYPES = {"ENTFALL", "VERTRETUNG"}


def send_alert(changes: list[dict]) -> None:
    """Benachrichtigt über neue Änderungen.

    Jeder Eintrag in `changes` hat die Felder:
      date (YYYYMMDD, int), start / end (HHMM, int), status (str), text (str)
    """
    if not changes:
        return
    # TODO: echte Benachrichtigung implementieren (nächster Schritt)
    print(f"[Alarm vorbereitet, noch nicht aktiv] {len(changes)} neue Änderung(en) würden gemeldet.")

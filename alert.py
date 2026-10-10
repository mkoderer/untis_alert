"""Alarm-Funktion für neue Stundenplan-Änderungen.

Unterstützt Benachrichtigungen über:
  - HomeAssistant (via Webhook)
  - E-Mail (via SMTP)
"""

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage

import requests
from dotenv import load_dotenv

load_dotenv()

# Status-Arten, die einen Alarm auslösen
ALERT_TYPES = {"ENTFALL", "VERTRETUNG"}


def format_message(changes: list[dict]) -> str:
    """Formatiert die Änderungen zu einem lesbaren Text."""
    lines = ["🚨 WebUntis Stundenplan-Änderung:\n"]
    for c in changes:
        d = datetime.strptime(str(c["date"]), "%Y%m%d").strftime("%d.%m.%Y")
        st = f"{c['start'] // 100:02d}:{c['start'] % 100:02d}"
        en = f"{c['end'] // 100:02d}:{c['end'] % 100:02d}"
        lines.append(f"• {d} {st}-{en}")
        lines.append(f"  {c['status']}: {c['text']}\n")
    return "\n".join(lines).strip()


def send_homeassistant(msg: str) -> None:
    """Sendet einen Payload an einen HomeAssistant Webhook."""
    url = os.getenv("HA_WEBHOOK_URL", "").strip()
    if not url:
        return

    try:
        # Wir senden die formatierte Nachricht als "message" Attribut
        resp = requests.post(url, json={"message": msg}, timeout=10)
        resp.raise_for_status()
        print("[Alert] HomeAssistant Webhook erfolgreich ausgelöst.")
    except Exception as e:
        print(f"[Alert] Fehler beim Senden an HomeAssistant: {e}")


def send_email(msg: str) -> None:
    """Sendet eine E-Mail via SMTP."""
    server = os.getenv("SMTP_SERVER", "").strip()
    if not server:
        return

    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    sender = os.getenv("EMAIL_FROM", user).strip()
    recipient = os.getenv("EMAIL_TO", "").strip()

    if not recipient:
        print("[Alert] SMTP_SERVER gesetzt, aber EMAIL_TO fehlt.")
        return

    em = EmailMessage()
    em.set_content(msg)
    em["Subject"] = "WebUntis Alarm: Stundenplan geändert"
    em["From"] = sender
    em["To"] = recipient

    try:
        with smtplib.SMTP(server, port) as s:
            s.starttls()
            if user and password:
                s.login(user, password)
            s.send_message(em)
        print("[Alert] E-Mail erfolgreich gesendet.")
    except Exception as e:
        print(f"[Alert] Fehler beim Senden der E-Mail: {e}")


def send_alert(changes: list[dict]) -> None:
    """Benachrichtigt über neue Änderungen."""
    if not changes:
        return

    msg = format_message(changes)
    
    # Versuche beide Wege (werden ignoriert, wenn in .env nicht konfiguriert)
    send_homeassistant(msg)
    send_email(msg)

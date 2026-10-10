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


def get_date_range_str(changes: list[dict]) -> str:
    if not changes:
        return ""
    dates = [c["date"] for c in changes]
    min_date = datetime.strptime(str(min(dates)), "%Y%m%d")
    max_date = datetime.strptime(str(max(dates)), "%Y%m%d")
    if min_date == max_date:
        return min_date.strftime("%d.%m.")
    return f"{min_date.strftime('%d.%m.')} - {max_date.strftime('%d.%m.')}"

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

def format_html_message(changes: list[dict]) -> str:
    """Erzeugt eine schöne HTML-Version der E-Mail."""
    from collections import defaultdict
    grouped = defaultdict(list)
    for c in changes:
        grouped[c["date"]].append(c)

    html = "<div style='font-family: Arial, sans-serif; color: #333; max-width: 600px;'>"
    html += "<h2 style='color: #2c3e50;'>🚨 Stundenplan-Änderungen</h2>"

    wdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    for d in sorted(grouped.keys()):
        date_obj = datetime.strptime(str(d), "%Y%m%d")
        date_str = f"{wdays[date_obj.weekday()]}, {date_obj.strftime('%d.%m.%Y')}"
        
        html += f"<h3 style='border-bottom: 2px solid #3498db; padding-bottom: 5px; color: #3498db; margin-top: 25px;'>{date_str}</h3>"
        
        for c in sorted(grouped[d], key=lambda x: x["start"]):
            st = f"{c['start'] // 100:02d}:{c['start'] % 100:02d}"
            en = f"{c['end'] // 100:02d}:{c['end'] % 100:02d}"
            
            # Farben je nach Status
            if c['status'] == "ENTFALL":
                color = "#e74c3c" # Rot
            elif c['status'] == "VERTRETUNG":
                color = "#f39c12" # Orange
            elif c['status'] == "RAUMÄNDERUNG":
                color = "#8e44ad" # Lila
            else:
                color = "#27ae60" # Grün (Zusatz)

            html += f"""
            <div style='margin-bottom: 12px; padding: 12px; background-color: #f8f9fa; border-left: 5px solid {color}; border-radius: 3px;'>
                <div style='margin-bottom: 5px;'>
                    <strong style='font-size: 16px;'>{st} - {en} Uhr</strong> &nbsp;|&nbsp; 
                    <span style='color: {color}; font-weight: bold;'>{c['status']}</span>
                </div>
                <div style='font-size: 15px; color: #555;'>{c['text']}</div>
            </div>
            """
    html += "</div>"
    return html

def send_homeassistant(msg: str) -> None:
    """Sendet einen Payload an einen HomeAssistant Webhook."""
    url = os.getenv("HA_WEBHOOK_URL", "").strip()
    if not url:
        return

    try:
        resp = requests.post(url, json={"message": msg}, timeout=10)
        resp.raise_for_status()
        print("[Alert] HomeAssistant Webhook erfolgreich ausgelöst.")
    except Exception as e:
        print(f"[Alert] Fehler beim Senden an HomeAssistant: {e}")

def send_email(changes: list[dict]) -> None:
    """Sendet eine E-Mail via SMTP."""
    server = os.getenv("SMTP_SERVER", "").strip()
    if not server:
        return

    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    
    sender_email = os.getenv("EMAIL_FROM", user).strip()
    sender_name = os.getenv("EMAIL_FROM_NAME", "").strip()
    recipient = os.getenv("EMAIL_TO", "").strip()

    if not recipient:
        print("[Alert] SMTP_SERVER gesetzt, aber EMAIL_TO fehlt.")
        return

    # Standard für E-Mails ist ein Komma zur Trennung von Adressen
    recipient = recipient.replace(";", ",")

    if sender_name:
        sender = f"{sender_name} <{sender_email}>"
    else:
        sender = sender_email

    from email.message import EmailMessage
    em = EmailMessage()
    
    # Text Version als Fallback
    text_msg = format_message(changes)
    em.set_content(text_msg)
    
    # HTML Version hinzufügen
    html_msg = format_html_message(changes)
    em.add_alternative(html_msg, subtype='html')

    date_range = get_date_range_str(changes)
    em["Subject"] = f"Stundenplan-Änderungen ({date_range})"
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

    print(f"\n[Alert] Sende Benachrichtigung für {len(changes)} neue Änderungen:")
    for c in changes:
        d = datetime.strptime(str(c["date"]), "%Y%m%d").strftime("%d.%m.%Y")
        st = f"{c['start'] // 100:02d}:{c['start'] % 100:02d}"
        en = f"{c['end'] // 100:02d}:{c['end'] % 100:02d}"
        print(f"  -> {d} {st}-{en} Uhr | {c['status']}: {c['text']}")
    print("-" * 50)

    msg = format_message(changes)
    
    send_homeassistant(msg)
    send_email(changes)

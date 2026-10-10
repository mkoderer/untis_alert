"""Änderungen im Stundenplan der nächsten 14 Tage anzeigen und mit dem letzten Lauf vergleichen.

Erkennt:
  - ENTFALL       Stunde fällt aus (code=cancelled, kein Ersatz im selben Slot)
  - VERTRETUNG    Stunde fällt aus und wird im selben Slot ersetzt (cancelled + irregular)
  - ZUSATZ        zusätzliche/unplanmäßige Stunde (irregular ohne Ausfall im Slot)
  - RAUMÄNDERUNG  regulärer Unterricht in anderem Raum (orgid gesetzt)

Der letzte Stand wird in data/last_changes.json gespeichert. Neue ENTFALL-/VERTRETUNG-
Einträge werden nur mit --alert an alert.send_alert() übergeben. Beim allerersten Lauf
gibt es keinen Vergleich (Ausgangsstand) und keinen Alarm.

Optionen: siehe `python check_changes.py --help`.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from alert import ALERT_TYPES, send_alert
from fetch_timetable import fetch_timetable

TAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
DAYS_AHEAD = 14
STATE_FILE = Path("data/last_changes.json")


def fmt_time(n: int) -> str:
    return f"{n // 100:02d}:{n % 100:02d}"


def fmt_day(n: int) -> str:
    d = datetime.strptime(str(n), "%Y%m%d").date()
    return f"{TAGE[d.weekday()]} {d:%d.%m.%Y}"


def names(p: dict, key: str) -> str:
    joined = ", ".join(x.get("longname") or x.get("name", "?") for x in p.get(key, []))
    if joined:
        return joined
    return "Sonderveranstaltung" if key == "su" else "-"


def rooms(p: dict) -> str:
    """Raum(e), bei Änderung mit 'statt <ursprünglich>'."""
    parts = []
    for r in p.get("ro", []):
        if r.get("orgname"):
            parts.append(f"{r['name']} statt {r['orgname']}")
        else:
            parts.append(r.get("name", "?"))
    return ", ".join(parts) or "-"


def has_room_change(p: dict) -> bool:
    return any("orgid" in r for r in p.get("ro", []))


def note(p: dict) -> str:
    texts = [p.get("substText"), p.get("lstext"), p.get("info")]
    unique = list(dict.fromkeys(t for t in texts if t))
    return f'  „{" | ".join(unique)}“' if unique else ""


def change(d: int, st: int, en: int, status: str, text: str) -> dict:
    return {"date": d, "start": st, "end": en, "status": status, "text": text}


def key(c: dict) -> str:
    """Eindeutiger Schlüssel; ändert sich der Text (z.B. anderer Raum), gilt es als neu."""
    return f"{c['date']}|{c['start']}|{c['end']}|{c['status']}|{c['text']}"


def find_changes(periods: list[dict]) -> list[dict]:
    slots = defaultdict(list)
    for p in periods:
        slots[(p["date"], p["startTime"], p["endTime"])].append(p)

    changes = []
    for (d, st, en), ps in sorted(slots.items()):
        cancelled = [p for p in ps if p.get("code") == "cancelled"]
        irregular = [p for p in ps if p.get("code") == "irregular"]
        regular = [p for p in ps if not p.get("code")]

        if cancelled and irregular:
            alt = ", ".join(names(p, "su") for p in cancelled)
            for p in irregular:
                changes.append(change(d, st, en, "VERTRETUNG",
                                      f"{alt} → {names(p, 'su')}  (Raum {rooms(p)}){note(p)}"))
        else:
            for p in cancelled:
                changes.append(change(d, st, en, "ENTFALL", f"{names(p, 'su')}{note(p)}"))
            for p in irregular:
                changes.append(change(d, st, en, "ZUSATZ", f"{names(p, 'su')}  (Raum {rooms(p)}){note(p)}"))
        for p in regular:
            if has_room_change(p):
                changes.append(change(d, st, en, "RAUMÄNDERUNG", f"{names(p, 'su')}  (Raum {rooms(p)}){note(p)}"))
    return changes


def load_state(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())["changes"]


def save_state(path: Path, changes: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"checked_at": datetime.now().isoformat(timespec="seconds"), "changes": changes},
        indent=2, ensure_ascii=False,
    ))


def print_list(changes: list[dict], mark: set[str] | None = None) -> None:
    current_day = None
    for c in changes:
        if c["date"] != current_day:
            print(fmt_day(c["date"]))
            current_day = c["date"]
        flag = "NEU " if mark and key(c) in mark else "    "
        print(f"  {flag}{fmt_time(c['start'])}–{fmt_time(c['end'])}  {c['status']:<12}  {c['text']}")


def positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("muss mindestens 1 sein")
    return n


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_changes.py",
        description="Prüft den WebUntis-Stundenplan auf Entfall, Vertretung, Zusatzstunden "
                    "und Raumänderungen und vergleicht mit dem letzten Lauf.",
        epilog="Beispiele:\n"
               "  check_changes.py                  Änderungen der nächsten 14 Tage anzeigen\n"
               "  check_changes.py --alert -q       für Cron: nur bei Neuem ausgeben + alarmieren\n"
               "  check_changes.py -d 7 --no-save   7 Tage ansehen, gespeicherten Stand nicht anfassen\n"
               "  check_changes.py --reset          Ausgangsstand neu setzen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-d", "--days", type=positive_int, default=DAYS_AHEAD, metavar="N",
                        help=f"Anzahl Tage ab heute (Standard: {DAYS_AHEAD})")
    parser.add_argument("-a", "--alert", action="store_true",
                        help=f"bei neuen Änderungen ({', '.join(sorted(ALERT_TYPES))}) alarmieren "
                             "(Standard: aus)")
    parser.add_argument("-n", "--only-new", action="store_true",
                        help="nur neue Änderungen seit dem letzten Check anzeigen")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="keine Ausgabe, außer es gibt neue oder aufgehobene Änderungen (für Cron)")
    parser.add_argument("--no-save", action="store_true",
                        help="gespeicherten Stand nicht aktualisieren (Probelauf)")
    parser.add_argument("--reset", action="store_true",
                        help="gespeicherten Stand verwerfen; dieser Lauf wird neuer Ausgangsstand")
    parser.add_argument("--state", type=Path, default=STATE_FILE, metavar="DATEI",
                        help=f"Datei für den gespeicherten Stand (Standard: {STATE_FILE})")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    start = date.today()
    end = start + timedelta(days=args.days)
    today_int = int(start.strftime("%Y%m%d"))

    try:
        periods = fetch_timetable(start, end)
    except Exception as e:
        print(f"Fehler beim Abruf des Stundenplans: {e}", file=sys.stderr)
        return 2

    changes = find_changes(periods)
    previous = None if args.reset else load_state(args.state)

    if previous is None:
        new, gone = [], []
    else:
        prev_keys = {key(c) for c in previous}
        curr_keys = {key(c) for c in changes}
        new = [c for c in changes if key(c) not in prev_keys]
        # Vergangene Tage fallen natürlich heraus – nur zukünftige als „aufgehoben“ melden
        gone = [c for c in previous if key(c) not in curr_keys and c["date"] >= today_int]

    show = not args.quiet or new or gone
    if show:
        last = max((p["date"] for p in periods), default=None)
        print(f"Stundenplan-Änderungen {start:%d.%m.%Y} – {end:%d.%m.%Y}")
        print(f"{len(periods)} Stunden geladen" + (f", Daten bis {fmt_day(last)}" if last else ""))
        print()

        if previous is None:
            grund = "Reset" if args.reset else "Erster Lauf"
            print(f"{grund} – Ausgangsstand wird {'nicht ' if args.no_save else ''}gespeichert, kein Vergleich.\n")

        listing = new if args.only_new else changes
        if listing:
            print_list(listing, mark={key(c) for c in new})
        else:
            print("Keine neuen Änderungen." if args.only_new else "Keine Änderungen.")

        if previous is not None:
            print()
            print(f"Seit letztem Check: {len(new)} neu, {len(gone)} aufgehoben/geändert")
            if gone:
                print("Nicht mehr vorhanden:")
                print_list(gone)

    if not args.no_save:
        save_state(args.state, changes)

    if args.alert:
        alerts = [c for c in new if c["status"] in ALERT_TYPES]
        send_alert(alerts)
    return 0


if __name__ == "__main__":
    sys.exit(main())

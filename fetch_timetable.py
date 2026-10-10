"""Stundenplan per JSON-RPC abrufen.

`fetch_timetable(start, end)` wird von anderen Skripten wiederverwendet.
Direkt ausgeführt: gibt die Rohdaten der nächsten Woche aus.
Zugangsdaten werden nie ausgegeben.
"""

import json
import sys
from datetime import date, timedelta

import requests

from login import PASSWORD, USER, rpc


def ymd(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def fetch_timetable(start: date, end: date) -> list[dict]:
    """Login, Stundenplan des eingeloggten Elements (Klasse) holen, Logout."""
    with requests.Session() as s:
        s.headers["User-Agent"] = "UntisCrawler/0.1"
        auth = rpc(s, "authenticate", {"user": USER, "password": PASSWORD, "client": "UntisCrawler"})
        try:
            result = rpc(s, "getTimetable", {
                "options": {
                    "element": {"id": auth["personId"], "type": auth["personType"]},
                    "startDate": ymd(start),
                    "endDate": ymd(end),
                    "showInfo": True,
                    "showSubstText": True,
                    "showLsText": True,
                    "showStudentgroup": True,
                    "klasseFields": ["id", "name", "longname"],
                    "subjectFields": ["id", "name", "longname"],
                    "teacherFields": ["id", "name", "longname"],
                    "roomFields": ["id", "name", "longname"],
                },
            })
        finally:
            rpc(s, "logout")
    result.sort(key=lambda p: (p["date"], p["startTime"]))
    return result


def next_week() -> tuple[date, date]:
    """Montag..Freitag der kommenden Woche."""
    today = date.today()
    monday = today + timedelta(days=7 - today.weekday())
    return monday, monday + timedelta(days=4)


def main() -> int:
    start, end = next_week()
    result = fetch_timetable(start, end)
    print(f"# {start} .. {end}: {len(result)} Einträge")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

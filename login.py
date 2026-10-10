"""Step 1: WebUntis login test (JSON-RPC).

Reads credentials from .env, authenticates, prints session info, logs out.
Credentials are never printed or logged.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("UNTIS_SERVER", "")
SCHOOL = os.getenv("UNTIS_SCHOOL", "")
USER = os.getenv("UNTIS_USER", "")
PASSWORD = os.getenv("UNTIS_PASSWORD", "")

URL = f"https://{SERVER}/WebUntis/jsonrpc.do"


def rpc(session: requests.Session, method: str, params: dict | None = None) -> dict:
    """Call a JSON-RPC method and return the 'result' (raises on error)."""
    if not SERVER or not SCHOOL:
        raise RuntimeError("UNTIS_SERVER / UNTIS_SCHOOL fehlen in .env")
    payload = {"id": "untis_crawler", "method": method, "params": params or {}, "jsonrpc": "2.0"}
    resp = session.post(URL, params={"school": SCHOOL}, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"{method} failed: [{err.get('code')}] {err.get('message')}")
    return data.get("result")


def main() -> int:
    if not SERVER or not SCHOOL or not USER or not PASSWORD:
        print("UNTIS_SERVER / UNTIS_SCHOOL / UNTIS_USER / UNTIS_PASSWORD fehlen in .env")
        return 1

    with requests.Session() as s:
        s.headers["User-Agent"] = "UntisCrawler/0.1"
        try:
            result = rpc(s, "authenticate", {"user": USER, "password": PASSWORD, "client": "UntisCrawler"})
        except Exception as e:
            print(f"Login failed: {e}")
            return 1

        print("Login OK")
        print(f"  personType: {result.get('personType')}  (1=class, 2=teacher, 5=student, 12=parent)")
        print(f"  personId:   {result.get('personId')}")
        print(f"  klasseId:   {result.get('klasseId')}")

        rpc(s, "logout")
        print("Logged out")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime

import requests

URL = "https://app.stintinospiagge.it/prenotazioni/1/1?lang=it"
STATE_FILE = "beach_notifier_state.json"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
}

NEGATIVE_PATTERNS = [
    r"posti risultano esauriti",
    r"disponibilit[aà].{0,20}esaurit",
    r"attualmente esaurite",
    r"nessuna disponibilit[aà]",
]

POSITIVE_PATTERNS = [
    r"disponibilit[aà]",
    r"posti indicativi",
    r"prenotazione giornaliera",
]


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def fetch_page():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def detect_status(html):
    low = html.lower()
    negative = any(re.search(p, low, re.I) for p in NEGATIVE_PATTERNS)
    positive = any(re.search(p, low, re.I) for p in POSITIVE_PATTERNS)

    if negative:
        return "sold_out"
    if positive:
        return "maybe_available"
    return "unknown"


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_status": None}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")
    api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(api, json={"chat_id": CHAT_ID, "text": text}, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    state = load_state()
    html = fetch_page()
    status = detect_status(html)
    last_status = state.get("last_status")
    log(f"current status: {status}")

    if status in ("maybe_available", "unknown") and last_status != status:
        msg = (
            "Beach alert: Moeglicherweise ist ein Slot frei oder die Seite hat sich geaendert.\n"
            f"Status: {status}\n"
            f"Link: {URL}"
        )
        send_telegram(msg)
        log("telegram sent")

    state["last_status"] = status
    save_state(state)


if __name__ == "__main__":
    main()

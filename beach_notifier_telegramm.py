import os, re, requests
from datetime import datetime

URL = "https://app.stintinospiagge.it/prenotazioni/1/1?lang=it"
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

NEGATIVE = [
    r"posti risultano esauriti",
    r"attualmente esaurite",
    r"nessuna disponibilit",
]

def main():
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    low = r.text.lower()
    sold_out = any(re.search(p, low) for p in NEGATIVE)
    print(f"[{datetime.now()}] sold_out={sold_out}")
    if not sold_out:
        api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(api, json={"chat_id": CHAT_ID, "text": f"Beach alert: Slot moeglicherweise frei! {URL}"}, timeout=30)
        print("telegram sent")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Delete all posts from @pashtelka_news and republish with updated teasers + images."""

import json
import sys
import time
from pathlib import Path

import requests

TOKEN = "8585090528:AAHWmjiT9TIlmdtz0x8Q_YpUCnP3APEx7i8"
CHANNEL_ID = "-1003726391778"
API = f"https://api.telegram.org/bot{TOKEN}"

ROOT = Path(__file__).resolve().parent.parent
TEASERS_DIR = ROOT / "state" / "teasers"
IMAGES_DIR = ROOT / "gatsby" / "static" / "images"

# Content order (chronological: oldest first)
CONTENT_ORDER = [
    "fuel-prices-drop-iran-ceasefire",
    "markets-surge-oil-drops-iran-ceasefire",
    "rent-prices-drop-third-month",
    "housing-euribor-180-percent-jump",
    "housing-aid-34k-applications-storm-damage",
    "health-system-crisis-oncology-queues",
    "easter-road-safety-20-deaths",
    "grocery-basket-record-258-euro",
    "parliament-fuel-tax-cut-june",
    "fire-prevention-land-clearing-guide",
    "rasi-immigration-enforcement-2025",
    "via-verde-immigration-one-year-results",
    "citizenship-law-10-year-naturalization",
    "aima-system-failure-april-deadline",
    "integrar-tourism-training-program",
    "labor-code-reform-trabalho-xxi",
    "lisbon-metro-strike-april-9-14",
    "metro-lisboa-24-hour-strike-april-9",
    "portugal-nato-baltic-deployment",
    "volta-deposit-system-bottles-cans-launch",
    "wildfire-season-prep-cipo",
    "rain-hail-storms-weather-april-8",
    "saharan-dust-health-warning",
    "weather-swings-saharan-dust-weekend",
    "yellow-warnings-south-30c-storms",
    "evening-digest-april-8",
]


def get_chat_info():
    """Get channel info to find message range."""
    resp = requests.get(f"{API}/getChat", params={"chat_id": CHANNEL_ID}, timeout=10)
    return resp.json()


def delete_messages(start_id: int, end_id: int):
    """Delete messages in range."""
    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            resp = requests.post(
                f"{API}/deleteMessage",
                json={"chat_id": int(CHANNEL_ID), "message_id": msg_id},
                timeout=10,
            )
            r = resp.json()
            if r.get("ok"):
                deleted += 1
        except Exception:
            pass
        time.sleep(0.1)  # Rate limit
    return deleted


def send_photo(image_path: str, caption: str, silent: bool = True) -> int | None:
    """Send photo with caption."""
    data = {"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"}
    if silent:
        data["disable_notification"] = "true"
    with open(image_path, "rb") as f:
        resp = requests.post(
            f"{API}/sendPhoto",
            data=data,
            files={"photo": f},
            timeout=30,
        )
    r = resp.json()
    if r.get("ok"):
        return r["result"]["message_id"]
    print(f"  Error: {r.get('description')}", file=sys.stderr)
    return None


def add_reaction(msg_id: int, emoji: str = "\U0001f525"):
    """Add reaction to message."""
    try:
        requests.post(
            f"{API}/setMessageReaction",
            json={
                "chat_id": int(CHANNEL_ID),
                "message_id": msg_id,
                "reaction": [{"type": "emoji", "emoji": emoji}],
            },
            timeout=10,
        )
    except Exception:
        pass


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("all", "delete"):
        # Delete existing messages (try range 1-200)
        print("Deleting existing messages...")
        deleted = delete_messages(1, 200)
        print(f"Deleted {deleted} messages.")

    if mode in ("all", "publish"):
        print(f"\nPublishing {len(CONTENT_ORDER)} posts...")
        for i, slug in enumerate(CONTENT_ORDER):
            teaser_file = TEASERS_DIR / f"{slug}.json"
            if not teaser_file.exists():
                print(f"  [{i+1}] SKIP {slug} (no teaser)")
                continue

            teaser = json.loads(teaser_file.read_text(encoding="utf-8"))
            caption = teaser["tg_post"]

            # Find image
            image_path = None
            for ext in (".jpg", ".jpeg", ".png"):
                p = IMAGES_DIR / f"{slug}{ext}"
                if p.exists():
                    image_path = str(p)
                    break

            if not image_path:
                print(f"  [{i+1}] SKIP {slug} (no image)")
                continue

            msg_id = send_photo(image_path, caption, silent=True)
            if msg_id:
                add_reaction(msg_id, "\U0001f525")
                print(f"  [{i+1}/{len(CONTENT_ORDER)}] {slug} -> msg {msg_id}")
            else:
                print(f"  [{i+1}/{len(CONTENT_ORDER)}] FAILED {slug}")

            time.sleep(1.5)  # TG rate limit: ~20 msgs/min

        print("\nDone!")


if __name__ == "__main__":
    main()

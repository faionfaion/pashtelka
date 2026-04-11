#!/usr/bin/env python3
"""Send a post to @pashtelka_news Telegram channel.

Usage:
  python3 scripts/send_post.py --caption "text" [--url URL] [--silent] [--reaction "🔥"]
"""
import argparse
import sys

import requests

TOKEN = "8578996384:AAFhkTHh_D40VdCc7em5U9taM5a-o00JzaA"
CHANNEL_ID = "-1003726391778"
API = f"https://api.telegram.org/bot{TOKEN}"


def send_text(chat_id, caption, preview_url=None, silent=False,
              button_url=None, button_text="Читати повністю →"):
    text = caption
    if preview_url:
        text = f'<a href="{preview_url}">\u00a0</a>{caption}'

    link_opts = {"prefer_large_media": True, "show_above_text": True}
    if preview_url:
        link_opts["url"] = preview_url

    payload = {
        "chat_id": int(chat_id),
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": link_opts,
    }
    if silent:
        payload["disable_notification"] = True
    if button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": button_text, "url": button_url}]]
        }

    resp = requests.post(f"{API}/sendMessage", json=payload)
    r = resp.json()
    if r.get("ok"):
        return r["result"]["message_id"]
    print(f"Error: {r.get('description')}", file=sys.stderr)
    return None


def add_reaction(chat_id, msg_id, emoji):
    requests.post(
        f"{API}/setMessageReaction",
        json={
            "chat_id": int(chat_id),
            "message_id": msg_id,
            "reaction": [{"type": "emoji", "emoji": emoji}],
        },
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--caption", required=True)
    p.add_argument("--url", default=None)
    p.add_argument("--reaction", default="🔥")
    p.add_argument("--silent", action="store_true")
    args = p.parse_args()

    msg_id = send_text(CHANNEL_ID, args.caption, preview_url=args.url, silent=args.silent,
                       button_url=args.url)
    if msg_id:
        add_reaction(CHANNEL_ID, msg_id, args.reaction)
        print(msg_id)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

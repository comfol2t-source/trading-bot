"""Poll Telegram for new commands and dispatch.

Designed to run on a cron (every 5-10 minutes) — uses getUpdates with
the saved offset so we only process each message once.
"""
import requests

import config
from bot import commands, state
from bot.telegram_sender import send_message


def poll_and_handle() -> int:
    """Fetch new messages, route each, return number processed."""
    last_id = state.get_last_update_id()
    offset = last_id + 1 if last_id else None

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getUpdates"
    params: dict = {"timeout": 0}
    if offset:
        params["offset"] = offset

    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            print(f"  ! getUpdates HTTP {r.status_code}")
            return 0
        updates = r.json().get("result", []) or []
    except requests.RequestException as e:
        print(f"  ! getUpdates error: {type(e).__name__}")
        return 0

    if not updates:
        return 0

    processed = 0
    max_uid = last_id
    for u in updates:
        uid = u.get("update_id", 0)
        max_uid = max(max_uid, uid)
        msg = u.get("message") or u.get("edited_message")
        if not msg:
            continue
        # Only respond to the configured chat (security)
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != str(config.TELEGRAM_CHAT_ID):
            continue
        text = msg.get("text", "")
        if not text:
            continue
        reply = commands.route(text)
        # Split long replies (Telegram 4096 char limit)
        _send_chunks(reply)
        processed += 1

    state.set_last_update_id(max_uid)
    return processed


def _send_chunks(text: str) -> None:
    """Split message above 4000 chars on blank lines."""
    if len(text) <= 4000:
        send_message(text)
        return
    chunks = []
    current = []
    cur_len = 0
    for line in text.split("\n"):
        if cur_len + len(line) + 1 > 3800 and current:
            chunks.append("\n".join(current))
            current = []
            cur_len = 0
        current.append(line)
        cur_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    for c in chunks:
        send_message(c)

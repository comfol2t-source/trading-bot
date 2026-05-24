"""Diagnose Telegram bot setup.

Checks:
  1. Bot token is valid (getMe).
  2. Lists all chats that have messaged the bot (getUpdates).
  3. Compares against the configured TELEGRAM_CHAT_ID.

Never prints the token itself.
"""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import requests

import config


def get_me(token: str) -> dict | None:
    """Verify the bot token by calling getMe."""
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"❌ getMe failed: HTTP {r.status_code}")
            print(f"   Response: {r.text}")
            return None
        return r.json().get("result")
    except requests.RequestException as e:
        print(f"❌ Network error: {type(e).__name__}")
        return None


def get_updates(token: str) -> list[dict]:
    """List chats that have messaged the bot recently."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            print(f"❌ getUpdates failed: HTTP {r.status_code}")
            return []
        return r.json().get("result", [])
    except requests.RequestException as e:
        print(f"❌ Network error: {type(e).__name__}")
        return []


def main():
    config.validate()
    token = config.TELEGRAM_BOT_TOKEN
    configured_chat_id = str(config.TELEGRAM_CHAT_ID)

    print("=" * 50)
    print("Telegram Bot Diagnostic")
    print("=" * 50)

    # 1. Check bot
    print("\n[1] Verifying bot token...")
    bot = get_me(token)
    if not bot:
        print("\n→ Token is invalid or revoked. Get a new one from @BotFather.")
        return
    print(f"✅ Bot is online")
    print(f"   Name: {bot.get('first_name')}")
    print(f"   Username: @{bot.get('username')}")
    print(f"   Bot ID: {bot.get('id')}")

    # 2. Check configured chat ID
    print(f"\n[2] Configured TELEGRAM_CHAT_ID: {configured_chat_id}")

    # 3. Check who has messaged the bot
    print("\n[3] Chats that have messaged the bot:")
    updates = get_updates(token)
    if not updates:
        print("   ⚠️  No messages found.")
        print(f"   → Open Telegram, search for @{bot.get('username')},")
        print("     press Start (or send /start), then run this script again.")
        return

    chat_ids_seen = set()
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid is None or cid in chat_ids_seen:
            continue
        chat_ids_seen.add(cid)
        name = chat.get("first_name") or chat.get("title") or "?"
        chat_type = chat.get("type")
        marker = "  ← matches configured" if str(cid) == configured_chat_id else ""
        print(f"   Chat ID: {cid}  | type: {chat_type}  | name: {name}{marker}")

    # 4. Diagnosis
    print("\n" + "=" * 50)
    if configured_chat_id in {str(c) for c in chat_ids_seen}:
        print("✅ Your configured chat ID is recognized — sending should work.")
    else:
        print("❌ Configured TELEGRAM_CHAT_ID does NOT match any chat above.")
        print("   → Update .env to use one of the Chat IDs shown.")
    print("=" * 50)


if __name__ == "__main__":
    main()

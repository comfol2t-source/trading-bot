"""Send messages to Telegram via the Bot HTTP API."""
import requests

import config


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to the configured Telegram chat.

    Uses HTML parse mode by default (safer than Markdown for ticker symbols).
    Returns True on success, False on failure.
    """
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            # Print status + API response only — never the URL (it contains the token).
            print(f"Telegram send failed: HTTP {r.status_code}")
            print(f"  Response: {r.text}")
            return False
        return True
    except requests.RequestException as e:
        # Avoid printing the exception's str() — it includes the URL with token.
        print(f"Telegram request error: {type(e).__name__}")
        return False

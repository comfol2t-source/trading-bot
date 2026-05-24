"""Persistent state for the bot — JSON files in .state/ folder.

Used for:
  - Seen news IDs (avoid duplicate news pushes)
  - Active price alerts
  - Portfolio positions
  - Last Telegram update_id (for command polling)
  - Last sent runner anomaly per ticker (avoid spam)

All state is committed back to git after mutation so GitHub Actions
runs persist data across invocations.
"""
import json
from pathlib import Path
from typing import Any

STATE_DIR = Path(__file__).resolve().parent.parent / ".state"
STATE_DIR.mkdir(exist_ok=True)


def _path(name: str) -> Path:
    return STATE_DIR / f"{name}.json"


def load(name: str, default: Any) -> Any:
    p = _path(name)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def save(name: str, data: Any) -> None:
    p = _path(name)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# === Convenience wrappers ===

def get_seen_news() -> set[str]:
    return set(load("seen_news", []))


def add_seen_news(ids: list[str], max_keep: int = 500) -> None:
    seen = load("seen_news", [])
    seen.extend(ids)
    # Keep most recent N to bound file size
    seen = seen[-max_keep:]
    save("seen_news", seen)


def get_alerts() -> list[dict]:
    """Each alert: {id, ticker, op ('<=' or '>='), price, created_at}"""
    return load("alerts", [])


def save_alerts(alerts: list[dict]) -> None:
    save("alerts", alerts)


def get_portfolio() -> list[dict]:
    """Each position: {ticker, qty, entry_price, opened_at}"""
    return load("portfolio", [])


def save_portfolio(positions: list[dict]) -> None:
    save("portfolio", positions)


def get_realized() -> list[dict]:
    """Closed trades: {ticker, qty, entry, exit, pnl, closed_at}"""
    return load("realized", [])


def save_realized(trades: list[dict]) -> None:
    save("realized", trades)


def get_last_update_id() -> int:
    return int(load("last_update_id", 0))


def set_last_update_id(uid: int) -> None:
    save("last_update_id", uid)


def get_runner_cooldown() -> dict[str, str]:
    """Map ticker → ISO date string of last runner alert (avoid same-day spam)."""
    return load("runner_cooldown", {})


def save_runner_cooldown(d: dict[str, str]) -> None:
    save("runner_cooldown", d)


def get_thb_last() -> float:
    """Last USD/THB rate sent in alert (to compute delta)."""
    return float(load("thb_last", 0.0))


def set_thb_last(rate: float) -> None:
    save("thb_last", rate)

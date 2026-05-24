"""Fetch IPO, earnings, and economic calendars via Finnhub."""
from datetime import datetime, timedelta

import requests

import config

_BASE = "https://finnhub.io/api/v1"


def get_ipo_calendar(days_ahead: int = 7) -> list[dict]:
    """Upcoming US IPOs."""
    try:
        start = datetime.utcnow().date()
        end = start + timedelta(days=days_ahead)
        r = requests.get(
            f"{_BASE}/calendar/ipo",
            params={
                "from": start.isoformat(),
                "to": end.isoformat(),
                "token": config.FINNHUB_API_KEY,
            },
            timeout=10,
        )
        if r.status_code != 200:
            return []
        data = r.json() or {}
        return data.get("ipoCalendar", []) or []
    except requests.RequestException:
        return []


def get_earnings_calendar(days_ahead: int = 7, watchlist: list[str] | None = None) -> list[dict]:
    """Upcoming US earnings — optionally filtered to watchlist tickers."""
    try:
        start = datetime.utcnow().date()
        end = start + timedelta(days=days_ahead)
        r = requests.get(
            f"{_BASE}/calendar/earnings",
            params={
                "from": start.isoformat(),
                "to": end.isoformat(),
                "token": config.FINNHUB_API_KEY,
            },
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json() or {}
        items = data.get("earningsCalendar", []) or []
        if watchlist:
            wl = {t.upper() for t in watchlist}
            items = [i for i in items if i.get("symbol", "").upper() in wl]
        # Sort by date
        items.sort(key=lambda x: x.get("date", ""))
        return items
    except requests.RequestException:
        return []


def get_economic_calendar(days_ahead: int = 7) -> list[dict]:
    """Upcoming macro events (Fed, CPI, NFP, etc.).

    Note: Finnhub's economic calendar endpoint requires a paid plan,
    so this returns a placeholder. Future enhancement: scrape investing.com.
    """
    # Placeholder — Finnhub /calendar/economic is paid-only
    # User can manually add key dates here for now
    return []

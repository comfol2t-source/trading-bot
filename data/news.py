"""Fetch market news via Finnhub free API.

Supports:
  - General market news
  - Per-ticker news
  - Smart filter (only news mentioning watchlist tickers)
  - Seen-news tracking (avoid duplicates)
"""
from datetime import datetime, timedelta

import requests

import config
from bot import state

_BASE = "https://finnhub.io/api/v1"


def get_general_news(limit: int = 5) -> list[dict]:
    """Fetch top general market news (US/world)."""
    try:
        r = requests.get(
            f"{_BASE}/news",
            params={"category": "general", "token": config.FINNHUB_API_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        return (r.json() or [])[:limit]
    except requests.RequestException:
        return []


def get_company_news(ticker: str, days_back: int = 3, limit: int = 2) -> list[dict]:
    """Fetch recent news for a specific US ticker."""
    try:
        end = datetime.utcnow().date()
        start = end - timedelta(days=days_back)
        r = requests.get(
            f"{_BASE}/company-news",
            params={
                "symbol": ticker,
                "from": start.isoformat(),
                "to": end.isoformat(),
                "token": config.FINNHUB_API_KEY,
            },
            timeout=10,
        )
        if r.status_code != 200:
            return []
        return (r.json() or [])[:limit]
    except requests.RequestException:
        return []


def get_fresh_news(limit: int = 5) -> list[dict]:
    """Get general news, skipping any we've already pushed to Telegram."""
    seen = state.get_seen_news()
    fresh = []
    for item in get_general_news(limit=20):
        nid = str(item.get("id") or item.get("url") or "")
        if not nid or nid in seen:
            continue
        fresh.append(item)
        if len(fresh) >= limit:
            break

    # Mark as seen
    if fresh:
        state.add_seen_news([str(i.get("id") or i.get("url") or "") for i in fresh])
    return fresh


def filter_watchlist_news(news: list[dict], tickers: list[str]) -> list[dict]:
    """Keep only news mentioning any watchlist ticker in headline/summary."""
    if not tickers:
        return news
    keep = []
    upper_tickers = {t.upper().replace(".BK", "").replace("-USD", "") for t in tickers}
    for item in news:
        text = (item.get("headline", "") + " " + item.get("summary", "")).upper()
        if any(t in text for t in upper_tickers if len(t) >= 3):
            keep.append(item)
    return keep

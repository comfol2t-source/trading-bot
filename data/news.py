"""Fetch market news via Finnhub free API."""
from datetime import datetime, timedelta
from typing import Optional

import requests

import config


_BASE = "https://finnhub.io/api/v1"


def get_general_news(limit: int = 5) -> list[dict]:
    """Fetch top general market news.

    Returns list of dicts with: headline, source, url, datetime (unix), summary.
    """
    try:
        r = requests.get(
            f"{_BASE}/news",
            params={"category": "general", "token": config.FINNHUB_API_KEY},
            timeout=10,
        )
        if r.status_code != 200:
            print(f"  ! Finnhub news HTTP {r.status_code}")
            return []
        items = r.json() or []
        return items[:limit]
    except requests.RequestException as e:
        print(f"  ! Finnhub news error: {type(e).__name__}")
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
        items = r.json() or []
        return items[:limit]
    except requests.RequestException:
        return []

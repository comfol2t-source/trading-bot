"""Fetch price data via yfinance with history + volume context."""
from typing import Optional

import yfinance as yf


def fetch_price(ticker: str) -> Optional[dict]:
    """Fetch enriched price data for a ticker.

    Returns dict with:
        ticker, price, prev_close, currency,
        change_pct (1D), change_5d_pct, change_30d_pct,
        volume, avg_volume_20d, volume_spike (x times avg)
    Returns None if essential data is missing.
    """
    try:
        t = yf.Ticker(ticker)

        # 35 days gives us ~22 trading days + buffer for 30-day calc.
        hist = t.history(period="60d", auto_adjust=False)
        if hist.empty:
            return None

        closes = hist["Close"].dropna()
        volumes = hist["Volume"].dropna()
        if len(closes) < 2:
            return None

        price = float(closes.iloc[-1])
        prev_close = float(closes.iloc[-2])
        if prev_close == 0:
            return None
        change_pct = (price - prev_close) / prev_close * 100

        # 5-day change: vs close ~5 trading days ago
        change_5d_pct = None
        if len(closes) >= 6:
            ref = float(closes.iloc[-6])
            if ref:
                change_5d_pct = (price - ref) / ref * 100

        # 30-day change: vs close ~22 trading days ago (1 month)
        change_30d_pct = None
        if len(closes) >= 23:
            ref = float(closes.iloc[-23])
            if ref:
                change_30d_pct = (price - ref) / ref * 100

        # Volume stats
        volume = float(volumes.iloc[-1]) if len(volumes) else 0.0
        avg_volume_20d = float(volumes.iloc[-21:-1].mean()) if len(volumes) >= 21 else 0.0
        volume_spike = (volume / avg_volume_20d) if avg_volume_20d > 0 else 0.0

        # Currency via fast_info (cheap)
        try:
            currency = t.fast_info.currency or "USD"
        except Exception:
            currency = "USD"

        return {
            "ticker": ticker,
            "price": price,
            "prev_close": prev_close,
            "currency": currency,
            "change_pct": change_pct,
            "change_5d_pct": change_5d_pct,
            "change_30d_pct": change_30d_pct,
            "volume": volume,
            "avg_volume_20d": avg_volume_20d,
            "volume_spike": volume_spike,
        }
    except Exception as e:
        print(f"  ! Failed to fetch {ticker}: {e}")
        return None


def fetch_multiple(tickers: list[str]) -> list[dict]:
    """Fetch prices for multiple tickers; skip failures."""
    out = []
    for ticker in tickers:
        d = fetch_price(ticker)
        if d is not None:
            out.append(d)
    return out

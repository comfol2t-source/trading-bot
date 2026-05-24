"""Sector heat map — aggregate average % change per theme."""
import config


def compute_heat(data_by_ticker: dict[str, dict], themes: dict[str, list[str]]) -> list[dict]:
    """Return list of {theme, avg_pct, count, emoji} sorted by avg_pct desc."""
    rows = []
    for theme, tickers in themes.items():
        items = [data_by_ticker[t] for t in tickers if t in data_by_ticker]
        if not items:
            continue
        valid = [d for d in items if d.get("change_pct") is not None]
        if not valid:
            continue
        avg = sum(d["change_pct"] for d in valid) / len(valid)
        rows.append({
            "theme": theme,
            "avg_pct": avg,
            "count": len(valid),
            "emoji": _heat_emoji(avg),
        })
    rows.sort(key=lambda r: r["avg_pct"], reverse=True)
    return rows


def _heat_emoji(pct: float) -> str:
    if pct >= 5:
        return "🟢🟢🟢"
    if pct >= 2:
        return "🟢🟢"
    if pct >= 0.5:
        return "🟢"
    if pct >= -0.5:
        return "⚪"
    if pct >= -2:
        return "🔴"
    if pct >= -5:
        return "🔴🔴"
    return "🔴🔴🔴"

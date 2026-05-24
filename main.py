"""Phase 1.5: Enhanced market brief with themes, top movers, anomalies, news.

Run with:
    python main.py
"""
import html
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Force UTF-8 console output for Windows Thai locale (CP874).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import config
from analysis.anomaly import find_anomalies, top_movers
from bot.telegram_sender import send_message
from data.news import get_general_news
from data.prices import fetch_multiple


# ---------- Formatting helpers ----------

def _clean_name(ticker: str) -> str:
    return (
        ticker.replace(".BK", "")
        .replace("=F", "")
        .replace("=X", "")
        .replace("^", "")
        .replace("-Y.NYB", "")
    )


def _arrow(pct: float | None) -> str:
    if pct is None:
        return "⚪"
    if pct > 0:
        return "🟢"
    if pct < 0:
        return "🔴"
    return "⚪"


def _pct(pct: float | None) -> str:
    if pct is None:
        return "  n/a "
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.2f}%"


def format_ticker_full(d: dict) -> str:
    """Full line: ticker | price | 1D | 5D | 30D."""
    name = html.escape(_clean_name(d["ticker"]))
    arrow = _arrow(d.get("change_pct"))
    return (
        f'{arrow} <code>{name:<8}</code> '
        f'{d["price"]:>10,.2f}  '
        f'<b>{_pct(d.get("change_pct")):>8}</b>  '
        f'5D {_pct(d.get("change_5d_pct")):>8}  '
        f'30D {_pct(d.get("change_30d_pct")):>8}'
    )


def format_ticker_compact(d: dict) -> str:
    """Compact one-liner: ticker price 1D%."""
    name = html.escape(_clean_name(d["ticker"]))
    arrow = _arrow(d.get("change_pct"))
    return (
        f'{arrow} <code>{name:<8}</code> '
        f'{d["price"]:>10,.2f}  '
        f'{_pct(d.get("change_pct"))}'
    )


# ---------- Section builders ----------

def section_macro(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["🌎 <b>Macro</b>"]
    lines.extend(format_ticker_compact(d) for d in items)
    return lines + [""]


def section_gold_fx(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["🥇 <b>Gold &amp; FX</b>"]
    lines.extend(format_ticker_compact(d) for d in items)
    return lines + [""]


def section_themed(title: str, themes: dict[str, list[str]],
                   data_by_ticker: dict[str, dict]) -> list[str]:
    """Render a watchlist grouped by theme."""
    lines = [f"<b>{title}</b>"]
    for theme, tickers in themes.items():
        items = [data_by_ticker[t] for t in tickers if t in data_by_ticker]
        if not items:
            continue
        lines.append(f"<i>— {html.escape(theme)} —</i>")
        lines.extend(format_ticker_full(d) for d in items)
    return lines + [""]


def section_top_movers(items: list[dict], n: int) -> list[str]:
    gainers, losers = top_movers(items, n)
    lines = ["🔥 <b>Top Movers (1D)</b>"]
    if gainers:
        lines.append("📈 <i>Gainers</i>")
        lines.extend(format_ticker_compact(d) for d in gainers)
    if losers:
        lines.append("📉 <i>Losers</i>")
        lines.extend(format_ticker_compact(d) for d in losers)
    return lines + [""]


def section_anomalies(items: list[dict]) -> list[str]:
    anoms = find_anomalies(items)
    if not anoms:
        return []
    lines = ["⚠️ <b>Anomalies</b> <i>(unusual moves)</i>"]
    for d, reasons in anoms:
        name = html.escape(_clean_name(d["ticker"]))
        reason_str = " + ".join(reasons)
        arrow = _arrow(d.get("change_pct"))
        lines.append(
            f'{arrow} <code>{name:<8}</code> '
            f'{d["price"]:>10,.2f}  '
            f'<i>{reason_str}</i>'
        )
    return lines + [""]


def section_news(news: list[dict]) -> list[str]:
    if not news:
        return []
    lines = ["📰 <b>Market News</b>"]
    for item in news:
        headline = html.escape(item.get("headline", "")[:120])
        source = html.escape(item.get("source", ""))
        url = item.get("url", "")
        if url:
            lines.append(f'• <a href="{html.escape(url, quote=True)}">{headline}</a> <i>({source})</i>')
        else:
            lines.append(f"• {headline} <i>({source})</i>")
    return lines + [""]


# ---------- Main ----------

def build_brief() -> str:
    now = datetime.now(ZoneInfo("Asia/Bangkok"))
    lines = [
        "📊 <b>Market Brief</b>",
        f"<i>{now.strftime('%d %b %Y, %H:%M')} (Bangkok)</i>",
        "",
    ]

    print("→ Fetching macro...")
    macro = fetch_multiple(config.MACRO)

    print("→ Fetching gold & FX...")
    gold_fx = fetch_multiple(config.GOLD_FX)

    print("→ Fetching US watchlist...")
    us = fetch_multiple(config.US_WATCHLIST)

    print("→ Fetching Thai watchlist...")
    th = fetch_multiple(config.THAI_WATCHLIST)

    print("→ Fetching news...")
    news = get_general_news(config.NEWS_COUNT)

    # Build maps for theme rendering
    us_by_ticker = {d["ticker"]: d for d in us}
    th_by_ticker = {d["ticker"]: d for d in th}

    # All equities (US + Thai) for movers + anomalies
    all_equities = us + th

    # Compose sections
    lines += section_macro(macro)
    lines += section_gold_fx(gold_fx)
    lines += section_top_movers(all_equities, config.TOP_MOVERS_COUNT)
    lines += section_anomalies(all_equities)
    lines += section_themed("🇺🇸 US Watchlist", config.US_THEMES, us_by_ticker)
    lines += section_themed("🇹🇭 Thai Watchlist", config.THAI_THEMES, th_by_ticker)
    lines += section_news(news)

    return "\n".join(lines)


def main():
    config.validate()
    print("Building market brief...\n")
    msg = build_brief()

    print("\n--- Preview (first 1500 chars) ---")
    print(msg[:1500])
    if len(msg) > 1500:
        print(f"... (+{len(msg) - 1500} more chars)")
    print("--- End preview ---\n")

    # Telegram limit is 4096 chars per message; split if needed.
    print(f"Total message length: {len(msg)} chars")
    print("Sending to Telegram...")

    if len(msg) <= 4000:
        ok = send_message(msg)
    else:
        # Split on blank lines so sections stay intact
        chunks = []
        current = []
        current_len = 0
        for line in msg.split("\n"):
            if current_len + len(line) + 1 > 3800 and current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            current.append(line)
            current_len += len(line) + 1
        if current:
            chunks.append("\n".join(current))
        print(f"Splitting into {len(chunks)} messages...")
        ok = all(send_message(c) for c in chunks)

    if ok:
        print("✅ Sent successfully — check your Telegram!")
    else:
        print("❌ Send failed — see error above.")


if __name__ == "__main__":
    main()

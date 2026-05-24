"""Brief formatters — convert price data + analysis into Telegram-ready HTML."""
import html
from datetime import datetime
from zoneinfo import ZoneInfo

import config
from analysis.anomaly import find_anomalies, top_movers
from analysis.heatmap import compute_heat
from data.news import filter_watchlist_news, get_fresh_news, get_general_news
from data.prices import fetch_multiple

ICT = ZoneInfo("Asia/Bangkok")


# ---------- Formatting helpers ----------

def _clean_name(ticker: str) -> str:
    return (
        ticker.replace(".BK", "")
        .replace("=F", "")
        .replace("=X", "")
        .replace("^", "")
        .replace("-Y.NYB", "")
        .replace("-USD", "")
    )


def _runner_tag(ticker: str) -> str:
    """Return 🚀 if ticker is a runner, else empty."""
    return "🚀" if config.is_runner(ticker) else ""


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


def format_full(d: dict) -> str:
    """Full line: ticker + runner tag + price + 1D/5D/30D."""
    name = html.escape(_clean_name(d["ticker"]))
    tag = _runner_tag(d["ticker"])
    arrow = _arrow(d.get("change_pct"))
    return (
        f'{arrow} <code>{name:<8}</code>{tag} '
        f'{d["price"]:>10,.2f}  '
        f'<b>{_pct(d.get("change_pct")):>8}</b>  '
        f'5D {_pct(d.get("change_5d_pct")):>8}  '
        f'30D {_pct(d.get("change_30d_pct")):>8}'
    )


def format_compact(d: dict) -> str:
    """Compact: ticker + runner tag + price + 1D."""
    name = html.escape(_clean_name(d["ticker"]))
    tag = _runner_tag(d["ticker"])
    arrow = _arrow(d.get("change_pct"))
    return (
        f'{arrow} <code>{name:<8}</code>{tag} '
        f'{d["price"]:>10,.2f}  '
        f'{_pct(d.get("change_pct"))}'
    )


# ---------- Section builders ----------

def section_macro(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["🌎 <b>Macro</b>"]
    lines.extend(format_compact(d) for d in items)
    return lines + [""]


def section_gold(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["🥇 <b>Gold</b>"]
    lines.extend(format_compact(d) for d in items)
    return lines + [""]


def section_currencies(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["💱 <b>Currencies</b>"]
    lines.extend(format_compact(d) for d in items)
    return lines + [""]


# Backwards-compat alias (combined render)
def section_gold_fx(items: list[dict]) -> list[str]:
    if not items:
        return []
    lines = ["💱 <b>Currencies &amp; Gold</b>"]
    lines.extend(format_compact(d) for d in items)
    return lines + [""]


def section_themed(title: str, themes: dict[str, list[str]],
                   data_by_ticker: dict[str, dict],
                   compact: bool = False) -> list[str]:
    fmt = format_compact if compact else format_full
    lines = [f"<b>{title}</b>"]
    for theme, tickers in themes.items():
        items = [data_by_ticker[t] for t in tickers if t in data_by_ticker]
        if not items:
            continue
        lines.append(f"<i>— {html.escape(theme)} —</i>")
        lines.extend(fmt(d) for d in items)
    return lines + [""]


def section_top_movers(items: list[dict], n: int) -> list[str]:
    gainers, losers = top_movers(items, n)
    lines = ["🔥 <b>Top Movers (1D)</b>"]
    if gainers:
        lines.append("📈 <i>Gainers</i>")
        lines.extend(format_compact(d) for d in gainers)
    if losers:
        lines.append("📉 <i>Losers</i>")
        lines.extend(format_compact(d) for d in losers)
    return lines + [""]


def section_anomalies(items: list[dict]) -> list[str]:
    anoms = find_anomalies(items)
    if not anoms:
        return []
    lines = ["⚠️ <b>Anomalies</b> <i>(unusual moves)</i>"]
    for d, reasons in anoms:
        name = html.escape(_clean_name(d["ticker"]))
        tag = _runner_tag(d["ticker"])
        reason_str = " + ".join(reasons)
        arrow = _arrow(d.get("change_pct"))
        lines.append(
            f'{arrow} <code>{name:<8}</code>{tag} '
            f'{d["price"]:>10,.2f}  '
            f'<i>{reason_str}</i>'
        )
    return lines + [""]


def section_heat(data_by_ticker: dict[str, dict],
                 us_themes: dict, th_themes: dict) -> list[str]:
    """Sector heat map across US + Thai themes."""
    rows_us = compute_heat(data_by_ticker, us_themes)
    rows_th = compute_heat(data_by_ticker, th_themes)
    lines = ["🔥 <b>Sector Heat</b>"]
    for r in rows_us + rows_th:
        theme = html.escape(r["theme"])
        sign = "+" if r["avg_pct"] >= 0 else ""
        lines.append(
            f'{r["emoji"]} <code>{theme[:20]:<20}</code> '
            f'{sign}{r["avg_pct"]:.2f}% avg'
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
            lines.append(
                f'• <a href="{html.escape(url, quote=True)}">{headline}</a> '
                f'<i>({source})</i>'
            )
        else:
            lines.append(f"• {headline} <i>({source})</i>")
    return lines + [""]


# ---------- Top-level brief builders ----------

def _header(title: str) -> list[str]:
    now = datetime.now(ICT)
    return [
        f"📊 <b>{title}</b>",
        f"<i>{now.strftime('%a %d %b, %H:%M')} (Bangkok)</i>",
        "",
    ]


def build_full_brief() -> str:
    """Long-form 4x/day brief — all sections."""
    lines = _header("Market Brief — Full")

    macro = fetch_multiple(config.MACRO)
    gold = fetch_multiple(config.GOLD)
    currencies = fetch_multiple(config.CURRENCIES)
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    crypto = fetch_multiple(config.CRYPTO_SPOT)

    us_map = {d["ticker"]: d for d in us}
    th_map = {d["ticker"]: d for d in th}
    all_equities = us + th
    all_data = {**us_map, **th_map, **{d["ticker"]: d for d in crypto}}

    # All US watchlist + Thai for filtering news
    watchlist_for_news = config.US_WATCHLIST + config.THAI_WATCHLIST
    general = get_fresh_news(15)
    relevant_news = filter_watchlist_news(general, watchlist_for_news)
    news = relevant_news[:config.NEWS_COUNT] if relevant_news else general[:config.NEWS_COUNT]

    lines += section_macro(macro)
    lines += section_gold(gold)
    lines += section_currencies(currencies)
    if crypto:
        lines.append("🪙 <b>Crypto Spot</b>")
        lines.extend(format_compact(d) for d in crypto)
        lines.append("")
    lines += section_heat(all_data, config.US_THEMES, config.THAI_THEMES)
    lines += section_top_movers(all_equities, config.TOP_MOVERS_COUNT)
    lines += section_anomalies(all_equities)
    lines += section_themed("🇺🇸 US Watchlist", config.US_THEMES, us_map)
    lines += section_themed("🇹🇭 Thai Watchlist", config.THAI_THEMES, th_map)
    lines += section_news(news)

    return "\n".join(lines)


def build_hourly_brief() -> str:
    """Compact hourly brief — macro + top movers + key themes."""
    lines = _header("Market Pulse — Hourly")

    macro = fetch_multiple(config.MACRO)
    gold = fetch_multiple(config.GOLD)
    currencies = fetch_multiple(config.CURRENCIES)
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)

    all_equities = us + th

    lines += section_macro(macro)
    lines += section_gold(gold)
    lines += section_currencies(currencies)
    lines += section_top_movers(all_equities, config.TOP_MOVERS_COUNT)
    lines += section_anomalies(all_equities)

    return "\n".join(lines)


def build_tenmin_brief() -> str:
    """Pre/post market 10-min brief — top movers + anomalies only (fast)."""
    lines = _header("Market Snap — 10-min")

    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    all_equities = us + th

    lines += section_top_movers(all_equities, 5)
    lines += section_anomalies(all_equities)

    return "\n".join(lines)


def build_news_only() -> str:
    """News-only brief (manual command)."""
    lines = _header("News Brief")
    watchlist = config.US_WATCHLIST + config.THAI_WATCHLIST
    general = get_general_news(15)
    relevant = filter_watchlist_news(general, watchlist)
    news = relevant[:config.NEWS_COUNT] if relevant else general[:config.NEWS_COUNT]
    lines += section_news(news)
    return "\n".join(lines)


def build_runner_only() -> str:
    """Runner-focused brief."""
    lines = _header("Runner Watch")
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    all_equities = us + th
    lines += section_top_movers(all_equities, 5)
    lines += section_anomalies(all_equities)
    return "\n".join(lines)


def build_heat_only() -> str:
    lines = _header("Sector Heat Map")
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    data = {**{d["ticker"]: d for d in us}, **{d["ticker"]: d for d in th}}
    lines += section_heat(data, config.US_THEMES, config.THAI_THEMES)
    return "\n".join(lines)


def build_macro_only() -> str:
    lines = _header("Macro + Gold + Currencies")
    lines += section_macro(fetch_multiple(config.MACRO))
    lines += section_gold(fetch_multiple(config.GOLD))
    lines += section_currencies(fetch_multiple(config.CURRENCIES))
    crypto = fetch_multiple(config.CRYPTO_SPOT)
    if crypto:
        lines.append("🪙 <b>Crypto Spot</b>")
        lines.extend(format_compact(d) for d in crypto)
        lines.append("")
    return "\n".join(lines)


def build_thai_only() -> str:
    lines = _header("Thai Watchlist")
    th = fetch_multiple(config.THAI_WATCHLIST)
    th_map = {d["ticker"]: d for d in th}
    lines += section_themed("🇹🇭 Thai", config.THAI_THEMES, th_map)
    return "\n".join(lines)


def build_us_only() -> str:
    lines = _header("US Watchlist")
    us = fetch_multiple(config.US_WATCHLIST)
    us_map = {d["ticker"]: d for d in us}
    lines += section_themed("🇺🇸 US", config.US_THEMES, us_map)
    return "\n".join(lines)

"""Command router for the interactive Telegram bot.

Supports both plain text ("update") and slash commands ("/update").
"""
import html
from datetime import datetime, timezone

from analysis import portfolio, position_sizing
from analysis.alerts import check_price_alerts
from bot import briefs, state
from data.calendars import get_earnings_calendar, get_ipo_calendar
from data.prices import fetch_price


HELP_TEXT = """🤖 <b>Trading Bot Commands</b>

<b>📊 Briefs (พิมพ์ตรงๆ หรือใส่ / ได้)</b>
• <code>update</code> / <code>full</code> — Market brief เต็ม
• <code>hourly</code> — สรุปสั้นๆ
• <code>news</code> — ข่าวล่าสุด
• <code>runner</code> — ตัวซิ่งของวัน
• <code>macro</code> — Macro + Gold + FX + Crypto spot
• <code>thai</code> — Thai watchlist
• <code>us</code> — US watchlist
• <code>heat</code> — Sector heat map

<b>📅 Calendars</b>
• <code>ipo</code> — IPO calendar 7 วัน
• <code>earnings</code> — Earnings 7 วัน (watchlist)

<b>💰 Price Alerts</b>
• <code>alert add NVDA &lt;= 200</code>
• <code>alert add KBANK &gt;= 150</code>
• <code>alert list</code>
• <code>alert remove 1</code>

<b>💼 Portfolio</b>
• <code>buy KBANK 1000 145.50</code>
• <code>sell KBANK 500 152.00</code>
• <code>portfolio</code> / <code>pf</code>

<b>🎯 Position Size</b>
• <code>size NVDA 215 200 100000 2</code>
  <i>(entry, stop, budget, risk%)</i>

• <code>help</code> — แสดงรายการนี้
"""


def _normalize(text: str) -> str:
    return text.strip().lower().lstrip("/")


def route(text: str) -> str:
    """Dispatch a single user message to the right handler.
    Returns reply text (HTML)."""
    text = text.strip()
    if not text:
        return "ลองพิมพ์ <code>help</code> ดูคำสั่งทั้งหมด"

    parts = text.split()
    cmd = _normalize(parts[0])
    args = parts[1:]

    try:
        # Briefs
        if cmd in ("update", "full"):
            return briefs.build_full_brief()
        if cmd in ("hourly", "pulse"):
            return briefs.build_hourly_brief()
        if cmd == "news":
            return briefs.build_news_only()
        if cmd in ("runner", "runners"):
            return briefs.build_runner_only()
        if cmd == "macro":
            return briefs.build_macro_only()
        if cmd in ("thai", "th"):
            return briefs.build_thai_only()
        if cmd == "us":
            return briefs.build_us_only()
        if cmd == "heat":
            return briefs.build_heat_only()

        # Calendars
        if cmd == "ipo":
            return _ipo()
        if cmd == "earnings":
            return _earnings()

        # Alerts
        if cmd == "alert":
            return _alert(args)

        # Portfolio
        if cmd == "buy":
            return _buy(args)
        if cmd == "sell":
            return _sell(args)
        if cmd in ("portfolio", "pf"):
            return _portfolio()

        # Position size
        if cmd == "size":
            return _size(args)

        # Help
        if cmd in ("help", "h", "?", "start"):
            return HELP_TEXT

        # Try as bare ticker (e.g. "NVDA" or "KBANK")
        if cmd.isalpha() and 1 < len(cmd) <= 6:
            return _ticker(cmd.upper())

    except Exception as e:
        return f"❌ Error: <code>{html.escape(str(e))}</code>"

    return f"❓ ไม่รู้จักคำสั่ง <code>{html.escape(text[:50])}</code>\nพิมพ์ <code>help</code> ดูคำสั่งทั้งหมด"


# ---------- Handlers ----------

def _ticker(t: str) -> str:
    # Try both bare and .BK
    for try_t in (t, f"{t}.BK"):
        d = fetch_price(try_t)
        if d:
            from bot.briefs import format_full
            return f"📊 <b>{html.escape(try_t)}</b>\n{format_full(d)}"
    return f"❓ ไม่พบ ticker <code>{html.escape(t)}</code>"


def _ipo() -> str:
    """IPO calendar — split into 7d / 8-15d / 16-30d sections."""
    from datetime import datetime, timedelta
    items = get_ipo_calendar(30)
    if not items:
        return "📅 ไม่มี IPO ใน 30 วันข้างหน้า"

    today = datetime.utcnow().date()
    bucket_7 = []
    bucket_15 = []
    bucket_30 = []
    for i in items:
        try:
            d = datetime.fromisoformat(i.get("date", "")).date()
        except ValueError:
            continue
        days = (d - today).days
        if days <= 7:
            bucket_7.append(i)
        elif days <= 15:
            bucket_15.append(i)
        elif days <= 30:
            bucket_30.append(i)

    def fmt(group: list) -> list[str]:
        out = []
        for i in group[:10]:
            date = i.get("date", "")
            sym = html.escape(i.get("symbol", "") or "—")
            name = html.escape((i.get("name", "") or "")[:45])
            price = i.get("price", "") or "TBD"
            shares = i.get("numberOfShares", "")
            shares_str = f", {int(shares):,} shares" if shares else ""
            out.append(f"• <code>{date}</code> <b>{sym}</b> — {name} <i>(${price}{shares_str})</i>")
        return out

    lines = ["📅 <b>IPO Calendar</b>"]
    lines.append(f"\n🔥 <b>This week (≤ 7 days)</b> — {len(bucket_7)}")
    lines.extend(fmt(bucket_7) if bucket_7 else ["<i>(none)</i>"])
    lines.append(f"\n📆 <b>Next 8–15 days</b> — {len(bucket_15)}")
    lines.extend(fmt(bucket_15) if bucket_15 else ["<i>(none)</i>"])
    lines.append(f"\n🗓 <b>16–30 days</b> — {len(bucket_30)}")
    lines.extend(fmt(bucket_30) if bucket_30 else ["<i>(none)</i>"])
    return "\n".join(lines)


def _earnings() -> str:
    import config
    items = get_earnings_calendar(7, watchlist=config.US_WATCHLIST)
    if not items:
        return "📅 ไม่มี earnings ของ watchlist ใน 7 วันข้างหน้า"
    lines = ["📅 <b>Earnings — 7 days (watchlist)</b>"]
    for i in items[:20]:
        date = i.get("date", "")
        sym = html.escape(i.get("symbol", ""))
        eps_est = i.get("epsEstimate", "?")
        when = i.get("hour", "")
        lines.append(f"• <code>{date}</code> {sym} EPS est: ${eps_est} <i>({when})</i>")
    return "\n".join(lines)


def _alert(args: list[str]) -> str:
    if not args:
        return "ใช้: <code>alert add TICKER &lt;= PRICE</code> หรือ <code>alert list</code>"

    sub = args[0].lower()
    if sub == "list":
        alerts = state.get_alerts()
        if not alerts:
            return "🔕 ยังไม่มี alert"
        lines = ["🔔 <b>Active alerts</b>"]
        for a in alerts:
            lines.append(f'• #{a["id"]} {html.escape(a["ticker"])} {a["op"]} {a["price"]}')
        return "\n".join(lines)

    if sub == "remove" and len(args) >= 2:
        try:
            aid = int(args[1])
        except ValueError:
            return "❌ ID ต้องเป็นตัวเลข"
        alerts = state.get_alerts()
        new_alerts = [a for a in alerts if a["id"] != aid]
        if len(new_alerts) == len(alerts):
            return f"❓ ไม่พบ alert #{aid}"
        state.save_alerts(new_alerts)
        return f"✅ ลบ alert #{aid} แล้ว"

    if sub == "add" and len(args) >= 4:
        ticker = args[1].upper()
        op = args[2]
        try:
            price = float(args[3])
        except ValueError:
            return "❌ ราคาต้องเป็นตัวเลข"
        if op not in ("<=", ">="):
            return "❌ ใช้ &lt;= หรือ &gt;= เท่านั้น"
        alerts = state.get_alerts()
        next_id = (max((a["id"] for a in alerts), default=0)) + 1
        alerts.append({
            "id": next_id,
            "ticker": ticker,
            "op": op,
            "price": price,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        state.save_alerts(alerts)
        return f"✅ Alert #{next_id} ตั้งแล้ว: {ticker} {op} {price}"

    return "ใช้: <code>alert add TICKER &lt;= PRICE</code> | <code>alert list</code> | <code>alert remove N</code>"


def _buy(args: list[str]) -> str:
    if len(args) < 3:
        return "ใช้: <code>buy TICKER QTY PRICE</code>"
    try:
        ticker = args[0].upper()
        qty = float(args[1])
        price = float(args[2])
    except ValueError:
        return "❌ QTY และ PRICE ต้องเป็นตัวเลข"
    p = portfolio.add_position(ticker, qty, price)
    return (
        f"✅ บันทึก buy: <b>{ticker}</b> {qty:g} @ {price:,.2f}\n"
        f"ตำแหน่งปัจจุบัน: {p['qty']:g} หุ้น avg {p['entry_price']:,.2f}"
    )


def _sell(args: list[str]) -> str:
    if len(args) < 3:
        return "ใช้: <code>sell TICKER QTY PRICE</code>"
    try:
        ticker = args[0].upper()
        qty = float(args[1])
        price = float(args[2])
    except ValueError:
        return "❌ QTY และ PRICE ต้องเป็นตัวเลข"
    trade = portfolio.close_position(ticker, qty, price)
    if trade is None:
        return f"❓ ไม่มีตำแหน่ง {ticker} ในพอร์ต"
    pnl_emoji = "🟢" if trade["pnl"] >= 0 else "🔴"
    return (
        f"✅ บันทึก sell: <b>{ticker}</b> {trade['qty']:g} @ {price:,.2f}\n"
        f"{pnl_emoji} P/L: <b>{trade['pnl']:+,.2f}</b>"
    )


def _portfolio() -> str:
    snap = portfolio.snapshot()
    if not snap["positions"] and not snap["realized"]:
        return "💼 พอร์ตว่างเปล่า — ลอง <code>buy KBANK 100 145</code>"
    lines = ["💼 <b>Portfolio</b>"]
    if snap["positions"]:
        lines.append("📈 <i>Open positions</i>")
        for p in snap["positions"]:
            pnl_emoji = "🟢" if p["pnl"] >= 0 else "🔴"
            lines.append(
                f'{pnl_emoji} <code>{html.escape(p["ticker"]):<8}</code> '
                f'{p["qty"]:g} @ {p["entry_price"]:,.2f} '
                f'→ {p["current_price"]:,.2f} '
                f'<b>{p["pnl"]:+,.2f}</b> ({p["pnl_pct"]:+.1f}%)'
            )
        lines.append("")
        lines.append(
            f'💰 Invested: {snap["total_invested"]:,.2f}\n'
            f'🎯 Current:  {snap["total_current"]:,.2f}\n'
            f'📊 Open P/L: <b>{snap["total_pnl"]:+,.2f}</b> '
            f'({snap["total_pnl_pct"]:+.2f}%)'
        )
    if snap["realized"]:
        lines.append("")
        lines.append("📜 <i>Recent realized (last 5)</i>")
        for t in snap["realized"][-5:]:
            emoji = "🟢" if t["pnl"] >= 0 else "🔴"
            lines.append(
                f'{emoji} <code>{html.escape(t["ticker"])}</code> '
                f'{t["qty"]:g} @ {t["entry"]:,.2f} → {t["exit"]:,.2f} '
                f'<b>{t["pnl"]:+,.2f}</b>'
            )
    return "\n".join(lines)


def _size(args: list[str]) -> str:
    if len(args) < 4:
        return "ใช้: <code>size TICKER ENTRY STOP BUDGET RISK%</code>"
    try:
        ticker = args[0].upper() if len(args) >= 5 else "—"
        if len(args) >= 5:
            entry = float(args[1])
            stop = float(args[2])
            budget = float(args[3])
            risk_pct = float(args[4])
        else:
            entry = float(args[0])
            stop = float(args[1])
            budget = float(args[2])
            risk_pct = float(args[3])
            ticker = "—"
    except ValueError:
        return "❌ ใส่เป็นตัวเลขทั้งหมด"

    r = position_sizing.calculate(entry, stop, budget, risk_pct)
    if "error" in r:
        return f"❌ {r['error']}"
    return (
        f"🎯 <b>Position Size</b> — {html.escape(ticker)}\n"
        f"Entry: {entry:,.2f} | Stop: {stop:,.2f} ({r['direction']})\n"
        f"Risk per share: {r['risk_per_share']:,.2f}\n"
        f"\n"
        f"→ ซื้อได้ <b>{r['shares']:,}</b> หุ้น\n"
        f"→ มูลค่า: {r['position_value']:,.2f} ({r['capital_pct']:.1f}% ของทุน)\n"
        f"→ ถ้า SL โดน: -{r['max_loss']:,.2f}"
    )

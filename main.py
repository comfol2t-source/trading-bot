"""Trading bot entry point.

Usage:
    python main.py auto       # smart cadence — used by GitHub Actions
    python main.py full       # full brief now
    python main.py hourly     # compact hourly brief
    python main.py tenmin     # 10-min interval brief
    python main.py alert      # alert check only
    python main.py command    # poll Telegram commands
    python main.py news       # news only
    python main.py runner     # runner check only
    python main.py weekly     # weekly recap
    python main.py heat       # sector heat map
    python main.py macro      # macro + gold + FX
    python main.py thai       # thai watchlist
    python main.py us         # us watchlist
"""
import html
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Force UTF-8 console output for Windows Thai locale (CP874).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import config
from analysis.alerts import (
    check_price_alerts, check_runners, check_thb_move, check_vix_panic,
)
from analysis.scheduler_logic import pick_jobs
from bot import briefs, listener
from bot.telegram_sender import send_message
from data.prices import fetch_multiple


ICT = ZoneInfo("Asia/Bangkok")


def _send_chunks(text: str) -> bool:
    if len(text) <= 4000:
        return send_message(text)
    ok = True
    chunks = []
    current = []
    cur_len = 0
    for line in text.split("\n"):
        if cur_len + len(line) + 1 > 3800 and current:
            chunks.append("\n".join(current))
            current = []
            cur_len = 0
        current.append(line)
        cur_len += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    for c in chunks:
        ok = send_message(c) and ok
    return ok


# ---------- Job handlers ----------

def job_full_brief():
    print("→ Job: full_brief")
    _send_chunks(briefs.build_full_brief())


def job_hourly_brief():
    print("→ Job: hourly_brief")
    _send_chunks(briefs.build_hourly_brief())


def job_tenmin_brief():
    print("→ Job: tenmin_brief")
    _send_chunks(briefs.build_tenmin_brief())


def job_news():
    print("→ Job: news")
    _send_chunks(briefs.build_news_only())


def job_runner():
    print("→ Job: runner")
    _send_chunks(briefs.build_runner_only())


def job_alert_check():
    """Check runner / price / THB / VIX alerts and push if triggered."""
    print("→ Job: alert_check")
    # Fetch a pool of prices once
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    macro = fetch_multiple(["^VIX", "THB=X"])
    all_eq = us + th
    prices_map = {d["ticker"]: d for d in all_eq + macro}

    # 1. Runner alerts
    runners = check_runners(all_eq)
    for r in runners:
        name = html.escape(r["ticker"].replace(".BK", ""))
        tag = "🚀" if config.is_runner(r["ticker"]) else ""
        msg = (
            f"🚨 <b>RUNNER ALERT</b> {tag}\n"
            f"<code>{name}</code> {r['price']:,.2f}\n"
            f"<i>{' + '.join(r['reasons'])}</i>"
        )
        send_message(msg)

    # 2. Price alerts (user-defined)
    triggered = check_price_alerts(prices_map)
    for a in triggered:
        msg = (
            f"💰 <b>PRICE ALERT</b>\n"
            f"<code>{html.escape(a['ticker'])}</code> "
            f"hit {a['op']} {a['price']:,.2f}\n"
            f"Current: {a['current_price']:,.2f}"
        )
        send_message(msg)

    # 3. USD/THB alert
    thb = check_thb_move()
    if thb:
        sign = "+" if thb["delta_pct"] > 0 else ""
        msg = (
            f"💱 <b>USD/THB ALERT</b>\n"
            f"{thb['last']:.4f} → {thb['current']:.4f} "
            f"({sign}{thb['delta_pct']:.2f}%)\n"
            f"บาท{thb['direction']} → กระทบราคาทองในไทย"
        )
        send_message(msg)

    # 4. VIX panic
    vix = check_vix_panic(prices_map)
    if vix:
        msg = (
            f"📉 <b>VIX PANIC</b>\n"
            f"VIX: {vix['vix']:.2f} ({vix.get('change_pct', 0):+.2f}%)\n"
            f"<i>ตลาด nervous — ระวังเข้า trade ใหม่</i>"
        )
        send_message(msg)


def job_command_poll():
    """Poll Telegram for new commands."""
    print("→ Job: command_poll")
    n = listener.poll_and_handle()
    if n:
        print(f"  Processed {n} command(s)")


def job_weekly_recap():
    """Friday 18:00 weekly summary."""
    print("→ Job: weekly_recap")
    us = fetch_multiple(config.US_WATCHLIST)
    th = fetch_multiple(config.THAI_WATCHLIST)
    all_eq = us + th
    valid = [d for d in all_eq if d.get("change_5d_pct") is not None]
    valid.sort(key=lambda d: d["change_5d_pct"], reverse=True)

    now = datetime.now(ICT)
    lines = [
        "📰 <b>Weekly Recap</b>",
        f"<i>{now.strftime('%d %b %Y')} — สัปดาห์ที่ผ่านมา</i>",
        "",
    ]
    if valid:
        lines.append("🏆 <b>Top 5 winners (5D)</b>")
        for d in valid[:5]:
            lines.append(briefs.format_compact({**d, "change_pct": d["change_5d_pct"]}))
        lines.append("")
        lines.append("💀 <b>Top 5 losers (5D)</b>")
        for d in list(reversed(valid))[:5]:
            lines.append(briefs.format_compact({**d, "change_pct": d["change_5d_pct"]}))
    _send_chunks("\n".join(lines))


def job_heat():
    _send_chunks(briefs.build_heat_only())


def job_macro():
    _send_chunks(briefs.build_macro_only())


def job_thai():
    _send_chunks(briefs.build_thai_only())


def job_us():
    _send_chunks(briefs.build_us_only())


JOBS = {
    "full_brief": job_full_brief,
    "hourly_brief": job_hourly_brief,
    "tenmin_brief": job_tenmin_brief,
    "news": job_news,
    "runner": job_runner,
    "alert_check": job_alert_check,
    "command_poll": job_command_poll,
    "weekly_recap": job_weekly_recap,
    "heat": job_heat,
    "macro": job_macro,
    "thai": job_thai,
    "us": job_us,
    # Aliases for manual use
    "full": job_full_brief,
    "hourly": job_hourly_brief,
    "tenmin": job_tenmin_brief,
    "alert": job_alert_check,
    "command": job_command_poll,
    "weekly": job_weekly_recap,
}


def main():
    config.validate()
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "auto":
        # Smart cadence — used by GitHub Actions
        jobs = pick_jobs()
        print(f"Auto mode → jobs: {jobs}")
        for j in jobs:
            handler = JOBS.get(j)
            if handler:
                try:
                    handler()
                except Exception as e:
                    print(f"  ! Job {j} failed: {type(e).__name__}: {e}")
            else:
                print(f"  ? Unknown job: {j}")
        return

    handler = JOBS.get(mode)
    if not handler:
        print(f"Unknown mode '{mode}'. Available: {', '.join(sorted(JOBS))}")
        sys.exit(1)
    handler()


if __name__ == "__main__":
    main()

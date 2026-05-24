"""Realtime alert engine — price alerts, runner alerts, USD/THB alerts."""
from datetime import datetime, timezone

import config
from bot import state
from data.prices import fetch_price


def check_price_alerts(prices_by_ticker: dict[str, dict]) -> list[dict]:
    """Check all user-defined price alerts. Returns triggered alerts (and removes them)."""
    alerts = state.get_alerts()
    triggered = []
    remaining = []
    for alert in alerts:
        ticker = alert["ticker"].upper()
        d = prices_by_ticker.get(ticker)
        if not d:
            d = fetch_price(ticker)
        if not d:
            remaining.append(alert)
            continue
        price = d["price"]
        op = alert["op"]
        target = float(alert["price"])
        hit = (op == "<=" and price <= target) or (op == ">=" and price >= target)
        if hit:
            triggered.append({**alert, "current_price": price})
        else:
            remaining.append(alert)
    if triggered:
        state.save_alerts(remaining)
    return triggered


def check_runners(prices: list[dict]) -> list[dict]:
    """Find tickers with extreme moves not yet alerted today."""
    today = datetime.now(timezone.utc).date().isoformat()
    cooldown = state.get_runner_cooldown()
    triggered = []
    for d in prices:
        chg = d.get("change_pct") or 0
        vol_spike = d.get("volume_spike") or 0
        pct_trigger = abs(chg) >= config.RUNNER_PCT_THRESHOLD
        vol_trigger = vol_spike >= config.RUNNER_VOLUME_MULTIPLIER
        if not (pct_trigger or vol_trigger):
            continue
        # Skip if already alerted today
        if cooldown.get(d["ticker"]) == today:
            continue
        reasons = []
        if pct_trigger:
            reasons.append(f"{chg:+.1f}%")
        if vol_trigger:
            reasons.append(f"vol {vol_spike:.1f}x avg")
        triggered.append({**d, "reasons": reasons})
        cooldown[d["ticker"]] = today
    if triggered:
        state.save_runner_cooldown(cooldown)
    return triggered


def check_thb_move() -> dict | None:
    """Check USD/THB for unusual move since last alert."""
    d = fetch_price("THB=X")
    if not d:
        return None
    current = d["price"]
    last = state.get_thb_last()
    if last == 0:
        state.set_thb_last(current)
        return None
    delta_pct = (current - last) / last * 100 if last else 0
    if abs(delta_pct) >= config.THB_MOVE_THRESHOLD:
        state.set_thb_last(current)
        return {
            "current": current,
            "last": last,
            "delta_pct": delta_pct,
            "direction": "weaker" if delta_pct > 0 else "stronger",
        }
    return None


def check_vix_panic(prices_by_ticker: dict[str, dict]) -> dict | None:
    """Alert if VIX above panic threshold."""
    vix = prices_by_ticker.get("^VIX")
    if not vix:
        vix = fetch_price("^VIX")
    if not vix:
        return None
    if vix["price"] >= config.VIX_PANIC_THRESHOLD:
        return {"vix": vix["price"], "change_pct": vix.get("change_pct", 0)}
    return None

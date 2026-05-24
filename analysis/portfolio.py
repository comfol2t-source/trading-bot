"""Portfolio tracker — open positions + realized P/L."""
from datetime import datetime, timezone

from bot import state
from data.prices import fetch_price


def add_position(ticker: str, qty: float, entry_price: float) -> dict:
    """Add a new position or stack on existing one (weighted average)."""
    positions = state.get_portfolio()
    ticker = ticker.upper()
    for p in positions:
        if p["ticker"] == ticker:
            # Average down/up
            total_qty = p["qty"] + qty
            avg_price = (p["qty"] * p["entry_price"] + qty * entry_price) / total_qty
            p["qty"] = total_qty
            p["entry_price"] = avg_price
            state.save_portfolio(positions)
            return p
    new = {
        "ticker": ticker,
        "qty": qty,
        "entry_price": entry_price,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    positions.append(new)
    state.save_portfolio(positions)
    return new


def close_position(ticker: str, qty: float, exit_price: float) -> dict | None:
    """Close (partial or full) position. Returns realized trade record or None if no position."""
    positions = state.get_portfolio()
    ticker = ticker.upper()
    for p in positions:
        if p["ticker"] == ticker:
            sell_qty = min(qty, p["qty"])
            pnl = (exit_price - p["entry_price"]) * sell_qty
            trade = {
                "ticker": ticker,
                "qty": sell_qty,
                "entry": p["entry_price"],
                "exit": exit_price,
                "pnl": pnl,
                "closed_at": datetime.now(timezone.utc).isoformat(),
            }
            realized = state.get_realized()
            realized.append(trade)
            state.save_realized(realized)
            p["qty"] -= sell_qty
            if p["qty"] <= 0:
                positions.remove(p)
            state.save_portfolio(positions)
            return trade
    return None


def snapshot() -> dict:
    """Return current portfolio with live prices and P/L."""
    positions = state.get_portfolio()
    rows = []
    total_invested = 0.0
    total_current = 0.0
    for p in positions:
        price_data = fetch_price(p["ticker"])
        current = price_data["price"] if price_data else p["entry_price"]
        invested = p["qty"] * p["entry_price"]
        market = p["qty"] * current
        pnl = market - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        rows.append({
            **p,
            "current_price": current,
            "invested": invested,
            "market": market,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
        total_invested += invested
        total_current += market

    return {
        "positions": rows,
        "total_invested": total_invested,
        "total_current": total_current,
        "total_pnl": total_current - total_invested,
        "total_pnl_pct": ((total_current - total_invested) / total_invested * 100)
                          if total_invested else 0,
        "realized": state.get_realized(),
    }

"""Position size calculator — how many shares to buy given budget + risk."""


def calculate(entry: float, stop: float, budget: float, risk_pct: float) -> dict:
    """Calculate position size based on fixed-risk model.

    Args:
        entry: planned entry price
        stop:  stop-loss price
        budget: total capital available
        risk_pct: % of budget willing to lose on this trade (e.g. 2.0)

    Returns dict with shares, position_value, capital_pct, max_loss.
    """
    if entry <= 0 or stop <= 0 or budget <= 0 or risk_pct <= 0:
        return {"error": "All inputs must be positive numbers"}
    if entry == stop:
        return {"error": "Entry and stop cannot be equal"}

    risk_per_share = abs(entry - stop)
    max_loss_total = budget * risk_pct / 100
    shares = int(max_loss_total // risk_per_share)

    if shares == 0:
        return {
            "error": "Risk per share exceeds risk budget — "
                     "tighten stop loss or increase risk %"
        }

    position_value = shares * entry
    if position_value > budget:
        # Cap to budget
        shares = int(budget // entry)
        position_value = shares * entry

    max_loss = shares * risk_per_share
    capital_pct = position_value / budget * 100

    return {
        "shares": shares,
        "position_value": position_value,
        "capital_pct": capital_pct,
        "max_loss": max_loss,
        "risk_per_share": risk_per_share,
        "direction": "long" if entry > stop else "short",
    }

"""Detect anomalous price/volume behaviour from enriched price data."""
import config


def is_anomalous(d: dict) -> tuple[bool, list[str]]:
    """Return (True/False, reasons) — does this ticker have an unusual move?

    Triggers:
      - |% change today| exceeds ANOMALY_PCT_THRESHOLD, or
      - Volume exceeds ANOMALY_VOLUME_MULTIPLIER x 20-day average.
    """
    reasons = []

    chg = d.get("change_pct")
    if chg is not None and abs(chg) >= config.ANOMALY_PCT_THRESHOLD:
        direction = "↑" if chg > 0 else "↓"
        reasons.append(f"{direction}{abs(chg):.1f}% move")

    spike = d.get("volume_spike", 0)
    if spike >= config.ANOMALY_VOLUME_MULTIPLIER:
        reasons.append(f"vol {spike:.1f}x avg")

    return (len(reasons) > 0, reasons)


def find_anomalies(items: list[dict]) -> list[tuple[dict, list[str]]]:
    """Return list of (item, reasons) for everything that's anomalous."""
    out = []
    for d in items:
        ok, reasons = is_anomalous(d)
        if ok:
            out.append((d, reasons))
    # Sort by |% change| descending
    out.sort(key=lambda x: abs(x[0].get("change_pct", 0) or 0), reverse=True)
    return out


def top_movers(items: list[dict], n: int = 3) -> tuple[list[dict], list[dict]]:
    """Return (top_gainers, top_losers) sorted by % change."""
    sorted_items = sorted(
        [d for d in items if d.get("change_pct") is not None],
        key=lambda d: d["change_pct"],
        reverse=True,
    )
    gainers = [d for d in sorted_items if d["change_pct"] > 0][:n]
    losers = list(reversed(
        [d for d in sorted_items if d["change_pct"] < 0][-n:]
    ))
    return gainers, losers

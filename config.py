"""Configuration for the trading bot — Phase 1.6.

Reads credentials from .env (local) or environment (GitHub Actions),
defines themed watchlists, runner tags, alert thresholds, schedule logic.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === Credentials ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


# === Alert thresholds ===
ANOMALY_PCT_THRESHOLD = 5.0       # Daily brief anomaly
ANOMALY_VOLUME_MULTIPLIER = 3.0
RUNNER_PCT_THRESHOLD = 7.0        # Realtime runner alert (stricter)
RUNNER_VOLUME_MULTIPLIER = 5.0
THB_MOVE_THRESHOLD = 1.0          # USD/THB |%change| triggers alert
VIX_PANIC_THRESHOLD = 25.0        # VIX above triggers alert
XD_ALERT_DAYS_AHEAD = 3           # Notify N days before XD

TOP_MOVERS_COUNT = 3
NEWS_COUNT = 5
NEWS_COUNT_HOURLY = 3              # Smaller for hourly briefs


# === Watchlists organised by theme ===

US_THEMES = {
    # AI/Chip merged (user choice — kept together, includes Semiconductor pure-play)
    "AI / Chip": [
        "NVDA", "AMD", "SMCI", "ARM", "AVGO", "TSM", "MU", "PLTR",
        "AI", "SOUN", "INTC", "ASML", "AMAT", "LRCX", "KLAC",
    ],
    "EV / Space / Defense": [
        "TSLA", "ASTS", "RKLB", "JOBY", "ACHR", "LMT", "LUNR",
    ],
    "Quantum": ["IONQ", "RGTI", "QBTS", "QUBT"],
    "Nuclear / Energy-US": ["SMR", "OKLO", "NNE", "CCJ", "VST"],
    "Biotech Runners": ["VKTX", "RXRX", "RGEN", "MRNA"],
    "Crypto Stocks": [
        "MSTR", "COIN", "MARA", "CLSK", "RIOT", "HUT",
        "IBIT", "GBTC", "ETHE",
    ],
    "Energy (US)": ["XOM", "CVX", "COP", "OXY", "EOG", "SLB"],
    "Medical (US)": ["UNH", "JNJ", "LLY", "PFE", "MRK", "ABBV"],
    "Retail": ["AMZN", "WMT", "COST", "TGT", "HD"],
    "Industrials": ["BA", "GE", "CAT", "DE"],
    "Rare Earth & Critical Minerals": [
        "MP",      # MP Materials — biggest US pure-play
        "USAR",    # USA Rare Earth
        "TMC",     # TMC the metals company (battery metals)
        "REMX",    # VanEck Rare Earth ETF
        "LYSCF",   # Lynas Rare Earths (Australia OTC)
    ],
}

US_WATCHLIST = [t for tickers in US_THEMES.values() for t in tickers]

# Crypto spot prices (not stocks — yfinance ticker format BTC-USD)
CRYPTO_SPOT = ["BTC-USD", "ETH-USD"]

# Thai dividend stocks (only requested sectors: Banking, Medical, Energy)
THAI_THEMES = {
    "Banking": [
        "KBANK.BK", "BBL.BK", "SCB.BK", "KTB.BK",
        "TISCO.BK", "KKP.BK", "TTB.BK", "BAY.BK",
        "LHFG.BK", "TCAP.BK",
    ],
    "Medical & Wellness": [
        "BDMS.BK", "BH.BK", "BCH.BK", "CHG.BK", "RAM.BK", "RJH.BK",
    ],
    "Energy": [
        "PTT.BK", "PTTEP.BK", "GULF.BK", "EGCO.BK", "RATCH.BK",
        "BANPU.BK", "BCP.BK", "TOP.BK", "IRPC.BK",
    ],
}

THAI_WATCHLIST = [t for tickers in THAI_THEMES.values() for t in tickers]

# Macro indicators
MACRO = ["DX-Y.NYB", "^TNX", "^VIX", "SPY", "QQQ"]

# Gold (own section)
GOLD = [
    "GC=F",        # Gold futures (USD/oz)
]

# Currencies (own section)
CURRENCIES = [
    "THB=X",       # USD/THB — Thai gold price proxy
    "JPY=X",       # USD/JPY — safe-haven currency
    "EURUSD=X",    # EUR/USD — major
    "GBPUSD=X",    # GBP/USD — major
    "CNY=X",       # USD/CNY — China impact
    "AUDUSD=X",    # AUD/USD — commodity currency
]

# Kept as alias for backwards compat (used in alert sweeps)
GOLD_FX = GOLD + CURRENCIES


# === Runner tags 🚀 — high-volatility momentum stocks ===
# These get a 🚀 emoji in every section they appear in
RUNNERS = {
    # Quantum (all are runners)
    "IONQ", "RGTI", "QBTS", "QUBT",
    # Nuclear small-caps
    "SMR", "OKLO", "NNE",
    # Space/Defense small-caps
    "ASTS", "RKLB", "LUNR", "JOBY", "ACHR",
    # AI/Chip runners
    "SMCI", "AI", "SOUN", "PLTR",
    # Biotech runners
    "VKTX", "RXRX", "MRNA",
    # Crypto miners
    "MARA", "CLSK", "RIOT", "HUT",
    "MSTR", "COIN",
    # Rare earth (small caps + high volatility)
    "MP", "USAR", "TMC",
}


def is_runner(ticker: str) -> bool:
    """Return True if ticker is tagged as a runner."""
    return ticker.upper().replace(".BK", "").replace("-USD", "") in RUNNERS


def validate():
    """Raise if any required credential is missing."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not FINNHUB_API_KEY:
        missing.append("FINNHUB_API_KEY")
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}\n"
            "Create a .env file (local) or set GitHub Actions secrets."
        )

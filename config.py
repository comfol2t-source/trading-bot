"""Configuration for the trading bot.

Reads credentials from .env, defines default watchlists.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === Credentials (loaded from .env) ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


# === Anomaly detection thresholds ===
ANOMALY_PCT_THRESHOLD = 5.0      # |% change| > 5% counts as unusual move
ANOMALY_VOLUME_MULTIPLIER = 3.0  # volume > 3x 20-day average counts as spike

# How many top gainers/losers to show in the brief
TOP_MOVERS_COUNT = 3
# How many news headlines to show
NEWS_COUNT = 5


# === Watchlists organised by theme ===

US_THEMES = {
    "AI / Chip": [
        "NVDA", "AMD", "SMCI", "ARM", "AVGO", "TSM", "MU", "PLTR",
        "AI", "SOUN",
    ],
    "EV / Space / Defense": [
        "TSLA", "ASTS", "RKLB", "JOBY", "ACHR", "LMT", "LUNR",
    ],
    "Quantum": [
        "IONQ", "RGTI", "QBTS", "QUBT",
    ],
    "Nuclear / Energy": [
        "SMR", "OKLO", "NNE", "CCJ", "VST",
    ],
    "Biotech Runners": [
        "VKTX", "RXRX",
    ],
    "Crypto-Proxy (no direct crypto)": [
        "MSTR", "COIN",
    ],
}

# Flat US watchlist (derived from themes)
US_WATCHLIST = [t for tickers in US_THEMES.values() for t in tickers]

# Thai dividend stocks organised by sector
THAI_THEMES = {
    "Banking": ["KBANK.BK", "BBL.BK", "SCB.BK", "KTB.BK"],
    "Energy / Utility": ["PTT.BK", "GULF.BK", "EGCO.BK", "RATCH.BK"],
    "Telecom": ["ADVANC.BK", "TRUE.BK"],
    "Property / REIT": ["CPNREIT.BK", "FTREIT.BK", "AIMIRT.BK"],
    "Infrastructure": ["AOT.BK", "BEM.BK", "DIF.BK"],
}

THAI_WATCHLIST = [t for tickers in THAI_THEMES.values() for t in tickers]

# Macro indicators
MACRO = [
    "DX-Y.NYB",   # DXY — US Dollar Index
    "^TNX",       # US 10-Year Treasury Yield
    "^VIX",       # Volatility Index
    "SPY",        # S&P 500 ETF
    "QQQ",        # Nasdaq-100 ETF
]

# Gold + FX (separate section)
GOLD_FX = [
    "GC=F",       # Gold Futures (USD/oz)
    "GLD",        # SPDR Gold Trust ETF (USD-denominated gold)
    "THB=X",      # USD/THB
    "JPY=X",      # USD/JPY (safe-haven proxy)
]


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
            "Create a .env file in the project root (copy from .env.example) "
            "and fill in your credentials."
        )

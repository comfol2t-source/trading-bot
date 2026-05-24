# Trading Bot

Personal market intelligence Telegram bot — US stocks, Thai dividend stocks, gold, macro indicators, IPO/earnings calendars.

**Approach:** Rule-based scoring + filtering (no AI/LLM API). Deep analysis via Hybrid mode — bot generates ready-to-paste prompts for Claude Pro.

## Phase 1 (current)

Fetches prices for the configured watchlist and pushes a snapshot to Telegram.

## Setup

1. Clone this repo, then in the project root:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in:
   - `TELEGRAM_BOT_TOKEN` — from @BotFather
   - `TELEGRAM_CHAT_ID` — from @userinfobot
   - `FINNHUB_API_KEY` — from finnhub.io

3. Run:
   ```powershell
   python main.py
   ```

You should receive a market snapshot in Telegram.

## Project structure

```
trading-bot/
├── .env                  # secrets (gitignored — create from .env.example)
├── .env.example
├── config.py             # credentials + default watchlists
├── main.py               # entry point
├── requirements.txt
├── data/
│   └── prices.py         # yfinance wrapper
└── bot/
    └── telegram_sender.py
```

## Roadmap

- **Phase 1** ✅ — Watchlist snapshot to Telegram
- **Phase 2** — Daily brief + Setup Score + indicators (RSI/MACD/MA)
- **Phase 3** — News + IPO/earnings calendars + Thai dividend module
- **Phase 4** — Runners scan + `/dive` prompt generator + GitHub Actions deploy

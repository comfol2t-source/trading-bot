# Trading Bot — Phase 1.6

Personal market intelligence Telegram bot — runs on **GitHub Actions** (free, no PC required).

Covers US stocks, Thai dividend stocks, gold, macro, crypto exposure, news, IPO/earnings calendars, portfolio tracking, price alerts, and runner alerts.

## What it does

- **Smart cadence brief** — pushed to Telegram automatically:
  - 4× full brief: 07:00, 13:00, 21:00, 04:30 ICT
  - Hourly compact brief (skipping quiet hours 04:30-06:30)
  - 10-min interval briefs around Thai & US market open/close
  - Friday 18:00 weekly recap
- **Realtime alerts** (every 10 min check):
  - 🚀 Runner alert (|Δ%| ≥ 7 or volume ≥ 5× avg, once per day per ticker)
  - 💰 Custom price alerts
  - 💱 USD/THB unusual move (≥ 1%)
  - 📉 VIX panic (≥ 25)
- **Interactive commands** via Telegram chat (1-5 min response):
  - `update`, `news`, `runner`, `macro`, `thai`, `us`, `heat`
  - `alert add/list/remove`, `buy`, `sell`, `portfolio`
  - `size`, `ipo`, `earnings`, `help`
  - Bare ticker (e.g. `NVDA` or `KBANK`) → single ticker info

## Watchlist (17 themes)

🇹🇭 **Thai (dividend-focused):** Banking (11 tickers), Medical & Wellness, Energy
🇺🇸 **US:** AI/Chip, EV/Space/Defense, Quantum, Nuclear, Biotech, Crypto Stocks/ETF, Energy, Medical, Retail, Consumer Staples, Industrials, Gold Mining
🥇 **Macro/FX:** DXY, US10Y, VIX, SPY, QQQ, GC futures, GLD, USD/THB
🪙 **Crypto spot:** BTC-USD, ETH-USD

🚀 **Runner tags** mark high-volatility momentum stocks (Quantum, Nuclear small-caps, Space, AI runners, Biotech, Crypto miners).

## Architecture

```
trading-bot/
├── config.py                  # watchlists, themes, runner tags, thresholds
├── main.py                    # entry — dispatches jobs by mode
├── data/
│   ├── prices.py              # yfinance + 5D/30D + volume context
│   ├── news.py                # Finnhub + smart filter + dedup
│   └── calendars.py           # IPO + earnings
├── analysis/
│   ├── anomaly.py             # |Δ%| or volume spike detection
│   ├── alerts.py              # runner / price / THB / VIX
│   ├── heatmap.py             # sector aggregation
│   ├── portfolio.py           # P/L tracker
│   ├── position_sizing.py     # fixed-risk sizing
│   └── scheduler_logic.py     # smart cadence (what to run when)
├── bot/
│   ├── briefs.py              # all message formatters
│   ├── commands.py            # command router
│   ├── listener.py            # poll Telegram getUpdates
│   ├── state.py               # JSON file persistence
│   └── telegram_sender.py     # token-safe HTTP send
├── .state/                    # runtime state (committed back by GH Actions)
└── .github/workflows/
    └── bot.yml                # cron */10 min — runs `python main.py auto`
```

## Setup

### Local development

```powershell
git clone https://github.com/comfol2t-source/trading-bot.git
cd trading-bot
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env   # fill in real credentials
python main.py full   # test
```

### GitHub Actions deploy

1. Set 3 repo secrets in GitHub → Settings → Secrets and variables → Actions:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `FINNHUB_API_KEY`
2. Push to main — `bot.yml` workflow takes over from there.
3. Watch runs at: `https://github.com/<user>/trading-bot/actions`

### Modes (manual)

```
python main.py auto      # used by GH Actions — smart cadence
python main.py full      # full brief now
python main.py hourly    # compact hourly brief
python main.py alert     # alert check only
python main.py command   # poll Telegram commands
python main.py news      # news only
python main.py runner    # runner check only
python main.py weekly    # weekly recap
python main.py heat      # sector heat map
python main.py macro     # macro + gold + FX
python main.py thai      # thai watchlist
python main.py us        # us watchlist
```

## Security notes

- `.env` is gitignored; secrets live in GitHub Actions Secrets in CI.
- `telegram_sender.py` never logs URLs (which contain the bot token).
- `diagnose.py` exists for safe Telegram debugging (prints chat IDs only).
- Bot listener restricts commands to the configured `TELEGRAM_CHAT_ID`.

## Cost

**$0 / month.**
- Telegram Bot API: free
- yfinance: free (Yahoo)
- Finnhub free tier: 60 req/min (more than enough)
- GitHub Actions: ~1,500 min/month used of 2,000 free quota

## Roadmap

- **Phase 2** — Technical indicators (RSI/MACD/MA), Setup Score 0-10, `/dive TICKER` prompt generator for Claude Pro paste-in
- **Phase 3** — Thai XD calendar (scrape Settrade), economic calendar (scrape investing.com), pre/post-market US movers

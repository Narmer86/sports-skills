---
name: kalshi
description: |
  Kalshi prediction markets — events, series, markets, trades, and candlestick data. Public API, no auth required for reads. US-regulated exchange (CFTC). Covers soccer, basketball, baseball, tennis, NFL, hockey event contracts.

  Use when: user asks about Kalshi-specific markets, event contracts, CFTC-regulated prediction markets, or candlestick/OHLC price history on sports outcomes.
  Don't use when: user asks about actual match results, scores, or statistics — use the sport-specific skill: football-data (soccer), nfl-data (NFL), nba-data (NBA), wnba-data (WNBA), nhl-data (NHL), mlb-data (MLB), tennis-data (tennis), golf-data (golf), cfb-data (college football), cbb-data (college basketball), or fastf1 (F1). Don't use for general "who will win" questions unless Kalshi is specifically mentioned — try polymarket first (broader sports coverage). Don't use for news — use sports-news instead.
license: MIT
metadata:
  author: machina-sports
  version: "0.2.0"
---

# Kalshi — Prediction Markets

## Quick Start

Prefer the CLI — it avoids Python import path issues:
```bash
# Search NBA markets
sports-skills kalshi search_markets --sport=nba

# Get today's NBA events with nested markets
sports-skills kalshi get_todays_events --sport=nba

# List available sport codes
sports-skills kalshi get_sports_config

# Raw markets by series ticker
sports-skills kalshi get_markets --series_ticker=KXNBA --status=open
```

Python SDK (alternative):
```python
from sports_skills import kalshi

# Sport-based search (same interface as polymarket)
kalshi.search_markets(sport='nba')
kalshi.search_markets(sport='nba', query='Lakers')
kalshi.get_todays_events(sport='nba')
kalshi.get_sports_config()

# Raw queries
kalshi.get_markets(series_ticker="KXNBA", status="open")
kalshi.get_event(event_ticker="KXNBA-26FEB14")
```

## Important Notes

- **"Football" = NFL on Kalshi.** Soccer is under "Soccer". Use `KXUCL`, `KXLALIGA`, etc. for soccer leagues.
- **Prices are probabilities.** A `last_price` of 20 means 20% implied probability. Scale is 0-100 (not 0-1 like Polymarket).
- **Always use `status="open"`** when querying markets, otherwise results include settled/closed markets.
- **Shared interface with Polymarket:** `search_markets(sport=...)`, `get_todays_events(sport=...)`, and `get_sports_config()` work the same way on both platforms.

*For detailed reference data, see the files in the `references/` directory.*

## Workflows

### Workflow: Sport Market Search (Recommended)
1. `search_markets --sport=nba` — finds all open NBA markets.
2. Optionally add `--query="Lakers"` to filter by keyword.
3. Results include yes_bid, no_bid, volume for each market.

### Workflow: Today's Events
1. `get_todays_events --sport=nba` — open events with nested markets.
2. Present events with prices (price = implied probability, 0-100 scale).

### Workflow: Discover Available Sports
1. `get_sports_config` — lists sport codes and series tickers.
2. Use any code with `search_markets(sport=...)` or `get_todays_events(sport=...)`.

### Workflow: Futures Market Check
1. `get_markets --series_ticker=<ticker> --status=open`
2. Sort by `last_price` descending.
3. Present top contenders with probability and volume.

### Workflow: Market Price History
1. Get market ticker from `search_markets --sport=nba`.
2. `get_market_candlesticks --series_ticker=<s> --ticker=<t> --start_ts=<start> --end_ts=<end> --period_interval=60`
3. Present OHLC with volume.

## Commands Reference

### Sport-Aware Commands (same interface as Polymarket)

| Command | Required | Optional | Description |
|---|---|---|---|
| `get_sports_config` | | | **Available sport codes** and series tickers |
| `get_todays_events` | sport | limit | **Today's events** for a sport with nested markets |
| `search_markets` | | sport, query, status, limit | **Find markets** by sport and/or keyword |

### Raw API Commands

| Command | Required | Optional | Description |
|---|---|---|---|
| `get_exchange_status` | | | Exchange trading status |
| `get_exchange_schedule` | | | Operating hours |
| `get_series_list` | | category, tags | All series (leagues) |
| `get_series` | series_ticker | | Series details |
| `get_events` | | limit, cursor, status, series_ticker, with_nested_markets | Event listing |
| `get_event` | event_ticker | with_nested_markets | Event details |
| `get_markets` | | limit, cursor, event_ticker, series_ticker, status, tickers | Market listing |
| `get_market` | ticker | | Market details |
| `get_trades` | | limit, cursor, ticker, min_ts, max_ts | Recent trades |
| `get_market_candlesticks` | series_ticker, ticker, start_ts, end_ts, period_interval | | OHLC data |
| `get_sports_filters` | | | Filter categories |

## Sport Codes

| Sport | Code | Series Ticker |
|---|---|---|
| NBA | `nba` | KXNBA |
| NFL | `nfl` | KXNFL |
| MLB | `mlb` | KXMLB |
| NHL | `nhl` | KXNHL |
| WNBA | `wnba` | KXWNBA |
| College Football | `cfb` | KXCFB |
| College Basketball | `cbb` | KXCBB |

## Examples

User: "What NBA markets are on Kalshi?"
1. Call `search_markets(sport='nba')` — same interface as polymarket
2. Present markets with yes/no prices and volume

User: "Who will win the Champions League?"
1. Call `get_markets(series_ticker="KXUCL", status="open")`
2. Sort by `last_price` descending — price = implied probability (e.g., 20 = 20%)
3. Present top teams with `yes_sub_title`, `last_price`, and `volume`

User: "Show me the price history for this NBA game"
1. Get the market ticker from `search_markets(sport='nba')`
2. Call `get_market_candlesticks(series_ticker="KXNBA", ticker="...", start_ts=..., end_ts=..., period_interval=60)`
3. Present OHLC data with volume

## Error Handling & Fallbacks

- If `search_markets` returns no results for a sport, that sport may not have active markets on Kalshi. Try `get_sports_config()` to see available sports.
- If series ticker returns no results, call `get_series_list()` to discover available tickers. See `references/series-tickers.md`.
- If markets are empty, use `status="open"` to filter. Default includes settled/closed markets.
- If "Football" returns NFL instead of soccer, Kalshi uses "Football" for NFL, "Soccer" for soccer. Use KXUCL, KXLALIGA, etc. for soccer.
- **Never fabricate market prices or probabilities.** If no market exists, state so.

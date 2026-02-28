# Valid Commands & Common Mistakes

## Sport-Aware Commands (recommended)

These use sport codes (`nba`, `nfl`, `mlb`, etc.) — same interface as Polymarket:
- `get_sports_config` — **list all available sport codes** and series tickers
- `get_todays_events` — **today's events for a sport** (requires `sport` param)
- `search_markets` — **find markets by sport and keyword** (use `sport` param)

## Raw API Commands

These query the Kalshi API directly using series/event/market tickers:
- `get_exchange_status`
- `get_exchange_schedule`
- `get_series_list`
- `get_series`
- `get_events`
- `get_event`
- `get_markets`
- `get_market`
- `get_trades`
- `get_market_candlesticks`
- `get_sports_filters`

## Key Usage Patterns

### Finding sport markets (MOST COMMON)
```bash
# Use the sport parameter — maps to the right series ticker automatically
sports-skills kalshi search_markets --sport=nba
sports-skills kalshi search_markets --sport=nba --query="Lakers"
sports-skills kalshi get_todays_events --sport=nba
```

### Discovering sport codes
```bash
sports-skills kalshi get_sports_config
# Returns: nba, nfl, mlb, nhl, wnba, cfb, cbb with series tickers
```

## Commands that DO NOT exist (commonly hallucinated)

- ~~`get_odds`~~ / ~~`get_probability`~~ — market prices ARE the implied probability. Use `get_market(ticker="...")` and read the `last_price` field (e.g., 20 = 20% implied probability).
- ~~`get_market_odds`~~ — use `get_market` or `get_markets` and interpret `last_price` as probability.
- ~~`get_series_by_sport`~~ — use `get_sports_config()` to see sport codes and series tickers.

## Other common mistakes

- **Not using the `sport` parameter** — without it, you need to know series tickers. `search_markets(sport='nba')` automatically resolves to `KXNBA`.
- Confusing "Football" (NFL) with "Soccer" on Kalshi — see the series tickers table.
- Guessing series or event tickers instead of using `get_sports_config()` or `get_series_list()`.
- Forgetting `status="open"` when querying raw markets — without it, results include settled/closed markets.

If you're unsure whether a command exists, check this list. Do not try commands that aren't listed above.

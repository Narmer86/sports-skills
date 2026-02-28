---
name: polymarket
description: |
  Polymarket sports prediction markets — live odds, prices, order books, events, series, and market search. No auth required. Covers NFL, NBA, MLB, soccer, tennis, cricket, MMA, esports. Supports moneyline, spreads, totals, and player props.

  Use when: user asks about sports betting odds, prediction markets, win probabilities, market sentiment, or "who is favored to win" questions.
  Don't use when: user asks about actual match results, scores, or statistics — use the sport-specific skill: football-data (soccer), nfl-data (NFL), nba-data (NBA), wnba-data (WNBA), nhl-data (NHL), mlb-data (MLB), tennis-data (tennis), golf-data (golf), cfb-data (college football), cbb-data (college basketball), or fastf1 (F1). Don't use for historical match data. Don't use for news — use sports-news instead. Don't confuse with Kalshi — Polymarket focuses on crypto-native prediction markets with deeper sports coverage; Kalshi is a US-regulated exchange with different market structure.
license: MIT
metadata:
  author: machina-sports
  version: "0.3.0"
---

# Polymarket — Sports Prediction Markets

## Quick Start

Prefer the CLI — it avoids Python import path issues:
```bash
# Get today's NBA single-game markets
sports-skills polymarket search_markets --sport=nba --sports_market_types=moneyline

# Get today's EPL events with all market types
sports-skills polymarket get_todays_events --sport=epl

# Search for a specific team's markets
sports-skills polymarket search_markets --sport=epl --query="Leeds" --sports_market_types=moneyline

# List all available sport codes
sports-skills polymarket get_sports_config
```

Python SDK (alternative):
```python
from sports_skills import polymarket

# Single-game markets for a sport
polymarket.search_markets(sport='nba', sports_market_types='moneyline')

# Today's events for a league
polymarket.get_todays_events(sport='epl')

# Search by team name within a league
polymarket.search_markets(sport='epl', query='Leeds')

# Available sport codes
polymarket.get_sports_config()
```

## Prerequisites

**Core commands** (14 commands) work out of the box — no dependencies, no API keys.

**Trading commands** require the `py_clob_client` package:
```bash
pip install sports-skills[polymarket]
```

**Trading commands** additionally require a configured wallet:

```bash
# Option 1 — environment variable
export POLYMARKET_PRIVATE_KEY=0x...
```

```python
# Option 2 — Python SDK (per-session)
from sports_skills import polymarket
polymarket.configure(private_key="0x...")
```

## Important Notes

- **Prices are probabilities.** A price of 0.65 means 65% implied probability. No conversion needed.
- **Use the `sport` parameter for single-game markets.** Without it, `search_markets` only finds high-volume futures. With `sport='nba'`, it finds today's NBA single-game moneylines, spreads, and props.
- **`token_id` vs `market_id`:** Price and orderbook endpoints require the CLOB `token_id`, not the Gamma `market_id`. Always call `get_market_details` first to get `clobTokenIds`.
- **`get_sports_config()`** returns 120+ sport codes (nba, epl, nfl, bun, fl1, ucl, mls, atp, wta, etc.).

*For detailed reference data, see the files in the `references/` directory.*

## Workflows

### Workflow: Find Single-Game Markets for a Sport
1. `search_markets --sport=nba` (or epl, nfl, bun, etc.)
2. Each market includes outcomes with prices (price = probability).
3. For detailed prices, use `get_market_prices --token_id=<clob_token_id>`.

### Workflow: Today's Events for a League
1. `get_todays_events --sport=epl` — returns events sorted by start date.
2. Each event includes nested markets (moneyline, spreads, totals, props).
3. Pick a market, get `clob_token_id` from outcomes, then `get_market_prices`.

### Workflow: Team-Specific Search
1. `search_markets --sport=epl --query="Leeds" --sports_market_types=moneyline`
2. Returns only Leeds United moneyline markets.
3. Works for any team/player name within a league.

### Workflow: Live Odds Check
1. `search_markets --sport=nba --query="Lakers" --sports_market_types=moneyline`
2. `get_market_prices --token_id=<id>` for live CLOB prices.
3. Present probabilities.

### Workflow: Discover Available Sports
1. `get_sports_config` — lists all sport codes and their series IDs.
2. Use any code with `search_markets(sport=...)` or `get_todays_events(sport=...)`.

### Workflow: Event Overview
1. `get_sports_events --active=true`
2. Pick event, then `get_event_details --event_id=<id>`.
3. For each market, get prices.

### Workflow: Price Trend Analysis
1. Find market via `search_markets --sport=nba`.
2. Get `clob_token_id` from the outcomes.
3. `get_price_history --token_id=<id> --interval=1w`
4. Present price movement.

### Workflow: Trading (requires py_clob_client + wallet)
1. `search_markets --sport=nba` — find markets
2. Get `clob_token_id` from the outcomes
3. `create_order --token_id=<id> --side=buy --price=0.55 --size=10`
4. `get_orders` — verify order placed
5. `cancel_order --order_id=<id>` — cancel if needed

## Commands Reference

### Core Commands (no dependencies needed)

| Command | Required | Optional | Description |
|---|---|---|---|
| `get_sports_config` | | | **Available sport codes** (nba, epl, nfl, bun, fl1, etc.) |
| `get_todays_events` | sport | limit | **Today's events for a league** — sorted by start date |
| `search_markets` | | query, sport, sports_market_types, tag_id, limit | **Find markets** by sport, keyword, and type |
| `get_sports_markets` | | limit, offset, sports_market_types, game_id, active, closed, order, ascending | Browse all sports markets |
| `get_sports_events` | | limit, offset, active, closed, order, ascending, series_id | Browse sports events |
| `get_series` | | limit, offset | List series (leagues) |
| `get_market_details` | | market_id, slug | Single market details |
| `get_event_details` | | event_id, slug | Single event details |
| `get_market_prices` | | token_id, token_ids | Current CLOB prices |
| `get_order_book` | token_id | | Full order book |
| `get_sports_market_types` | | | Valid market types |
| `get_price_history` | token_id | interval, fidelity | Historical prices |
| `get_last_trade_price` | token_id | | Most recent trade |

### Trading Commands (requires py_clob_client + wallet)

| Command | Required | Optional | Description |
|---|---|---|---|
| `configure` | | private_key, signature_type | Configure wallet |
| `create_order` | token_id, side, price, size | order_type | Place limit order |
| `market_order` | token_id, side, amount | | Place market order |
| `cancel_order` | order_id | | Cancel order |
| `cancel_all_orders` | | | Cancel all orders |
| `get_orders` | | market | Open orders |
| `get_user_trades` | | | Your trades |

## Sport Codes (common)

Use these with `search_markets(sport=...)` and `get_todays_events(sport=...)`:

| Code | League |
|---|---|
| `nba` | NBA |
| `nfl` | NFL |
| `nhl` | NHL |
| `mlb` | MLB |
| `wnba` | WNBA |
| `epl` | English Premier League |
| `bun` | Bundesliga |
| `lal` | La Liga |
| `fl1` | Ligue 1 |
| `sea` | Serie A |
| `ucl` | Champions League |
| `uel` | Europa League |
| `mls` | MLS |
| `atp` | ATP Tennis |
| `wta` | WTA Tennis |
| `cfb` | College Football |
| `cbb` | College Basketball |

Run `get_sports_config()` for the full list of 120+ sport codes.

## Examples

User: "Who's favored in tonight's NBA games?"
1. Call `search_markets(sport='nba', sports_market_types='moneyline')`
2. Present each matchup with implied probabilities (price = probability)

User: "Show me Leeds vs Man City odds"
1. Call `search_markets(sport='epl', query='Leeds', sports_market_types='moneyline')`
2. Present outcomes with prices

User: "What EPL matches are on today?"
1. Call `get_todays_events(sport='epl')`
2. Present events with their nested markets

User: "Who will win the Premier League?"
1. Call `search_markets(query='Premier League')` — this returns futures
2. Sort results by Yes outcome price descending

User: "Show me Bundesliga odds for Dortmund vs Bayern"
1. Call `search_markets(sport='bun', query='Dortmund', sports_market_types='moneyline')`
2. Present outcomes with prices

User: "What sports markets are available?"
1. Call `get_sports_config()` — lists all sport codes
2. Present the available leagues

## Error Handling & Fallbacks

- **If search returns 0 results**, make sure you're using the `sport` parameter. Without it, search only checks high-volume markets and may miss single-game events.
- If `get_market_prices` fails, you likely used `market_id` instead of `token_id`. Always call `get_market_details` first to get CLOB `token_id`.
- If prices seem stale, check `get_last_trade_price` for the most recent trade. Low-liquidity markets may have wide spreads.
- **Never fabricate odds or probabilities.** If no market exists, state so.

# Valid Commands & Common Mistakes

## Core Commands (no dependencies needed)

These work out of the box:
- `get_sports_config` — **list all available sport codes** (nba, epl, nfl, bun, etc.)
- `get_todays_events` — **today's events for a specific sport** (requires `sport` param)
- `search_markets` — **find markets by sport, keyword, and type** (use `sport` param for single-game markets)
- `get_sports_markets` — browse all sports markets (sorted by volume)
- `get_sports_events` — browse sports events (sorted by volume)
- `get_series` — list series (leagues)
- `get_market_details` — single market details (by market_id or slug)
- `get_event_details` — single event details with nested markets
- `get_market_prices` — current CLOB prices (requires token_id)
- `get_order_book` — full order book (requires token_id)
- `get_sports_market_types` — valid market types
- `get_price_history` — historical prices (requires token_id)
- `get_last_trade_price` — most recent trade (requires token_id)

## Trading Commands (requires py_clob_client + wallet)

- `configure` — set wallet private key
- `create_order` — place a limit order (token_id, side, price, size)
- `market_order` — place a market order (token_id, side, amount)
- `cancel_order` — cancel an order by ID
- `cancel_all_orders` — cancel all open orders
- `get_orders` — view open orders
- `get_user_trades` — view your trades

## Key Usage Patterns

### Finding single-game markets (MOST COMMON)
```bash
# Use the sport parameter — this is the key to finding single-game markets
sports-skills polymarket search_markets --sport=nba --sports_market_types=moneyline
sports-skills polymarket search_markets --sport=epl --query="Leeds"
sports-skills polymarket get_todays_events --sport=nba
```

### Discovering sport codes
```bash
sports-skills polymarket get_sports_config
# Returns: nba, epl, nfl, bun, fl1, ucl, mls, atp, wta, and 110+ more
```

## Commands that DO NOT exist (commonly hallucinated)

- ~~`get_market_odds`~~ / ~~`get_odds`~~ -- market prices ARE the implied probability. Use `get_market_prices(token_id="...")` where price = probability.
- ~~`get_implied_probability`~~ -- the price IS the implied probability. No conversion needed.
- ~~`get_current_odds`~~ -- use `get_last_trade_price(token_id="...")` for the most recent price.
- ~~`get_markets`~~ -- the correct command is `get_sports_markets` (for browsing) or `search_markets` (for searching by keyword/sport).

## Other common mistakes

- **Not using the `sport` parameter** — without it, `search_markets` only checks high-volume markets and misses single-game events. Always pass `sport='nba'` (or epl, nfl, etc.) when looking for specific game markets.
- Using `market_id` where `token_id` is needed — price and orderbook endpoints require the CLOB `token_id`, not the Gamma `market_id`. Always call `get_market_details` first to get `clobTokenIds`.
- Searching generic terms like "soccer" or "football" without `sport` — use the sport code parameter instead.
- Forgetting to get the `token_id` before calling price/orderbook endpoints — always fetch market details first.

If you're unsure whether a command exists, check this list. Do not try commands that aren't listed above.

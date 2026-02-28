# Sport Codes & Series Tickers

## Sport Codes (use with search_markets, get_todays_events)

| Sport | Code | Series Ticker |
|---|---|---|
| NBA | `nba` | KXNBA |
| NFL | `nfl` | KXNFL |
| MLB | `mlb` | KXMLB |
| NHL | `nhl` | KXNHL |
| WNBA | `wnba` | KXWNBA |
| College Football | `cfb` | KXCFB |
| College Basketball | `cbb` | KXCBB |

Use `get_sports_config()` to see all available codes.

## Soccer Series Tickers (raw API only)

**IMPORTANT:** On Kalshi, "Football" = American Football (NFL). Soccer is under "Soccer".

| League | Series Ticker | Notes |
|---|---|---|
| Champions League | `KXUCL` | Futures (winner) |
| La Liga | `KXLALIGA` | Futures (winner) |
| Bundesliga | `KXBUNDESLIGA` | Futures (winner) |
| Serie A | `KXSERIEA` | Futures (winner) |
| Ligue 1 | `KXLIGUE1` | Futures (winner) |
| FA Cup | `KXFACUP` | Futures |
| Europa League | `KXUEL` | Futures |
| Conference League | `KXUECL` | Futures |

Not all soccer leagues have futures/winner markets. EPL has match-day games but **no title winner** market. Use `get_sports_filters()` to discover all available competitions.

Soccer leagues are not yet mapped to sport codes — use `get_markets(series_ticker="KXUCL", status="open")` directly.

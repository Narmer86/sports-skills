---
name: betting
description: |
  Betting analysis — odds conversion, de-vigging, edge detection, Kelly criterion, Monte Carlo simulation, and drawdown analysis. Pure computation, no API calls. Works with odds from any source: ESPN (American odds), Polymarket (decimal probabilities), Kalshi (integer probabilities).

  Use when: user asks about bet sizing, expected value, edge analysis, Kelly criterion, Monte Carlo simulation, drawdown analysis, odds conversion, or comparing odds across sources. Also use when you have odds from ESPN and a prediction market price and want to evaluate whether a bet has positive expected value.
  Don't use when: user asks for live odds or market data — use polymarket, kalshi, or the sport-specific skill to fetch odds first, then use this skill to analyze them.
license: MIT
metadata:
  author: machina-sports
  version: "0.1.0"
---

# Betting Analysis

## Quick Start

```bash
sports-skills betting convert_odds --odds=-150 --from_format=american
sports-skills betting devig --odds=-150,+130 --format=american
sports-skills betting find_edge --fair_prob=0.58 --market_prob=0.52
sports-skills betting evaluate_bet --book_odds=-150,+130 --market_prob=0.52
```

Python SDK:
```python
from sports_skills import betting

betting.convert_odds(odds=-150, from_format="american")
betting.devig(odds="-150,+130", format="american")
betting.find_edge(fair_prob=0.58, market_prob=0.52)
```

## Odds Formats

| Format | Example | Description |
|---|---|---|
| American | `-150`, `+130` | US sportsbook standard. Negative = favorite, positive = underdog |
| Decimal | `1.67`, `2.30` | European standard. Payout per $1 (includes stake) |
| Probability | `0.60`, `0.43` | Direct implied probability (0-1). Polymarket uses this format |

**Conversion rules:**
- American negative: prob = -odds / (-odds + 100). Example: -150 → 150/250 = 0.600
- American positive: prob = 100 / (odds + 100). Example: +130 → 100/230 = 0.435
- Decimal: prob = 1 / odds. Example: 1.67 → 0.599
- Kalshi prices (0-100 integer): divide by 100 to get probability format

## Commands

| Command | Required | Optional | Description |
|---|---|---|---|
| `convert_odds` | odds, from_format | | Convert between American, decimal, probability |
| `devig` | odds | format | Remove vig from sportsbook odds → fair probabilities |
| `find_edge` | fair_prob, market_prob | | Compute edge, EV, and Kelly from two probabilities |
| `kelly_criterion` | fair_prob, market_prob | | Kelly fraction for optimal bet sizing |
| `monte_carlo_sim` | returns | n_simulations, n_periods, initial_bankroll, seed | Monte Carlo resampling simulation |
| `max_drawdown` | values | | Maximum drawdown from a wealth/equity series |
| `evaluate_bet` | book_odds, market_prob | book_format, outcome, returns, n_simulations, n_periods, initial_bankroll, seed | Full pipeline: devig → edge → Kelly → Monte Carlo |

## Workflows

### Workflow: Compare ESPN vs Polymarket/Kalshi

This is the primary workflow. The agent already has odds from ESPN and a prediction market — no user estimation needed.

1. Get ESPN moneyline odds for a game (e.g., from `nba get_scoreboard`):
   - Home: `-150`, Away: `+130`
2. Get Polymarket/Kalshi price for the same outcome (e.g., home team at `0.52`).
3. De-vig the ESPN odds to get fair probabilities:
   `devig --odds=-150,+130 --format=american`
   → Fair: Home 57.9%, Away 42.1% (removed ~3.5% vig)
4. Compare fair prob to market price:
   `find_edge --fair_prob=0.579 --market_prob=0.52`
   → Edge: 5.9%, EV: 11.3%, Kelly: 0.123
5. Full evaluation with Monte Carlo:
   `evaluate_bet --book_odds=-150,+130 --market_prob=0.52`

### Workflow: De-Vig Sportsbook Odds

Strip the vig/juice from DraftKings odds to see the "true" implied probabilities.

1. `devig --odds=-110,-110 --format=american`
   → Each side is 50.0% fair (standard -110/-110 spread/total)
2. `devig --odds=-200,+170 --format=american`
   → Favorite: 65.2%, Underdog: 34.8%
3. `devig --odds=-150,+300,+400 --format=american` (3-way soccer)
   → Home: 47.3%, Draw: 19.8%, Away: 15.7%

### Workflow: Odds Conversion

Convert odds from one format to another.

1. `convert_odds --odds=-150 --from_format=american`
   → Probability: 60.0%, Decimal: 1.6667
2. `convert_odds --odds=2.50 --from_format=decimal`
   → Probability: 40.0%, American: +150

### Workflow: Monte Carlo Risk Analysis

Simulate portfolio outcomes from historical bet returns.

1. `monte_carlo_sim --returns=0.08,-0.04,0.06,-0.03,0.07 --n_simulations=10000 --initial_bankroll=1000`
2. Review: P(profit), P(ruin), mean/median final value, drawdown stats.

### Workflow: Drawdown Analysis

Analyze worst-case peak-to-trough losses from a wealth series.

1. `max_drawdown --values=1000,1080,1040,1100,1050,1120,980`
2. Review: max drawdown %, peak/trough values and indices.

## Examples

User: "Is there edge on the Lakers game? ESPN has them at -150 and Polymarket has them at 52 cents"
1. `devig --odds=-150,+130 --format=american` → Fair home prob ~58%
2. `find_edge --fair_prob=0.58 --market_prob=0.52` → Edge ~6%, positive EV
3. `kelly_criterion --fair_prob=0.58 --market_prob=0.52` → Kelly fraction
4. Present: edge, EV per dollar, recommended bet size as % of bankroll

User: "What are the true odds for this spread? Both sides are -110"
1. `devig --odds=-110,-110 --format=american`
2. Present: each side is 50% fair probability, vig is ~4.5%

User: "Convert -200 to implied probability"
1. `convert_odds --odds=-200 --from_format=american`
2. Present: 66.7% implied probability, 1.50 decimal odds

User: "Run a simulation on my betting returns"
1. `monte_carlo_sim --returns=0.12,-0.08,0.05,-0.03,0.09,-0.06,0.07 --n_simulations=10000`
2. Present: distribution of outcomes, P(profit), risk of ruin, drawdown stats

## Key Concepts

- **Vig/Juice**: The sportsbook's margin. A -110/-110 line implies 52.4% + 52.4% = 104.8% total, meaning 4.8% overround. De-vigging removes this to get fair probabilities.
- **Edge**: The difference between your estimated true probability and the market price. Positive edge = profitable in expectation.
- **Kelly Criterion**: Optimal bet sizing that maximizes long-term growth. f* = (fair_prob - market_prob) / (1 - market_prob).
- **Expected Value (EV)**: Average return per dollar bet. EV = fair_prob / market_prob - 1.
- **Maximum Drawdown**: Worst peak-to-trough decline in a wealth series. Measures downside risk.

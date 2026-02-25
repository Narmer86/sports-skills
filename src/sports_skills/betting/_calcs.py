"""Betting analysis — odds conversion, de-vigging, edge detection, Kelly, Monte Carlo.

Pure-computation module (no network calls). Uses stdlib only (math, random).
Works with odds from any source: ESPN (American), Polymarket (decimal prob),
Kalshi (integer prob), or raw decimal odds.

Functions:
1. convert_odds     — convert between American, decimal, and probability formats
2. devig            — strip vig/juice from sportsbook odds to get fair probabilities
3. find_edge        — compare fair probability to market price, compute edge + EV
4. kelly_criterion  — optimal bet sizing from two probabilities (no user estimation)
5. monte_carlo_sim  — simulate N wealth paths via resampling
6. max_drawdown     — worst peak-to-trough loss from a wealth series
7. evaluate_bet     — all-in-one: book odds + market price → full risk profile
"""

from __future__ import annotations

import random

# ============================================================
# Response Helpers
# ============================================================


def _success(data, message=""):
    return {"status": True, "data": data, "message": message}


def _error(message, data=None):
    return {"status": False, "data": data, "message": message}


# ============================================================
# Internal: American odds ↔ implied probability
# ============================================================


def _american_to_prob(odds: float) -> float:
    """Convert American odds to implied probability (0-1)."""
    if odds < 0:
        return -odds / (-odds + 100)
    elif odds > 0:
        return 100 / (odds + 100)
    else:
        # odds == 0 is invalid in American format, treat as even
        return 0.5


def _prob_to_american(prob: float) -> float:
    """Convert implied probability (0-1) to American odds."""
    if prob <= 0 or prob >= 1:
        return 0.0
    if prob >= 0.5:
        return -(prob / (1 - prob)) * 100
    else:
        return ((1 - prob) / prob) * 100


def _decimal_to_prob(odds: float) -> float:
    """Convert decimal odds (e.g. 2.5) to implied probability."""
    if odds <= 0:
        return 0.0
    return 1.0 / odds


def _prob_to_decimal(prob: float) -> float:
    """Convert implied probability to decimal odds."""
    if prob <= 0:
        return 0.0
    return 1.0 / prob


# ============================================================
# 1. Convert Odds
# ============================================================


def convert_odds(request_data: dict) -> dict:
    """Convert odds between American, decimal, and probability formats.

    Params:
        odds (float): The odds value to convert.
        from_format (str): Source format — "american", "decimal", or "probability".
    """
    params = request_data.get("params", {})
    try:
        odds = float(params.get("odds", 0))
    except (TypeError, ValueError) as e:
        return _error(f"Invalid odds value: {e}")

    from_format = str(params.get("from_format", "american")).lower()

    if from_format == "american":
        prob = _american_to_prob(odds)
        decimal_odds = _prob_to_decimal(prob)
        american = odds
    elif from_format == "decimal":
        if odds <= 1.0:
            return _error("Decimal odds must be greater than 1.0")
        prob = _decimal_to_prob(odds)
        american = _prob_to_american(prob)
        decimal_odds = odds
    elif from_format == "probability":
        if not 0 < odds < 1:
            return _error("Probability must be between 0 and 1 (exclusive)")
        prob = odds
        american = _prob_to_american(prob)
        decimal_odds = _prob_to_decimal(prob)
    else:
        return _error(
            f"Unknown format '{from_format}'. Use 'american', 'decimal', or 'probability'"
        )

    return _success(
        {
            "implied_probability": round(prob, 6),
            "american": round(american, 1),
            "decimal": round(decimal_odds, 4),
            "from_format": from_format,
            "input_odds": odds,
        },
        f"Implied probability: {prob:.1%}",
    )


# ============================================================
# 2. De-vig
# ============================================================


def devig(request_data: dict) -> dict:
    """Remove vig/juice from sportsbook odds to get fair probabilities.

    Uses the multiplicative (proportional) method:
    fair_prob[i] = raw_prob[i] / sum(raw_probs)

    Params:
        odds (str): Comma-separated odds for all outcomes
                     (e.g. "-150,+130" for a 2-way, or "-110,-110" for spread/total).
        format (str): Odds format — "american" (default), "decimal", or "probability".
    """
    params = request_data.get("params", {})
    raw = params.get("odds", "")
    if not raw:
        return _error("odds is required (comma-separated, e.g. '-150,+130')")

    try:
        if isinstance(raw, str):
            odds_list = [float(o.strip()) for o in raw.split(",")]
        elif isinstance(raw, list):
            odds_list = [float(o) for o in raw]
        else:
            return _error("odds must be a comma-separated string or list")
    except (TypeError, ValueError) as e:
        return _error(f"Invalid odds format: {e}")

    if len(odds_list) < 2:
        return _error("Need at least 2 outcome odds to de-vig")

    fmt = str(params.get("format", "american")).lower()

    # Convert all to implied probabilities
    if fmt == "american":
        raw_probs = [_american_to_prob(o) for o in odds_list]
    elif fmt == "decimal":
        raw_probs = [_decimal_to_prob(o) for o in odds_list]
    elif fmt == "probability":
        raw_probs = list(odds_list)
    else:
        return _error(
            f"Unknown format '{fmt}'. Use 'american', 'decimal', or 'probability'"
        )

    if any(p <= 0 for p in raw_probs):
        return _error("All implied probabilities must be positive")

    overround = sum(raw_probs)
    fair_probs = [p / overround for p in raw_probs]
    vig_pct = (overround - 1.0) * 100

    outcomes = []
    for i, (odds_val, raw_p, fair_p) in enumerate(
        zip(odds_list, raw_probs, fair_probs)
    ):
        outcomes.append(
            {
                "outcome": i,
                "input_odds": odds_val,
                "implied_prob": round(raw_p, 6),
                "fair_prob": round(fair_p, 6),
                "fair_american": round(_prob_to_american(fair_p), 1),
            }
        )

    return _success(
        {
            "outcomes": outcomes,
            "overround": round(overround, 6),
            "vig_pct": round(vig_pct, 2),
            "format": fmt,
        },
        f"Vig: {vig_pct:.2f}% | Fair probs: {', '.join(f'{p:.1%}' for p in fair_probs)}",
    )


# ============================================================
# 3. Find Edge
# ============================================================


def find_edge(request_data: dict) -> dict:
    """Compare fair probability to market price — compute edge, EV, and Kelly.

    The agent provides both values from data it already has:
    - fair_prob: from de-vigged sportsbook odds (ESPN/DraftKings)
    - market_prob: from a prediction market (Polymarket, Kalshi)

    Params:
        fair_prob (float): True/fair probability of the outcome (0-1).
        market_prob (float): Market price / implied probability to bet at (0-1).
    """
    params = request_data.get("params", {})
    try:
        fair_prob = float(params.get("fair_prob", 0))
        market_prob = float(params.get("market_prob", 0))
    except (TypeError, ValueError) as e:
        return _error(f"Invalid parameters: {e}")

    if not 0 < fair_prob < 1:
        return _error("fair_prob must be between 0 and 1 (exclusive)")
    if not 0 < market_prob < 1:
        return _error("market_prob must be between 0 and 1 (exclusive)")

    edge = fair_prob - market_prob
    ev_per_dollar = fair_prob / market_prob - 1.0  # ROI per $1 bet
    kelly = (fair_prob - market_prob) / (1.0 - market_prob) if market_prob < 1 else 0.0

    if edge > 0:
        recommendation = "bet"
        rating = "positive edge"
    elif edge == 0:
        recommendation = "no bet"
        rating = "no edge"
    else:
        recommendation = "no bet"
        rating = "negative edge"

    return _success(
        {
            "edge": round(edge, 6),
            "edge_pct": f"{edge * 100:.2f}%",
            "ev_per_dollar": round(ev_per_dollar, 6),
            "kelly_fraction": round(kelly, 6),
            "fair_prob": fair_prob,
            "market_prob": market_prob,
            "recommendation": recommendation,
        },
        f"Edge: {edge * 100:.2f}% ({rating}) | EV: {ev_per_dollar * 100:.2f}% | Kelly: {kelly:.4f}",
    )


# ============================================================
# 4. Kelly Criterion
# ============================================================


def kelly_criterion(request_data: dict) -> dict:
    """Compute the Kelly fraction from fair probability and market probability.

    f* = (fair_prob - market_prob) / (1 - market_prob)

    Equivalent to the classical f* = (p*b - q) / b where:
      p = fair_prob, b = (1/market_prob) - 1

    Params:
        fair_prob (float): True/fair probability of winning (0-1).
        market_prob (float): Market price you'd buy at (0-1).
    """
    params = request_data.get("params", {})
    try:
        fair_prob = float(params.get("fair_prob", 0))
        market_prob = float(params.get("market_prob", 0))
    except (TypeError, ValueError) as e:
        return _error(f"Invalid parameters: {e}")

    if not 0 < fair_prob < 1:
        return _error("fair_prob must be between 0 and 1 (exclusive)")
    if not 0 < market_prob < 1:
        return _error("market_prob must be between 0 and 1 (exclusive)")

    edge = fair_prob - market_prob
    f_star = edge / (1.0 - market_prob)
    b = (1.0 / market_prob) - 1.0  # net odds equivalent
    ev_per_dollar = fair_prob / market_prob - 1.0

    return _success(
        {
            "kelly_fraction": round(f_star, 6),
            "edge": round(edge, 6),
            "ev_per_dollar": round(ev_per_dollar, 6),
            "fair_prob": fair_prob,
            "market_prob": market_prob,
            "net_odds": round(b, 4),
            "recommendation": "bet" if f_star > 0 else "no bet",
        },
        f"Kelly fraction: {f_star:.4f} ({'positive edge' if f_star > 0 else 'negative edge'})",
    )


# ============================================================
# 5. Monte Carlo Resampling
# ============================================================


def monte_carlo_sim(request_data: dict) -> dict:
    """Run Monte Carlo resampling on an empirical return set.

    Takes a set of historical returns and simulates N wealth paths by
    randomly resampling (with replacement) from those returns.

    Params:
        returns (str): Comma-separated returns as decimals (e.g. "0.08,-0.04,0.06,-0.03,0.07").
        n_simulations (int): Number of simulated paths (default: 10000).
        n_periods (int): Number of periods per path (default: length of returns).
        initial_bankroll (float): Starting bankroll (default: 1000).
        seed (int): Random seed for reproducibility (optional).
    """
    params = request_data.get("params", {})

    # Parse returns
    raw = params.get("returns", "")
    if not raw:
        return _error(
            "returns is required (comma-separated decimals, e.g. '0.08,-0.04,0.06')"
        )
    try:
        if isinstance(raw, str):
            returns = [float(r.strip()) for r in raw.split(",")]
        elif isinstance(raw, list):
            returns = [float(r) for r in raw]
        else:
            return _error("returns must be a comma-separated string or list of numbers")
    except (TypeError, ValueError) as e:
        return _error(f"Invalid returns format: {e}")

    if len(returns) < 2:
        return _error("Need at least 2 return values")

    n_sims = int(params.get("n_simulations", 10000))
    n_periods_raw = params.get("n_periods")
    n_periods = int(n_periods_raw) if n_periods_raw is not None else len(returns)
    bankroll = float(params.get("initial_bankroll", 1000.0))
    seed = params.get("seed")

    if n_sims < 1 or n_sims > 100000:
        return _error("n_simulations must be between 1 and 100,000")
    if n_periods < 1:
        return _error("n_periods must be >= 1")

    rng = random.Random(int(seed)) if seed is not None else random.Random()

    # Run simulations
    final_values = []
    max_drawdowns = []
    paths_summary = []  # store subset for visualization

    for j in range(n_sims):
        # Resample returns with replacement
        path_returns = [rng.choice(returns) for _ in range(n_periods)]

        # Build wealth path
        wealth = [bankroll]
        for r in path_returns:
            wealth.append(wealth[-1] * (1.0 + r))

        final_values.append(wealth[-1])

        # Compute max drawdown for this path
        peak = wealth[0]
        mdd = 0.0
        for w in wealth[1:]:
            if w > peak:
                peak = w
            dd = (w - peak) / peak if peak != 0 else 0.0
            if dd < mdd:
                mdd = dd
        max_drawdowns.append(mdd)

        # Store first 20 paths for visualization
        if j < 20:
            paths_summary.append(
                {
                    "path_id": j,
                    "final_value": round(wealth[-1], 2),
                    "max_drawdown": round(mdd, 4),
                    "values": [
                        round(w, 2) for w in wealth[:: max(1, len(wealth) // 50)]
                    ],
                }
            )

    # Compute statistics
    final_values.sort()
    max_drawdowns.sort()
    n = len(final_values)

    mean_final = sum(final_values) / n
    median_final = final_values[n // 2]
    p5 = final_values[int(n * 0.05)]
    p25 = final_values[int(n * 0.25)]
    p75 = final_values[int(n * 0.75)]
    p95 = final_values[int(n * 0.95)]
    prob_profit = sum(1 for v in final_values if v > bankroll) / n
    prob_ruin = sum(1 for v in final_values if v <= bankroll * 0.1) / n

    mean_mdd = sum(max_drawdowns) / n
    median_mdd = max_drawdowns[n // 2]
    worst_mdd = max_drawdowns[0]  # most negative
    p5_mdd = max_drawdowns[int(n * 0.05)]

    return _success(
        {
            "simulations": n_sims,
            "periods": n_periods,
            "initial_bankroll": bankroll,
            "returns_used": returns,
            "final_value": {
                "mean": round(mean_final, 2),
                "median": round(median_final, 2),
                "p5": round(p5, 2),
                "p25": round(p25, 2),
                "p75": round(p75, 2),
                "p95": round(p95, 2),
                "min": round(final_values[0], 2),
                "max": round(final_values[-1], 2),
            },
            "probability_of_profit": round(prob_profit, 4),
            "probability_of_ruin": round(prob_ruin, 4),
            "max_drawdown": {
                "mean": round(mean_mdd, 4),
                "median": round(median_mdd, 4),
                "worst": round(worst_mdd, 4),
                "p5": round(p5_mdd, 4),
            },
            "sample_paths": paths_summary,
        },
        f"Simulated {n_sims} paths over {n_periods} periods",
    )


# ============================================================
# 6. Maximum Drawdown (standalone)
# ============================================================


def max_drawdown(request_data: dict) -> dict:
    """Compute the maximum drawdown from a wealth/equity series.

    Peak: Pt = max(s<=t) Ws
    Drawdown: DDt = (Wt - Pt) / Pt
    MDD = min(DDt)

    Params:
        values (str): Comma-separated wealth values (e.g. "1000,1080,1040,1100,1050").
    """
    params = request_data.get("params", {})
    raw = params.get("values", "")
    if not raw:
        return _error("values is required (comma-separated wealth series)")
    try:
        if isinstance(raw, str):
            values = [float(v.strip()) for v in raw.split(",")]
        elif isinstance(raw, list):
            values = [float(v) for v in raw]
        else:
            return _error("values must be a comma-separated string or list")
    except (TypeError, ValueError) as e:
        return _error(f"Invalid values format: {e}")

    if len(values) < 2:
        return _error("Need at least 2 values")

    peak = values[0]
    mdd = 0.0
    mdd_peak_idx = 0
    mdd_trough_idx = 0
    current_peak_idx = 0

    drawdown_series = []
    for i, w in enumerate(values):
        if w > peak:
            peak = w
            current_peak_idx = i
        dd = (w - peak) / peak if peak != 0 else 0.0
        drawdown_series.append(round(dd, 6))
        if dd < mdd:
            mdd = dd
            mdd_peak_idx = current_peak_idx
            mdd_trough_idx = i

    return _success(
        {
            "max_drawdown": round(mdd, 6),
            "max_drawdown_pct": f"{mdd * 100:.2f}%",
            "peak_value": round(values[mdd_peak_idx], 2),
            "trough_value": round(values[mdd_trough_idx], 2),
            "peak_index": mdd_peak_idx,
            "trough_index": mdd_trough_idx,
            "drawdown_series": drawdown_series,
        },
        f"Max drawdown: {mdd * 100:.2f}%",
    )


# ============================================================
# 7. Evaluate Bet (all-in-one)
# ============================================================


def evaluate_bet(request_data: dict) -> dict:
    """Full bet evaluation: convert book odds → de-vig → edge → Kelly → Monte Carlo.

    Takes sportsbook odds and a prediction market price, computes everything
    without requiring the user to estimate probabilities.

    Params:
        book_odds (str): Comma-separated sportsbook odds for all outcomes
                         (e.g. "-150,+130" for a 2-way market).
        market_prob (float): Prediction market price for the outcome you're
                             evaluating (0-1). This is the first outcome in book_odds.
        book_format (str): Format of book_odds — "american" (default), "decimal",
                           or "probability".
        outcome (int): Which outcome to evaluate (0-indexed, default: 0 = first).
        returns (str): Optional historical returns for Monte Carlo simulation.
        n_simulations (int): Monte Carlo paths (default: 10000).
        n_periods (int): Periods per path (default: length of returns).
        initial_bankroll (float): Starting bankroll (default: 1000).
        seed (int): Random seed (optional).
    """
    params = request_data.get("params", {})

    # Step 1: De-vig the book odds
    book_odds = params.get("book_odds", "")
    if not book_odds:
        return _error("book_odds is required (e.g. '-150,+130')")

    book_format = str(params.get("book_format", "american")).lower()
    devig_result = devig({"params": {"odds": book_odds, "format": book_format}})
    if not devig_result["status"]:
        return devig_result

    # Step 2: Get fair probability for the target outcome
    outcome_idx = int(params.get("outcome", 0))
    outcomes = devig_result["data"]["outcomes"]
    if outcome_idx < 0 or outcome_idx >= len(outcomes):
        return _error(
            f"outcome index {outcome_idx} out of range (0-{len(outcomes) - 1})"
        )
    fair_prob = outcomes[outcome_idx]["fair_prob"]

    # Step 3: Get market probability
    try:
        market_prob = float(params.get("market_prob", 0))
    except (TypeError, ValueError) as e:
        return _error(f"Invalid market_prob: {e}")

    if not 0 < market_prob < 1:
        return _error("market_prob must be between 0 and 1 (exclusive)")

    # Step 4: Edge + Kelly
    edge_result = find_edge(
        {"params": {"fair_prob": fair_prob, "market_prob": market_prob}}
    )
    if not edge_result["status"]:
        return edge_result

    # Step 5: Monte Carlo (if returns provided)
    mc_result = None
    if params.get("returns"):
        mc_result = monte_carlo_sim(
            {
                "params": {
                    "returns": params.get("returns"),
                    "n_simulations": params.get("n_simulations", 10000),
                    "n_periods": params.get("n_periods"),
                    "initial_bankroll": params.get("initial_bankroll", 1000),
                    "seed": params.get("seed"),
                }
            }
        )
        if not mc_result["status"]:
            return mc_result

    # Build response
    data = {
        "devig": devig_result["data"],
        "edge": edge_result["data"],
    }
    if mc_result:
        data["monte_carlo"] = mc_result["data"]

    # Summary
    edge = edge_result["data"]["edge"]
    kelly = edge_result["data"]["kelly_fraction"]
    ev = edge_result["data"]["ev_per_dollar"]

    summary_parts = [
        f"Fair: {fair_prob:.1%}",
        f"Market: {market_prob:.1%}",
        f"Edge: {edge * 100:.2f}%",
        f"Kelly: {kelly:.4f}",
        f"EV: {ev * 100:.2f}%",
    ]
    if mc_result:
        prob_profit = mc_result["data"]["probability_of_profit"]
        mean_mdd = mc_result["data"]["max_drawdown"]["mean"]
        summary_parts.append(f"P(profit): {prob_profit:.1%}")
        summary_parts.append(f"Mean MDD: {mean_mdd:.1%}")

    recommendation = "no bet"
    if kelly > 0:
        if mc_result and mc_result["data"]["probability_of_profit"] > 0.5 or not mc_result:
            recommendation = "bet"

    data["recommendation"] = recommendation
    data["summary"] = " | ".join(summary_parts)

    return _success(data, data["summary"])

"""Betting analysis — odds conversion, de-vigging, edge detection, Kelly, Monte Carlo.

Source-agnostic: works with odds from ESPN, Polymarket, Kalshi, or any sportsbook.
Pure computation — no network calls, no auth required.
"""

from __future__ import annotations

from sports_skills.betting._calcs import convert_odds as _convert_odds
from sports_skills.betting._calcs import devig as _devig
from sports_skills.betting._calcs import evaluate_bet as _evaluate_bet
from sports_skills.betting._calcs import find_edge as _find_edge
from sports_skills.betting._calcs import kelly_criterion as _kelly_criterion
from sports_skills.betting._calcs import max_drawdown as _max_drawdown
from sports_skills.betting._calcs import monte_carlo_sim as _monte_carlo_sim


def _req(**kwargs):
    """Build request_data dict from kwargs."""
    return {"params": {k: v for k, v in kwargs.items() if v is not None}}


def convert_odds(*, odds: float, from_format: str = "american") -> dict:
    """Convert odds between American, decimal, and probability formats."""
    return _convert_odds(_req(odds=odds, from_format=from_format))


def devig(*, odds: str, format: str = "american") -> dict:
    """Remove vig/juice from sportsbook odds to get fair probabilities."""
    return _devig(_req(odds=odds, format=format))


def find_edge(*, fair_prob: float, market_prob: float) -> dict:
    """Compare fair probability to market price — compute edge, EV, and Kelly."""
    return _find_edge(_req(fair_prob=fair_prob, market_prob=market_prob))


def kelly_criterion(*, fair_prob: float, market_prob: float) -> dict:
    """Compute the Kelly fraction from fair and market probabilities."""
    return _kelly_criterion(_req(fair_prob=fair_prob, market_prob=market_prob))


def monte_carlo_sim(
    *,
    returns: str,
    n_simulations: int = 10000,
    n_periods: int | None = None,
    initial_bankroll: float = 1000.0,
    seed: int | None = None,
) -> dict:
    """Run Monte Carlo resampling on an empirical return set."""
    return _monte_carlo_sim(
        _req(
            returns=returns,
            n_simulations=n_simulations,
            n_periods=n_periods,
            initial_bankroll=initial_bankroll,
            seed=seed,
        )
    )


def max_drawdown(*, values: str) -> dict:
    """Compute maximum drawdown from a wealth/equity series."""
    return _max_drawdown(_req(values=values))


def evaluate_bet(
    *,
    book_odds: str,
    market_prob: float,
    book_format: str = "american",
    outcome: int = 0,
    returns: str | None = None,
    n_simulations: int = 10000,
    n_periods: int | None = None,
    initial_bankroll: float = 1000.0,
    seed: int | None = None,
) -> dict:
    """Full bet evaluation: book odds + market price → edge → Kelly → Monte Carlo."""
    return _evaluate_bet(
        _req(
            book_odds=book_odds,
            market_prob=market_prob,
            book_format=book_format,
            outcome=outcome,
            returns=returns,
            n_simulations=n_simulations,
            n_periods=n_periods,
            initial_bankroll=initial_bankroll,
            seed=seed,
        )
    )

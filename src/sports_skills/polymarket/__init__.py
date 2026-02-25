"""Polymarket sports prediction markets — prices, order books, events, and series.

Uses Gamma API (public, no auth) and CLOB API (public reads) via stdlib only.
"""

from __future__ import annotations

from sports_skills.polymarket._connector import (
    get_event_details as _get_event_details,
)
from sports_skills.polymarket._connector import (
    get_last_trade_price as _get_last_trade_price,
)
from sports_skills.polymarket._connector import (
    get_market_details as _get_market_details,
)
from sports_skills.polymarket._connector import (
    get_market_prices as _get_market_prices,
)
from sports_skills.polymarket._connector import (
    get_order_book as _get_order_book,
)
from sports_skills.polymarket._connector import (
    get_price_history as _get_price_history,
)
from sports_skills.polymarket._connector import (
    get_series as _get_series,
)
from sports_skills.polymarket._connector import (
    get_sports_events as _get_sports_events,
)
from sports_skills.polymarket._connector import (
    get_sports_market_types as _get_sports_market_types,
)
from sports_skills.polymarket._connector import (
    get_sports_markets as _get_sports_markets,
)
from sports_skills.polymarket._connector import (
    search_markets as _search_markets,
)


def _req(**kwargs):
    """Build request_data dict from kwargs."""
    return {"params": {k: v for k, v in kwargs.items() if v is not None}}


def get_sports_markets(
    *,
    limit: int = 50,
    offset: int = 0,
    sports_market_types: str | None = None,
    game_id: str | None = None,
    active: bool = True,
    closed: bool = False,
    order: str = "volume",
    ascending: bool = False,
) -> dict:
    """Get active sports prediction markets with optional filtering."""
    return _get_sports_markets(
        _req(
            limit=limit,
            offset=offset,
            sports_market_types=sports_market_types,
            game_id=game_id,
            active=active,
            closed=closed,
            order=order,
            ascending=ascending,
        )
    )


def get_sports_events(
    *,
    limit: int = 50,
    offset: int = 0,
    active: bool = True,
    closed: bool = False,
    order: str = "volume",
    ascending: bool = False,
    series_id: str | None = None,
) -> dict:
    """Get sports events (each event groups related markets)."""
    return _get_sports_events(
        _req(
            limit=limit,
            offset=offset,
            active=active,
            closed=closed,
            order=order,
            ascending=ascending,
            series_id=series_id,
        )
    )


def get_series(*, limit: int = 100, offset: int = 0) -> dict:
    """Get all series (leagues, recurring event groups)."""
    return _get_series(_req(limit=limit, offset=offset))


def get_market_details(
    *, market_id: str | None = None, slug: str | None = None
) -> dict:
    """Get detailed information for a specific market."""
    return _get_market_details(_req(market_id=market_id, slug=slug))


def get_event_details(*, event_id: str | None = None, slug: str | None = None) -> dict:
    """Get detailed information for a specific event (includes nested markets)."""
    return _get_event_details(_req(event_id=event_id, slug=slug))


def get_market_prices(
    *, token_id: str | None = None, token_ids: list[str] | None = None
) -> dict:
    """Get current prices for one or more markets from the CLOB API."""
    return _get_market_prices(_req(token_id=token_id, token_ids=token_ids))


def get_order_book(*, token_id: str) -> dict:
    """Get the full order book for a market."""
    return _get_order_book(_req(token_id=token_id))


def get_sports_market_types() -> dict:
    """Get all valid sports market types (moneyline, spreads, totals, props, etc.)."""
    return _get_sports_market_types(_req())


def search_markets(
    *,
    query: str | None = None,
    sports_market_types: str | None = None,
    tag_id: int | None = None,
    limit: int = 20,
) -> dict:
    """Find sports markets by keyword and filters."""
    return _search_markets(
        _req(
            query=query,
            sports_market_types=sports_market_types,
            tag_id=tag_id,
            limit=limit,
        )
    )


def get_price_history(
    *, token_id: str, interval: str = "max", fidelity: int = 120
) -> dict:
    """Get historical price data for a market over time."""
    return _get_price_history(
        _req(token_id=token_id, interval=interval, fidelity=fidelity)
    )


def get_last_trade_price(*, token_id: str) -> dict:
    """Get the most recent trade price for a market."""
    return _get_last_trade_price(_req(token_id=token_id))

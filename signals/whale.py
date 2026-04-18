"""Whale — copy-trade dominant wallets.

Intent: a small set of wallets are consistently profitable per category.
Maintain a watchlist keyed by category and fire when a tracked whale opens
a fresh position. The tweet cited six example wallets — state.whale_list
should be curated and updated periodically.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class WhaleSignal(Signal):
    name = "whale"

    def __init__(self, min_position_usd: float = 100.0):
        self.min_position_usd = min_position_usd

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: watch state.whale_trades stream (from Polymarket chain events)
        # TODO: if a tracked whale opens position > min on this market, fire same side
        return None

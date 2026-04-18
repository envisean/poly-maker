"""Category — market-class gating.

Intent: different market categories have different edge profiles (politics
mean-reverts slower than crypto; sports resolves near deadlines; weather
follows oracle feeds). This detector applies category-specific rules and
fires when the pattern matches the category's known edge.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class CategorySignal(Signal):
    name = "category"

    def __init__(self, rules: Optional[dict] = None):
        # rules example: {"politics": {...}, "crypto": {...}, "sports": {...}}
        self.rules = rules or {}

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: classify market.category
        # TODO: look up per-category rule (price band, hold-time, volatility floor)
        # TODO: fire if current market state matches the category's edge pattern
        return None

"""Disposition — directional conviction from order flow vs price.

Intent: when cumulative buy-pressure vs sell-pressure diverges from price
movement over window W by N standard deviations, fire toward the pressured
side. Catches markets where flow is loading up before price catches up.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class DispositionSignal(Signal):
    name = "disposition"

    def __init__(self, window_sec: int = 300, sigma_threshold: float = 2.0):
        self.window_sec = window_sec
        self.sigma_threshold = sigma_threshold

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: compute flow_pressure = buy_size - sell_size over window
        # TODO: compute price_delta over same window
        # TODO: fire YES if flow_pressure > 0 and price_delta < 0 - sigma*std
        # TODO: fire NO if flow_pressure < 0 and price_delta > 0 + sigma*std
        return None

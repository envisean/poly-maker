"""Velocity — rate of change of implied odds.

Intent: sharp moves (large Δprice / Δt) often overshoot. Fire contrarian
against velocity spikes that exceed the market's historical velocity
distribution, scaled by liquidity to avoid thin-book false positives.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class VelocitySignal(Signal):
    name = "velocity"

    def __init__(self, lookback_sec: int = 60, z_threshold: float = 3.0):
        self.lookback_sec = lookback_sec
        self.z_threshold = z_threshold

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: price_velocity = (price_now - price_lookback) / lookback_sec
        # TODO: z = (price_velocity - rolling_mean) / rolling_std
        # TODO: if |z| > z_threshold and liquidity >= min, fire contrarian
        return None

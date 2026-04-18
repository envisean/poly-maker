"""Theta — time decay / settlement proximity.

Intent: as resolution approaches, mispricings compress and edge decays.
Fire only when time-to-resolution is in a productive band (long enough
to hold, short enough that variance is bounded).
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class ThetaSignal(Signal):
    name = "theta"

    def __init__(self, min_hours: float = 1.0, max_hours: float = 72.0):
        self.min_hours = min_hours
        self.max_hours = max_hours

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: compute hours until market.resolution_ts
        # TODO: if inside [min_hours, max_hours] and price in mispricing band, fire
        return None

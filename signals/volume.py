"""Volume — abnormal volume vs rolling baseline.

Intent: volume spikes often precede price discovery. Fire in the direction
of the aggressor side when volume exceeds the rolling baseline by N
standard deviations.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class VolumeSignal(Signal):
    name = "volume"

    def __init__(self, window_sec: int = 900, z_threshold: float = 2.5):
        self.window_sec = window_sec
        self.z_threshold = z_threshold

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: compute 1m volume and rolling baseline over window_sec
        # TODO: z-score; if > threshold, inspect aggressor side (buy vs sell prints)
        # TODO: fire in aggressor direction
        return None

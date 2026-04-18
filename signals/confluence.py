"""Confluence engine — enter only when >= N detectors agree on direction.

This is the real glue: detectors are independent and fire in parallel; a
trade is proposed only when their outputs converge on the same side within
a single evaluation window.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

from .base import Signal, SignalFire


@dataclass
class ConfluenceHit:
    market_id: str
    direction: str
    fires: List[SignalFire] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.fires)

    @property
    def mean_confidence(self) -> float:
        if not self.fires:
            return 0.0
        return sum(f.confidence for f in self.fires) / len(self.fires)


class ConfluenceEngine:
    """Evaluates all detectors on a market and emits a hit on threshold agreement."""

    def __init__(self, signals: Iterable[Signal], threshold: int = 3):
        self.signals = list(signals)
        self.threshold = threshold

    def evaluate(self, market: dict, state: Any) -> Optional[ConfluenceHit]:
        by_direction: dict[str, list[SignalFire]] = defaultdict(list)
        for sig in self.signals:
            fire = sig.detect(market, state)
            if fire is not None:
                by_direction[fire.direction].append(fire)

        if not by_direction:
            return None

        direction, fires = max(by_direction.items(), key=lambda kv: len(kv[1]))
        if len(fires) < self.threshold:
            return None

        return ConfluenceHit(
            market_id=market.get("id") or market.get("condition_id", ""),
            direction=direction,
            fires=fires,
        )

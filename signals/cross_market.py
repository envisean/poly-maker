"""Cross-market — price deltas across venues for equivalent questions.

Intent: when Polymarket prices drift meaningfully from Kalshi / PredictIt /
Manifold / BTC oracle (for crypto questions), arb the gap. The detector
needs a mapping of cross-venue question equivalence — that mapping is the
hard part and lives in state.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class CrossMarketSignal(Signal):
    name = "cross_market"

    def __init__(self, delta_threshold_cents: float = 5.0):
        self.delta_threshold_cents = delta_threshold_cents

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: lookup equivalent markets on Kalshi/PredictIt/Manifold
        # TODO: for crypto-priced questions, fetch BTC/ETH oracle price
        # TODO: compute delta in cents; if > threshold and venue liquidity OK, fire
        return None

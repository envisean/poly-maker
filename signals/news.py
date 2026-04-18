"""News — feed-to-market lag detector.

Intent: authoritative feeds (NOAA / AP / Reuters / CoinGecko) sometimes
publish resolving information before market odds adjust. Fire on the side
of the news during the lag window.

Source feeds live in state.news_feeds; this detector only checks whether
a fresh relevant item exists and whether market price has already moved.
"""
from __future__ import annotations

from typing import Any, Optional

from .base import Signal, SignalFire


class NewsSignal(Signal):
    name = "news"

    def __init__(self, max_lag_sec: int = 120):
        self.max_lag_sec = max_lag_sec

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        # TODO: match market keywords against recent feed items (state.news_feeds)
        # TODO: compute news_ts vs market last-move ts
        # TODO: if news_ts is within lag window and price hasn't moved, fire
        return None

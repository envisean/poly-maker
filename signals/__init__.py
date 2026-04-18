"""Parallel detector grid for Polymarket.

Eight detectors run on every market tick. The ConfluenceEngine fires a trade
proposal when >= N detectors agree on a direction within the same window.

Detectors:
    disposition   — order-flow pressure vs price
    category      — market-category gating (politics/crypto/sports rules)
    velocity      — rate-of-change of implied odds
    cross_market  — Polymarket vs Kalshi/PredictIt/Manifold/BTC oracle
    news          — news feed → market reaction lag
    volume        — abnormal volume vs rolling baseline
    whale         — copy dominant wallets by category
    theta         — time decay / settlement proximity
"""
from .base import Signal, SignalFire
from .confluence import ConfluenceEngine, ConfluenceHit

__all__ = ["Signal", "SignalFire", "ConfluenceEngine", "ConfluenceHit"]

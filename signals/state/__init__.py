"""Persistent state backend for the signal grid.

Layered on top of poly-maker's in-memory `poly_data.global_state`:
- global_state   → hot cache for the MM loop (unchanged)
- signals.state  → durable, queryable layer for detectors + audit + replay
"""
from .db import connect, init_schema
from .recorder import Recorder
from .market import MarketState
from .global_store import GlobalState

__all__ = ["connect", "init_schema", "Recorder", "MarketState", "GlobalState"]

"""Signal protocol — the contract every detector implements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SignalFire:
    """A detector's output when it triggers on a market tick."""

    signal: str          # detector name (e.g. "velocity")
    market_id: str
    direction: str       # "YES" or "NO"
    confidence: float    # 0.0 - 1.0
    evidence: dict = field(default_factory=dict)


class Signal(ABC):
    """Base class for every detector in the parallel grid.

    Detectors are instantiated once per bot. They may be stateful (e.g.
    rolling baselines, wallet copy-lists) — state should be loaded in
    __init__ and refreshed via update() if needed.
    """

    name: str = "unnamed"

    def update(self, state: Any) -> None:
        """Optional hook to refresh internal state (rolling windows, etc)."""
        return None

    @abstractmethod
    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        """Return a SignalFire if this detector triggers on this tick, else None."""
        raise NotImplementedError

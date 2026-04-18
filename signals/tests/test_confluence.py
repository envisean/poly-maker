from typing import Any, Optional

from signals.base import Signal, SignalFire
from signals.confluence import ConfluenceEngine


class _Fake(Signal):
    def __init__(self, name: str, fire: Optional[SignalFire]):
        self.name = name
        self._fire = fire

    def detect(self, market: dict, state: Any) -> Optional[SignalFire]:
        return self._fire


def _fire(name: str, direction: str, conf: float = 0.7) -> SignalFire:
    return SignalFire(signal=name, market_id="m1", direction=direction,
                      confidence=conf, evidence={})


def test_no_fires_returns_none():
    engine = ConfluenceEngine([_Fake("a", None), _Fake("b", None)], threshold=3)
    assert engine.evaluate({"id": "m1"}, None) is None


def test_below_threshold_returns_none():
    engine = ConfluenceEngine([
        _Fake("a", _fire("a", "YES")),
        _Fake("b", _fire("b", "YES")),
    ], threshold=3)
    assert engine.evaluate({"id": "m1"}, None) is None


def test_threshold_met_returns_hit():
    engine = ConfluenceEngine([
        _Fake("a", _fire("a", "YES")),
        _Fake("b", _fire("b", "YES")),
        _Fake("c", _fire("c", "YES")),
    ], threshold=3)
    hit = engine.evaluate({"id": "m1"}, None)
    assert hit is not None
    assert hit.direction == "YES"
    assert hit.count == 3


def test_strongest_direction_wins():
    engine = ConfluenceEngine([
        _Fake("a", _fire("a", "YES")),
        _Fake("b", _fire("b", "YES")),
        _Fake("c", _fire("c", "YES")),
        _Fake("d", _fire("d", "NO")),
        _Fake("e", _fire("e", "NO")),
    ], threshold=3)
    hit = engine.evaluate({"id": "m1"}, None)
    assert hit is not None
    assert hit.direction == "YES"
    assert hit.count == 3


def test_mean_confidence():
    engine = ConfluenceEngine([
        _Fake("a", _fire("a", "YES", 0.6)),
        _Fake("b", _fire("b", "YES", 0.8)),
        _Fake("c", _fire("c", "YES", 1.0)),
    ], threshold=3)
    hit = engine.evaluate({"id": "m1"}, None)
    assert hit is not None
    assert abs(hit.mean_confidence - 0.8) < 1e-9

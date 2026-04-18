"""Shape tests — every stub is importable and returns None from detect()."""
from signals.disposition import DispositionSignal
from signals.category import CategorySignal
from signals.velocity import VelocitySignal
from signals.cross_market import CrossMarketSignal
from signals.news import NewsSignal
from signals.volume import VolumeSignal
from signals.whale import WhaleSignal
from signals.theta import ThetaSignal


ALL_STUBS = [
    DispositionSignal,
    CategorySignal,
    VelocitySignal,
    CrossMarketSignal,
    NewsSignal,
    VolumeSignal,
    WhaleSignal,
    ThetaSignal,
]


def test_all_stubs_instantiate_with_defaults():
    for cls in ALL_STUBS:
        inst = cls()
        assert inst.name
        assert inst.detect({"id": "m1"}, None) is None


def test_unique_names():
    names = [cls().name for cls in ALL_STUBS]
    assert len(names) == len(set(names))
    assert set(names) == {
        "disposition", "category", "velocity", "cross_market",
        "news", "volume", "whale", "theta",
    }

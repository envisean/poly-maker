"""End-to-end tests for the state layer. Uses in-memory DuckDB."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from signals.state import GlobalState, MarketState, Recorder, connect, init_schema


@pytest.fixture()
def conn():
    c = connect(":memory:")
    init_schema(c)
    yield c
    c.close()


@pytest.fixture()
def recorder(conn):
    r = Recorder(conn, flush_interval_sec=0.05, flush_batch_size=50)
    yield r
    r.stop()


def test_recorder_flush_writes_ticks(conn, recorder):
    recorder.tick("m1", yes_price=0.50, best_bid=0.49, best_ask=0.51)
    recorder.tick("m1", yes_price=0.52, best_bid=0.51, best_ask=0.53)
    recorder.flush()
    count = conn.execute("SELECT COUNT(*) FROM market_ticks WHERE market_id = 'm1'").fetchone()[0]
    assert count == 2


def test_recorder_background_thread_flushes(conn, recorder):
    recorder.start()
    recorder.tick("m1", yes_price=0.50)
    time.sleep(0.2)  # let the thread flush
    count = conn.execute("SELECT COUNT(*) FROM market_ticks").fetchone()[0]
    assert count == 1


def test_market_state_recent_ticks_windowed(conn, recorder):
    now = datetime.now(timezone.utc)
    # 100s ago, 30s ago, 5s ago
    recorder.tick("m1", yes_price=0.40, ts=now - timedelta(seconds=100))
    recorder.tick("m1", yes_price=0.50, ts=now - timedelta(seconds=30))
    recorder.tick("m1", yes_price=0.55, ts=now - timedelta(seconds=5))
    recorder.flush()
    ms = MarketState(conn)
    assert len(ms.recent_ticks("m1", window_sec=60, now=now)) == 2
    assert len(ms.recent_ticks("m1", window_sec=200, now=now)) == 3


def test_market_state_volume_summary(conn, recorder):
    now = datetime.now(timezone.utc)
    recorder.trade_print("m1", "BUY", 0.50, 10, ts=now - timedelta(seconds=20))
    recorder.trade_print("m1", "SELL", 0.50, 4, ts=now - timedelta(seconds=10))
    recorder.trade_print("m1", "BUY", 0.51, 6, ts=now - timedelta(seconds=5))
    recorder.flush()
    summary = MarketState(conn).volume_summary("m1", window_sec=60, now=now)
    assert summary["total"] == 20
    assert summary["buy"] == 16
    assert summary["sell"] == 4
    assert summary["prints"] == 3


def test_market_state_price_delta(conn, recorder):
    now = datetime.now(timezone.utc)
    recorder.tick("m1", yes_price=0.40, ts=now - timedelta(seconds=50))
    recorder.tick("m1", yes_price=0.55, ts=now - timedelta(seconds=5))
    recorder.flush()
    assert MarketState(conn).price_delta("m1", window_sec=60, now=now) == pytest.approx(0.15)


def test_market_state_price_delta_insufficient(conn, recorder):
    now = datetime.now(timezone.utc)
    recorder.tick("m1", yes_price=0.40, ts=now - timedelta(seconds=5))
    recorder.flush()
    assert MarketState(conn).price_delta("m1", window_sec=60, now=now) is None


def test_global_state_roundtrip(conn):
    gs = GlobalState(conn)
    assert gs.get("missing") is None
    gs.set("k", {"a": 1, "b": [2, 3]})
    assert gs.get("k") == {"a": 1, "b": [2, 3]}
    gs.set("k", {"a": 2})  # upsert
    assert gs.get("k") == {"a": 2}
    gs.delete("k")
    assert gs.get("k") is None


def test_global_state_whale_list(conn):
    gs = GlobalState(conn)
    assert gs.whale_list() == []
    gs.set_whale_list(["0xaaa", "0xbbb"])
    assert gs.whale_list() == ["0xaaa", "0xbbb"]


def test_global_state_cross_venue_prices(conn):
    gs = GlobalState(conn)
    gs.set_cross_venue_price("kalshi:fed-cut", 0.32)
    gs.set_cross_venue_price("manifold:fed-cut", 0.28)
    assert gs.cross_venue_prices() == {
        "kalshi:fed-cut": 0.32,
        "manifold:fed-cut": 0.28,
    }


def test_schema_is_idempotent(conn):
    # Calling init_schema again should not fail.
    init_schema(conn)
    init_schema(conn)


def test_confluence_hit_recorded(conn, recorder):
    recorder.confluence_hit(
        market_id="m1",
        direction="YES",
        count=3,
        mean_confidence=0.75,
        fires=[{"signal": "velocity", "confidence": 0.8}],
    )
    recorder.flush()
    row = conn.execute("SELECT market_id, direction, count FROM confluence_hits").fetchone()
    assert row == ("m1", "YES", 3)


def test_order_recorded(conn, recorder):
    recorder.order(
        market_id="m1",
        side="BUY",
        price=0.50,
        size=100,
        status="PLACED",
        order_id="ord-1",
        note="triggered by confluence hit",
    )
    recorder.flush()
    row = conn.execute(
        "SELECT market_id, side, price, size, status FROM orders"
    ).fetchone()
    assert row == ("m1", "BUY", 0.50, 100, "PLACED")

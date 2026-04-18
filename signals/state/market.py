"""MarketState — read-side queries for per-market rolling windows.

Detectors (velocity, volume, disposition) call these methods to get the
time-bounded history they need to make a decision.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import duckdb


class MarketState:
    """Read interface over `market_ticks` and `trade_prints`.

    Queries are time-bounded windows. DuckDB handles the columnar lookup
    efficiently with the (market_id, ts) index.
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self.conn = conn

    def recent_ticks(
        self,
        market_id: str,
        window_sec: int,
        *,
        now: Optional[datetime] = None,
    ) -> list[tuple[datetime, Optional[float], Optional[float], Optional[float]]]:
        """Return [(ts, yes_price, best_bid, best_ask)] for the window."""
        end = now or datetime.now(timezone.utc)
        start = end - timedelta(seconds=window_sec)
        rows = self.conn.execute(
            """
            SELECT ts, yes_price, best_bid, best_ask
            FROM market_ticks
            WHERE market_id = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [market_id, start, end],
        ).fetchall()
        return rows

    def recent_prints(
        self,
        market_id: str,
        window_sec: int,
        *,
        now: Optional[datetime] = None,
    ) -> list[tuple[datetime, str, float, float]]:
        """Return [(ts, side, price, size)] for the window."""
        end = now or datetime.now(timezone.utc)
        start = end - timedelta(seconds=window_sec)
        return self.conn.execute(
            """
            SELECT ts, side, price, size
            FROM trade_prints
            WHERE market_id = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
            """,
            [market_id, start, end],
        ).fetchall()

    def volume_summary(
        self,
        market_id: str,
        window_sec: int,
        *,
        now: Optional[datetime] = None,
    ) -> dict:
        """Aggregate volume and buy/sell imbalance over the window."""
        end = now or datetime.now(timezone.utc)
        start = end - timedelta(seconds=window_sec)
        row = self.conn.execute(
            """
            SELECT
              COALESCE(SUM(size), 0)                                           AS total,
              COALESCE(SUM(CASE WHEN side = 'BUY'  THEN size ELSE 0 END), 0)   AS buy,
              COALESCE(SUM(CASE WHEN side = 'SELL' THEN size ELSE 0 END), 0)   AS sell,
              COUNT(*)                                                          AS prints
            FROM trade_prints
            WHERE market_id = ? AND ts >= ? AND ts <= ?
            """,
            [market_id, start, end],
        ).fetchone()
        total, buy, sell, prints = row or (0.0, 0.0, 0.0, 0)
        return {"total": total, "buy": buy, "sell": sell, "prints": prints}

    def price_delta(
        self,
        market_id: str,
        window_sec: int,
        *,
        now: Optional[datetime] = None,
    ) -> Optional[float]:
        """Return yes_price(end) - yes_price(start), or None if insufficient data."""
        ticks = self.recent_ticks(market_id, window_sec, now=now)
        ticks = [t for t in ticks if t[1] is not None]
        if len(ticks) < 2:
            return None
        return ticks[-1][1] - ticks[0][1]

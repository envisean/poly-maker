"""GlobalState — non-market-specific state backed by the `global_kv` table.

Holds the whale watchlist, cross-venue prices, oracle prices, sentiment
snapshots — anything that's about the world rather than a specific market.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import duckdb


class GlobalState:
    """Key/value store over `global_kv`. Values are JSON-serializable."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self.conn = conn

    def get(self, key: str) -> Optional[Any]:
        row = self.conn.execute(
            "SELECT value FROM global_kv WHERE key = ?", [key]
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, key: str, value: Any) -> None:
        now = datetime.now(timezone.utc)
        self.conn.execute(
            """
            INSERT INTO global_kv (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT (key) DO UPDATE SET
              value = excluded.value,
              updated_at = excluded.updated_at
            """,
            [key, json.dumps(value), now],
        )

    def delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM global_kv WHERE key = ?", [key])

    # ── typed accessors with sensible defaults ────────────────────────────

    def whale_list(self) -> list[str]:
        return self.get("whale_list") or []

    def set_whale_list(self, wallets: list[str]) -> None:
        self.set("whale_list", wallets)

    def cross_venue_prices(self) -> dict[str, float]:
        """Equivalent-question prices across venues keyed by '<venue>:<question>'."""
        return self.get("cross_venue_prices") or {}

    def set_cross_venue_price(self, key: str, price: float) -> None:
        prices = self.cross_venue_prices()
        prices[key] = price
        self.set("cross_venue_prices", prices)

    def news_last_seen(self) -> Optional[datetime]:
        val = self.get("news_last_seen_iso")
        if not val:
            return None
        return datetime.fromisoformat(val)

    def mark_news_seen(self, ts: Optional[datetime] = None) -> None:
        self.set("news_last_seen_iso", (ts or datetime.now(timezone.utc)).isoformat())

"""Async-friendly batch recorder — the single writer into DuckDB.

All state mutations go through this. Records are enqueued in memory and
flushed on a timer or when the queue fills. This keeps the WS hot path
unblocked while still persisting durably on-disk.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any, Optional

import duckdb


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _Write:
    table: str
    cols: tuple[str, ...]
    row: tuple


class Recorder:
    """Buffers writes and flushes to DuckDB on an interval or size threshold.

    Not thread-safe across Recorder instances — use one per DB connection.
    Safe to enqueue from any thread.
    """

    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        flush_interval_sec: float = 1.0,
        flush_batch_size: int = 500,
    ) -> None:
        self.conn = conn
        self.flush_interval_sec = flush_interval_sec
        self.flush_batch_size = flush_batch_size
        self._q: Queue[_Write] = Queue()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="recorder", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        self.flush()

    # ── producer api ───────────────────────────────────────────────────────

    def tick(
        self,
        market_id: str,
        *,
        yes_price: Optional[float] = None,
        no_price: Optional[float] = None,
        best_bid: Optional[float] = None,
        best_ask: Optional[float] = None,
        spread: Optional[float] = None,
        liquidity: Optional[float] = None,
        ts: Optional[datetime] = None,
    ) -> None:
        self._q.put(_Write(
            table="market_ticks",
            cols=("market_id", "ts", "yes_price", "no_price", "best_bid", "best_ask", "spread", "liquidity"),
            row=(market_id, ts or _utcnow(), yes_price, no_price, best_bid, best_ask, spread, liquidity),
        ))

    def trade_print(
        self,
        market_id: str,
        side: str,
        price: float,
        size: float,
        *,
        wallet: Optional[str] = None,
        ts: Optional[datetime] = None,
    ) -> None:
        self._q.put(_Write(
            table="trade_prints",
            cols=("market_id", "ts", "side", "price", "size", "wallet"),
            row=(market_id, ts or _utcnow(), side, price, size, wallet),
        ))

    def signal_fire(
        self,
        signal_name: str,
        market_id: str,
        direction: str,
        confidence: float,
        evidence: Optional[dict] = None,
        *,
        ts: Optional[datetime] = None,
    ) -> None:
        self._q.put(_Write(
            table="signal_fires",
            cols=("ts", "signal_name", "market_id", "direction", "confidence", "evidence"),
            row=(ts or _utcnow(), signal_name, market_id, direction, confidence, json.dumps(evidence or {})),
        ))

    def confluence_hit(
        self,
        market_id: str,
        direction: str,
        count: int,
        mean_confidence: float,
        fires: list[dict],
        *,
        ts: Optional[datetime] = None,
    ) -> None:
        self._q.put(_Write(
            table="confluence_hits",
            cols=("ts", "market_id", "direction", "count", "mean_confidence", "fires"),
            row=(ts or _utcnow(), market_id, direction, count, mean_confidence, json.dumps(fires)),
        ))

    def order(
        self,
        market_id: str,
        side: str,
        price: float,
        size: float,
        status: str,
        *,
        order_id: Optional[str] = None,
        confluence_hit_ts: Optional[datetime] = None,
        note: Optional[str] = None,
        ts: Optional[datetime] = None,
    ) -> None:
        self._q.put(_Write(
            table="orders",
            cols=("ts", "order_id", "market_id", "side", "price", "size", "status", "confluence_hit_ts", "note"),
            row=(ts or _utcnow(), order_id, market_id, side, price, size, status, confluence_hit_ts, note),
        ))

    def heartbeat(self, component: str, message: str = "") -> None:
        self._q.put(_Write(
            table="service_heartbeat",
            cols=("ts", "component", "message"),
            row=(_utcnow(), component, message),
        ))

    # ── flush internals ────────────────────────────────────────────────────

    def flush(self) -> int:
        """Drain the queue into DuckDB. Returns count of rows written."""
        grouped: dict[tuple[str, tuple[str, ...]], list[tuple]] = {}
        drained = 0
        while True:
            try:
                w = self._q.get_nowait()
            except Empty:
                break
            grouped.setdefault((w.table, w.cols), []).append(w.row)
            drained += 1

        if not grouped:
            return 0

        for (table, cols), rows in grouped.items():
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(cols)
            self.conn.executemany(
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
                rows,
            )
        return drained

    def _run(self) -> None:
        next_flush = time.monotonic() + self.flush_interval_sec
        while not self._stop.is_set():
            now = time.monotonic()
            if self._q.qsize() >= self.flush_batch_size or now >= next_flush:
                try:
                    self.flush()
                except Exception as exc:
                    # Never let the recorder thread die silently — log and continue.
                    print(f"[recorder] flush error: {exc}")
                next_flush = time.monotonic() + self.flush_interval_sec
            time.sleep(0.05)

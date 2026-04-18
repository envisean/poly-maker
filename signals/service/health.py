"""Tiny HTTP health endpoint — no dependency on any web framework.

GET /healthz → 200 with JSON { ok, last_heartbeat, killswitch, ticks_1m }
GET /stats   → 200 with richer counters (orders, hits, positions)
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import duckdb

from .killswitch import KillSwitch


class _Handler(BaseHTTPRequestHandler):
    conn: duckdb.DuckDBPyConnection = None   # set by server
    killswitch: KillSwitch = None            # set by server

    def log_message(self, fmt, *args):  # silence stderr access log
        return

    def do_GET(self):  # noqa: N802
        if self.path == "/healthz":
            self._write(self._healthz())
        elif self.path == "/stats":
            self._write(self._stats())
        else:
            self._write({"error": "not found"}, status=404)

    def _write(self, body: dict, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, default=str).encode())

    def _healthz(self) -> dict:
        hb = self.conn.execute(
            "SELECT MAX(ts) FROM service_heartbeat"
        ).fetchone()
        last = hb[0] if hb else None
        ticks = self.conn.execute(
            "SELECT COUNT(*) FROM market_ticks WHERE ts > ?",
            [datetime.now(timezone.utc) - timedelta(minutes=1)],
        ).fetchone()[0]
        ok = False
        if last is not None:
            # DuckDB may return tz-naive — treat as UTC.
            last_utc = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
            ok = datetime.now(timezone.utc) - last_utc < timedelta(seconds=30)
        return {
            "ok": ok,
            "last_heartbeat": last,
            "killswitch": self.killswitch.is_engaged(),
            "ticks_1m": ticks,
        }

    def _stats(self) -> dict:
        q = lambda sql, params=None: self.conn.execute(sql, params or []).fetchone()
        now = datetime.now(timezone.utc)
        one_day = now - timedelta(days=1)
        return {
            "as_of": now,
            "ticks_1h": q("SELECT COUNT(*) FROM market_ticks WHERE ts > ?", [now - timedelta(hours=1)])[0],
            "ticks_24h": q("SELECT COUNT(*) FROM market_ticks WHERE ts > ?", [one_day])[0],
            "prints_24h": q("SELECT COUNT(*) FROM trade_prints WHERE ts > ?", [one_day])[0],
            "fires_24h": q("SELECT COUNT(*) FROM signal_fires WHERE ts > ?", [one_day])[0],
            "hits_24h": q("SELECT COUNT(*) FROM confluence_hits WHERE ts > ?", [one_day])[0],
            "orders_24h": q("SELECT COUNT(*) FROM orders WHERE ts > ?", [one_day])[0],
            "positions_open": q("SELECT COUNT(*) FROM positions WHERE size <> 0")[0],
        }


class HealthServer:
    def __init__(self, conn: duckdb.DuckDBPyConnection, killswitch: KillSwitch, port: int) -> None:
        handler = type("_H", (_Handler,), {"conn": conn, "killswitch": killswitch})
        self._srv = HTTPServer(("0.0.0.0", port), handler)
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True, name="health")
        self._thread.start()

    def stop(self) -> None:
        self._srv.shutdown()
        self._srv.server_close()

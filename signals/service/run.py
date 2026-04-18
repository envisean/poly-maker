"""Service entrypoint — wires ingestion → state → confluence → order router.

Modes
-----
- Without credentials: runs in idle heartbeat mode. Records service heartbeats
  and serves /healthz. Lets us validate the service lifecycle before going live.
- With credentials (PK / BROWSER_ADDRESS / SPREADSHEET_URL set): connects to
  Polymarket websockets, streams events into the state store, evaluates the
  confluence engine every tick, routes orders via poly_data.polymarket_client.

Graceful shutdown on SIGTERM / SIGINT: recorder flushes, health server stops.
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

from signals.confluence import ConfluenceEngine
from signals.state import GlobalState, MarketState, Recorder, connect, init_schema

from .config import ServiceConfig
from .health import HealthServer
from .killswitch import KillSwitch


log = logging.getLogger("polymaker.service")


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )


def _has_credentials() -> bool:
    return bool(os.getenv("PK")) and bool(os.getenv("BROWSER_ADDRESS"))


def _build_detectors() -> list:
    """All 8 detectors — stubs today, real implementations as they land."""
    from signals.category import CategorySignal
    from signals.cross_market import CrossMarketSignal
    from signals.disposition import DispositionSignal
    from signals.news import NewsSignal
    from signals.theta import ThetaSignal
    from signals.velocity import VelocitySignal
    from signals.volume import VolumeSignal
    from signals.whale import WhaleSignal

    return [
        DispositionSignal(),
        CategorySignal(),
        VelocitySignal(),
        CrossMarketSignal(),
        NewsSignal(),
        VolumeSignal(),
        WhaleSignal(),
        ThetaSignal(),
    ]


class Service:
    def __init__(self, cfg: ServiceConfig) -> None:
        self.cfg = cfg
        self.conn = connect(cfg.db_path)
        init_schema(self.conn)
        self.recorder = Recorder(self.conn)
        self.market_state = MarketState(self.conn)
        self.global_state = GlobalState(self.conn)
        self.killswitch = KillSwitch(cfg.killswitch_path)
        self.health = HealthServer(self.conn, self.killswitch, cfg.health_port)
        self.engine = ConfluenceEngine(_build_detectors(), threshold=cfg.confluence_threshold)
        self._stop = threading.Event()

    # ── lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        log.info("starting service (db=%s, threshold=%d, dry_run=%s)",
                 self.cfg.db_path, self.cfg.confluence_threshold, self.cfg.dry_run)
        self.recorder.start()
        self.health.start()
        self._install_signals()

    def stop(self) -> None:
        log.info("stopping service")
        self._stop.set()
        self.health.stop()
        self.recorder.stop()
        self.conn.close()

    def _install_signals(self) -> None:
        # signal.signal only works in the main thread; skip quietly when running
        # inside a background thread (e.g. from tests).
        if threading.current_thread() is not threading.main_thread():
            return

        def handler(signum, frame):
            log.info("received signal %s", signum)
            self._stop.set()
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)

    # ── main loop ──────────────────────────────────────────────────────────

    def run(self) -> int:
        self.start()
        try:
            if _has_credentials():
                self._run_live()
            else:
                log.warning("no PK/BROWSER_ADDRESS set — running in idle heartbeat mode")
                self._run_idle()
        finally:
            self.stop()
        return 0

    def _run_idle(self) -> None:
        """No credentials: just heartbeat so /healthz stays green."""
        while not self._stop.is_set():
            self.recorder.heartbeat("idle", "awaiting credentials")
            time.sleep(self.cfg.tick_interval_sec)

    def _run_live(self) -> None:
        """Credentialed mode — hook into poly-maker's WS feeds and trade.

        Deliberately thin: the heavy lifting lives in poly_data.*. This method
        is the join point where WS events get mirrored into the state store
        and the confluence engine gets a chance to fire on each tick.
        """
        # TODO: import poly_data.websocket_handlers and register callbacks that
        # call self.recorder.tick() / self.recorder.trade_print() on each event.
        # TODO: per-market tick: evaluate self.engine on each market and route
        # via poly_data.polymarket_client when a hit fires and not dry_run.
        while not self._stop.is_set():
            self.recorder.heartbeat("live", "tick")
            # scaffold only — detectors are stubs; no confluence hits today.
            time.sleep(self.cfg.tick_interval_sec)


def main() -> int:
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    cfg = ServiceConfig.from_env()
    _setup_logging(cfg.log_level)
    return Service(cfg).run()


if __name__ == "__main__":
    sys.exit(main())

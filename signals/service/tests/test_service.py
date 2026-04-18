"""Smoke tests for the service lifecycle — confirms boot, heartbeat, shutdown."""
from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from signals.service.config import ServiceConfig
from signals.service.killswitch import KillSwitch
from signals.service.run import Service


def _free_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def cfg(tmp_path):
    return ServiceConfig(
        db_path=str(tmp_path / "state.duckdb"),
        tick_interval_sec=0.05,
        confluence_threshold=3,
        health_port=_free_port(),
        killswitch_path=str(tmp_path / "KILL"),
        dry_run=True,
        log_level="WARNING",
    )


def test_killswitch(tmp_path):
    ks = KillSwitch(str(tmp_path / "KILL"))
    assert ks.is_engaged() is False
    (tmp_path / "KILL").touch()
    assert ks.is_engaged() is True


def test_service_boots_and_heartbeats(cfg):
    svc = Service(cfg)
    # Shorter flush cadence so the test doesn't have to wait for the 1s default.
    svc.recorder.flush_interval_sec = 0.1
    t = threading.Thread(target=svc.run, daemon=True)
    t.start()
    time.sleep(1.0)  # tick several times, flush, serve healthz
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{cfg.health_port}/healthz", timeout=2)
        payload = json.loads(resp.read())
        assert payload["ok"] is True
        assert payload["killswitch"] is False
    finally:
        svc._stop.set()
        t.join(timeout=3)
    assert not t.is_alive()


def test_healthz_reports_killswitch(cfg, tmp_path):
    Path(cfg.killswitch_path).touch()
    svc = Service(cfg)
    svc.recorder.flush_interval_sec = 0.1
    t = threading.Thread(target=svc.run, daemon=True)
    t.start()
    time.sleep(0.5)
    try:
        resp = urllib.request.urlopen(f"http://127.0.0.1:{cfg.health_port}/healthz", timeout=2)
        assert json.loads(resp.read())["killswitch"] is True
    finally:
        svc._stop.set()
        t.join(timeout=3)

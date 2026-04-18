"""Service configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceConfig:
    db_path: str
    tick_interval_sec: float
    confluence_threshold: int
    health_port: int
    killswitch_path: str
    dry_run: bool
    log_level: str

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        return cls(
            db_path=os.getenv("POLYMAKER_DB_PATH", "data/state.duckdb"),
            tick_interval_sec=float(os.getenv("POLYMAKER_TICK_SEC", "1.0")),
            confluence_threshold=int(os.getenv("POLYMAKER_CONFLUENCE_THRESHOLD", "3")),
            health_port=int(os.getenv("POLYMAKER_HEALTH_PORT", "8787")),
            killswitch_path=os.getenv("POLYMAKER_KILLSWITCH", str(Path.home() / "KILL")),
            dry_run=os.getenv("POLYMAKER_DRY_RUN", "1") == "1",
            log_level=os.getenv("POLYMAKER_LOG_LEVEL", "INFO"),
        )

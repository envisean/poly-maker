"""File-based kill-switch. Touch the file and the service stops trading.

The service still stays alive (recording ticks, heartbeats) so we can see
what's happening — only order placement is blocked.
"""
from __future__ import annotations

from pathlib import Path


class KillSwitch:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def is_engaged(self) -> bool:
        return self.path.exists()

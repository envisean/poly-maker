# Deploy — polymaker.service

Install the systemd unit on CT 107 (pve-sea-01):

```bash
sudo bash /home/polymaker/poly-maker/deploy/install.sh
sudo systemctl start polymaker.service
```

## Operations

```bash
# status
sudo systemctl status polymaker.service

# logs (tail)
sudo journalctl -u polymaker.service -f

# health
curl http://10.1.0.107:8787/healthz
curl http://10.1.0.107:8787/stats

# kill-switch (blocks new orders, service keeps recording)
touch /home/polymaker/KILL
rm /home/polymaker/KILL

# restart after config change
sudo systemctl restart polymaker.service
```

## Modes

- **Idle** (no `PK` / `BROWSER_ADDRESS` in `.env`) — service runs, heartbeats,
  /healthz reports green. No trading.
- **Live** — once creds are set, the service will connect to Polymarket WS,
  record ticks, and route orders on confluence hits (unless `POLYMAKER_DRY_RUN=1`).

## Environment

All service knobs (see `signals/service/config.py`):

| Var | Default | Meaning |
|-----|---------|---------|
| `POLYMAKER_DB_PATH` | `data/state.duckdb` | DuckDB file |
| `POLYMAKER_TICK_SEC` | `1.0` | Main loop cadence |
| `POLYMAKER_CONFLUENCE_THRESHOLD` | `3` | Detectors-to-fire threshold |
| `POLYMAKER_HEALTH_PORT` | `8787` | /healthz, /stats port |
| `POLYMAKER_KILLSWITCH` | `~/KILL` | Kill-switch file path |
| `POLYMAKER_DRY_RUN` | `1` | Don't actually place orders (safe default) |
| `POLYMAKER_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

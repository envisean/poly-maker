#!/usr/bin/env bash
# Install/refresh the polymaker.service systemd unit.
# Run as root on the target host (CT 107).
set -euo pipefail

REPO_DIR="/home/polymaker/poly-maker"
UNIT_SRC="${REPO_DIR}/deploy/polymaker.service"
UNIT_DST="/etc/systemd/system/polymaker.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root" >&2; exit 1
fi

install -m 0644 "${UNIT_SRC}" "${UNIT_DST}"
install -d -o polymaker -g polymaker "${REPO_DIR}/data"

systemctl daemon-reload
systemctl enable polymaker.service
echo "Installed. Start with: systemctl start polymaker.service"
echo "Logs: journalctl -u polymaker.service -f"
echo "Health: curl http://10.1.0.107:8787/healthz"

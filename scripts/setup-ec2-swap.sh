#!/bin/bash
# Run once on a fresh t2.micro (1GB RAM) before `docker compose -f docker-compose.prod.yml build`.
# The frontend build step (npm run build) and Postgres+Redis+backend+celery
# running together can exceed 1GB; a swap file prevents OOM kills.
set -euo pipefail

SWAP_FILE=/swapfile
SWAP_SIZE_GB=2

if swapon --show | grep -q "$SWAP_FILE"; then
  echo "Swap already active at $SWAP_FILE"
  exit 0
fi

sudo fallocate -l ${SWAP_SIZE_GB}G "$SWAP_FILE"
sudo chmod 600 "$SWAP_FILE"
sudo mkswap "$SWAP_FILE"
sudo swapon "$SWAP_FILE"

if ! grep -q "$SWAP_FILE" /etc/fstab; then
  echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab
fi

sudo sysctl vm.swappiness=10
echo "vm.swappiness=10" | sudo tee /etc/sysctl.d/60-swappiness.conf

swapon --show
free -h

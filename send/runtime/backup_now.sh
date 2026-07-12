#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/binarybot"
BKP_DIR="/opt/binarybot_backups"
TS="$(date -u +%Y%m%d_%H%M%S)"
OUT="${BKP_DIR}/binarybot_${TS}.tar.gz"

mkdir -p "$BKP_DIR"

tar -czf "$OUT" \
  --exclude="${ROOT}/Legacy" \
  --exclude="${ROOT}/legacy" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  -C /opt binarybot

ln -sf "$(basename "$OUT")" "${BKP_DIR}/LATEST.tar.gz"

echo "OK: backup created -> $OUT"
ls -lah "$OUT"
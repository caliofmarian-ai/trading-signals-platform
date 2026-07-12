#!/usr/bin/env bash
set -euo pipefail

# BinaryBot — Rollback utility
# Usage:
#   /opt/binarybot/runtime/rollback.sh                # uses LATEST.tar.gz
#   /opt/binarybot/runtime/rollback.sh LATEST.tar.gz  # explicit
#   /opt/binarybot/runtime/rollback.sh binarybot_YYYYMMDD_HHMMSS.tar.gz

BACKUP_DIR="/opt/binarybot_backups"
TARGET_DIR="/opt/binarybot"

ARG="${1:-LATEST.tar.gz}"
BACKUP_PATH="${BACKUP_DIR}/${ARG}"

if [[ ! -e "${BACKUP_PATH}" ]]; then
  echo "ERROR: backup not found: ${BACKUP_PATH}"
  echo "Available backups:"
  ls -1 "${BACKUP_DIR}" | sed 's/^/  - /'
  exit 1
fi

# Resolve symlink (LATEST.tar.gz -> real tar.gz)
if [[ -L "${BACKUP_PATH}" ]]; then
  REAL="$(readlink -f "${BACKUP_PATH}")"
else
  REAL="${BACKUP_PATH}"
fi

if [[ ! -f "${REAL}" ]]; then
  echo "ERROR: resolved backup is not a file: ${REAL}"
  exit 1
fi

echo "Rollback source: ${REAL}"
echo "Target dir:      ${TARGET_DIR}"
echo

# Safety: require explicit confirmation
read -r -p "Type RESTORE to continue: " CONFIRM
if [[ "${CONFIRM}" != "RESTORE" ]]; then
  echo "Aborted."
  exit 0
fi

# Make a safety backup of current /opt/binarybot (excluding Legacy)
STAMP="$(date -u +%Y%m%d_%H%M%S)"
SAFETY="${BACKUP_DIR}/pre_rollback_${STAMP}.tar.gz"

echo "Creating safety backup -> ${SAFETY}"
tar \
  --exclude='./Legacy' \
  --exclude='./legacy' \
  -C /opt \
  -czf "${SAFETY}" \
  binarybot

# Restore: wipe target except Legacy (Legacy remains untouched)
echo "Restoring..."
if [[ -d "${TARGET_DIR}" ]]; then
  find "${TARGET_DIR}" -mindepth 1 \
    \( -name 'Legacy' -o -name 'legacy' \) -prune -o \
    -exec rm -rf {} +
fi

# Extract tar to /opt (tar contains binarybot/...)
tar -C /opt -xzf "${REAL}"

# Fix CRLF issues in runtime scripts (common QuickEdit problem)
if command -v sed >/dev/null 2>&1; then
  sed -i 's/\r$//' /opt/binarybot/runtime/*.sh 2>/dev/null || true
fi

echo "OK: rollback completed."
echo "Safety backup saved: ${SAFETY}"
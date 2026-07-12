#!/usr/bin/env bash
set -euo pipefail

set -a
. /opt/binarybot/.env
set +a

MSG="${1:-}"

if [[ -z "${MSG}" ]]; then
  echo "Usage: $0 <signal_text>"
  exit 1
fi

if [[ -z "${TOPIC_SIGNALS_LIVE:-}" ]]; then
  echo "ERROR: TOPIC_SIGNALS_LIVE is missing in .env"
  exit 2
fi

TS="$(date -u '+%Y-%m-%d %H:%M:%SZ')"
TEXT="🚀 SIGNAL [${TS}]\n${MSG}"

exec /opt/binarybot/tg_send.sh "${TOPIC_SIGNALS_LIVE}" "${TEXT}"
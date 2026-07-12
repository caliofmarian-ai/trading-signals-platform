#!/usr/bin/env bash
set -euo pipefail

# Load .env so we have TELEGRAM_* + TOPIC_*
set -a
. /opt/binarybot/.env
set +a

MSG="${1:-}"

if [[ -z "$MSG" ]]; then
  echo "Usage: $0 \"Daily stats W:3 L:1 WR:75%\""
  exit 1
fi

THREAD="${TOPIC_PERFORMANCE_STATS:-}"
if [[ -z "$THREAD" ]]; then
  echo "ERROR: TOPIC_PERFORMANCE_STATS is not set in .env"
  exit 2
fi

/opt/binarybot/tg_send.sh "$THREAD" "📊 ${MSG}"

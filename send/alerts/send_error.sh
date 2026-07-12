#!/usr/bin/env bash
set -euo pipefail

set -a
. /opt/binarybot/.env
set +a

WHERE="${1:-UNKNOWN}"
ERR="${2:-}"

if [[ -z "${ERR}" ]]; then
  echo "Usage: $0 <where> <error_text>"
  exit 1
fi

if [[ -z "${TOPIC_DEBUG_ERRORS:-}" ]]; then
  echo "ERROR: TOPIC_DEBUG_ERRORS is missing in .env"
  exit 2
fi

TS="$(date -u '+%Y-%m-%d %H:%M:%SZ')"
TEXT="🩺 DEBUG ERROR [${TS}]\nWHERE: ${WHERE}\n\n${ERR}"

exec /opt/binarybot/tg_send.sh "${TOPIC_DEBUG_ERRORS}" "${TEXT}"
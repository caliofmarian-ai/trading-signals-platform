#!/usr/bin/env bash
set -euo pipefail

set -a
. /opt/binarybot/.env
set +a

LEVEL="${1:-INFO}"   # INFO / WARN / CRIT
MSG="${2:-}"

if [[ -z "${MSG}" ]]; then
  echo "Usage: $0 <INFO|WARN|CRIT> <message>"
  exit 1
fi

if [[ -z "${TOPIC_SYSTEM_ALERTS:-}" ]]; then
  echo "ERROR: TOPIC_SYSTEM_ALERTS is missing in .env"
  exit 2
fi

TS="$(date -u '+%Y-%m-%d %H:%M:%SZ')"

case "${LEVEL^^}" in
  INFO) ICON="🟢" ;;
  WARN) ICON="🟠" ;;
  CRIT|CRITICAL) ICON="🔴" ;;
  *) ICON="⚪" ;;
esac

TEXT="${ICON} SYSTEM ${LEVEL^^} [${TS}]\n${MSG}"

exec /opt/binarybot/tg_send.sh "${TOPIC_SYSTEM_ALERTS}" "${TEXT}"
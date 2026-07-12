#!/usr/bin/env bash
set -euo pipefail

set -a
. /opt/binarybot/.env
set +a

EVENT="${1:-}"
DETAILS="${2:-}"

if [[ -z "${EVENT}" ]]; then
  echo "Usage: $0 <event> [details]"
  exit 1
fi

if [[ -z "${TOPIC_BILLING_EVENTS:-}" ]]; then
  echo "ERROR: TOPIC_BILLING_EVENTS is missing in .env"
  exit 2
fi

TS="$(date -u '+%Y-%m-%d %H:%M:%SZ')"

if [[ -n "${DETAILS}" ]]; then
  TEXT="💳 BILLING [${TS}]\nEVENT: ${EVENT}\n${DETAILS}"
else
  TEXT="💳 BILLING [${TS}]\nEVENT: ${EVENT}"
fi

exec /opt/binarybot/tg_send.sh "${TOPIC_BILLING_EVENTS}" "${TEXT}"
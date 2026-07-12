#!/usr/bin/env bash
set -euo pipefail

set -a
. /opt/binarybot/.env
set +a

RESULT="${1:-}"     # WIN / LOSS / BREAKEVEN / RESULT
DETAILS="${2:-}"    # optional extra text

if [[ -z "${RESULT}" ]]; then
  echo "Usage: $0 <WIN|LOSS|BREAKEVEN|RESULT> [details]"
  exit 1
fi

if [[ -z "${TOPIC_TRADE_RESULTS:-}" ]]; then
  echo "ERROR: TOPIC_TRADE_RESULTS is missing in .env"
  exit 2
fi

TS="$(date -u '+%Y-%m-%d %H:%M:%SZ')"

case "${RESULT^^}" in
  WIN)      PREFIX="✅ WIN" ;;
  LOSS)     PREFIX="❌ LOSS" ;;
  BREAKEVEN|BE) PREFIX="➖ BREAKEVEN" ;;
  RESULT)   PREFIX="📌 RESULT" ;;
  *)        PREFIX="📌 ${RESULT}" ;;
esac

if [[ -n "${DETAILS}" ]]; then
  TEXT="${PREFIX} [${TS}]\n${DETAILS}"
else
  TEXT="${PREFIX} [${TS}]"
fi

exec /opt/binarybot/tg_send.sh "${TOPIC_TRADE_RESULTS}" "${TEXT}"
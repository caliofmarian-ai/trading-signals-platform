#!/usr/bin/env bash

set -a
. /opt/binarybot/.env
set +a

THREAD="$1"
TEXT="$2"

curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
-H "Content-Type: application/json" \
-d "{
\"chat_id\": \"$TELEGRAM_ADMIN_CHAT_ID\",
\"message_thread_id\": $THREAD,
\"text\": \"$TEXT\"
}"

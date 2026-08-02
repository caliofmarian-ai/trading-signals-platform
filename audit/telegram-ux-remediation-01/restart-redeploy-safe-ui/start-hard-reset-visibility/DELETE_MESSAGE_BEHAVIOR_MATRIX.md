# DELETE_MESSAGE_BEHAVIOR_MATRIX.md

## deleteMessage Outcome Classification

### Canonical `delete_message()` Function

Located in `send/core/telegram_publisher.py`.

**Signature:**
```python
def delete_message(chat_id: int, message_id: int) -> Dict[str, Any]
```

**Guarantee:** Never raises. Always returns a structured result dict.

**Result fields:**
- `outcome`: one of the DELETE_OUTCOME_* constants
- `chat_id`: echo of input
- `message_id`: echo of input
- `error_code`: Telegram error_code (int or None)
- `description`: sanitized description (str or None); never contains bot token

### Outcome Constants

| Constant | Value | Meaning |
|---|---|---|
| `DELETE_OUTCOME_DELETED` | `"deleted"` | Message deleted successfully |
| `DELETE_OUTCOME_ABSENT` | `"message_absent"` | Message already gone (not found) |
| `DELETE_OUTCOME_FORBIDDEN` | `"forbidden"` | Deletion forbidden or message too old |
| `DELETE_OUTCOME_TRANSPORT` | `"transport_failure"` | Network/connectivity failure |
| `DELETE_OUTCOME_UNEXPECTED` | `"unexpected"` | Unexpected API response |

### Behavior Matrix

| Scenario | Telegram response | Outcome | /start continues? |
|---|---|---|---|
| Normal deletion | `{"ok": true}` | `deleted` | ✅ Yes |
| Message not found | 400 `message to delete not found` | `message_absent` | ✅ Yes |
| Message ID invalid | 400 `message_id_invalid` | `message_absent` | ✅ Yes |
| Chat not found | 400 `chat not found` | `message_absent` | ✅ Yes |
| Bot blocked | 403 `bot was blocked by the user` | `forbidden` | ✅ Yes |
| Not enough rights | 400/403 `not enough rights` | `forbidden` | ✅ Yes |
| Message too old | 400 `can't be deleted for everyone` | `forbidden` | ✅ Yes |
| Network timeout | `requests.exceptions.Timeout` | `transport_failure` | ✅ Yes |
| Connection error | `requests.exceptions.ConnectionError` | `transport_failure` | ✅ Yes |
| Unexpected exception | Any other exception | `unexpected` | ✅ Yes |

### Transport Failure and /start

A `transport_failure` outcome means the delete call itself could not reach
Telegram. The `/start` sequence still proceeds to `sendMessage`. Even in a
transport failure scenario, the replacement send is attempted. If the Telegram
transport itself is completely unavailable (i.e., `sendMessage` also fails),
that failure is handled separately by the send-failure path.

### Token Safety

All descriptions are passed through `_sanitize()` before being stored in the
result dict. The bot token is never included in logged diagnostic output.

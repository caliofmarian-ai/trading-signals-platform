# /opt/binarybot/core/telegram_publisher.py
# BinaryBot — Telegram API Abstraction Layer

from __future__ import annotations
import os
import re
import requests
from typing import Dict, Any, Optional


def _get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    return token


def _base_url() -> str:
    return f"https://api.telegram.org/bot{_get_bot_token()}"


# Regex that matches the bot-token segment inside a Telegram API URL so it can
# be redacted from any string before it reaches a log sink or exception message.
_TOKEN_PATTERN = re.compile(r"(?<=/bot)\d+:[A-Za-z0-9_-]+")


def _sanitize(s: str) -> str:
    """Replace any bot-token substring in *s* with a safe placeholder."""
    return _TOKEN_PATTERN.sub("[REDACTED]", s)


# ---------------------------------------------------------------------------
# Structured Telegram API exception
# ---------------------------------------------------------------------------

class TelegramAPIError(RuntimeError):
    """Structured exception for Telegram API failures.

    Attributes:
        operation:    Name of the API operation that failed (e.g. "editMessageText").
        http_status:  HTTP response status code.
        error_code:   Telegram API ``error_code`` field (int) or None.
        description:  Sanitized Telegram API ``description`` field.
        retry_after:  Seconds to wait before retrying (flood-control), or None.
    """

    def __init__(
        self,
        operation: str,
        http_status: int,
        error_code: Optional[int],
        description: str,
        retry_after: Optional[int] = None,
    ) -> None:
        self.operation = operation
        self.http_status = http_status
        self.error_code = error_code
        self.description = _sanitize(description)
        self.retry_after = retry_after
        super().__init__(
            f"Telegram {operation} failed: "
            f"http={http_status} code={error_code} description={self.description!r}"
        )

    @classmethod
    def from_response(cls, operation: str, http_status: int, data: Dict[str, Any]) -> "TelegramAPIError":
        """Construct from a parsed Telegram API response dict."""
        error_code_raw = data.get("error_code")
        error_code: Optional[int] = None
        try:
            error_code = int(error_code_raw) if error_code_raw is not None else None
        except (TypeError, ValueError):
            pass
        description = str(data.get("description") or "no description")
        retry_after: Optional[int] = None
        params = data.get("parameters")
        if isinstance(params, dict):
            ra = params.get("retry_after")
            try:
                retry_after = int(ra) if ra is not None else None
            except (TypeError, ValueError):
                pass
        return cls(
            operation=operation,
            http_status=http_status,
            error_code=error_code,
            description=description,
            retry_after=retry_after,
        )

    # Normalized description for classification (lowercase, stripped).
    @property
    def normalized_description(self) -> str:
        return self.description.lower().strip()

    def is_stale_message(self) -> bool:
        """Return True when the error unambiguously indicates a deleted/inaccessible message.

        Classification uses structured fields (error_code, http_status) first,
        then falls back to normalized description matching for known patterns.
        Telegram HTTP 400 + error_code 400 with a stale-message description is
        the canonical form.
        """
        # Structural: HTTP 400 with known stale codes/descriptions.
        if self.http_status == 400:
            stale_descriptions = (
                "message to edit not found",
                "message can't be edited",
                "message can not be edited",
                "message to be replied not found",
            )
            nd = self.normalized_description
            if any(marker in nd for marker in stale_descriptions):
                return True
        # Structural: HTTP 403 indicates the bot lost access (blocked/kicked).
        if self.http_status == 403:
            nd = self.normalized_description
            if "bot was blocked by the user" in nd or "user is deactivated" in nd:
                return True
        return False

    def is_not_modified(self) -> bool:
        """Return True when the message content was identical (no-op edit)."""
        return "message is not modified" in self.normalized_description

    def is_chat_not_found(self) -> bool:
        nd = self.normalized_description
        return "chat not found" in nd or "peer_id_invalid" in nd


def _raise_from_response(operation: str, resp: requests.Response, data: Dict[str, Any]) -> None:
    """Raise TelegramAPIError built from the HTTP response and parsed data."""
    raise TelegramAPIError.from_response(operation, resp.status_code, data)


def _safe_api_error(data: Dict[str, Any]) -> str:
    """Return a log-safe summary of a Telegram API error response (legacy helper)."""
    error_code = data.get("error_code", "?")
    description = _sanitize(str(data.get("description", "no description")))
    return f"code={error_code} description={description!r}"


def send_message(
    chat_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:

    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    if thread_id:
        payload["message_thread_id"] = thread_id

    r = requests.post(f"{_base_url()}/sendMessage", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        _raise_from_response("sendMessage", r, data)

    return data


def edit_message(
    chat_id: int,
    message_id: int,
    text: Optional[str] = None,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Edit an existing Telegram message.

    parse_mode is intentionally omitted so that both edit_message and
    send_message use the same rendering mode (plain text).  Setting HTML mode
    here while send_message uses no mode caused Telegram to reject edits
    whenever the text contained HTML-special characters such as the ``<value>``
    and ``<dir>`` placeholders present in admin command-help strings, producing
    a 400 parse-entities error that was mis-classified as an unexpected failure
    and silently fell through to send_message, violating the single-message
    contract.

    Raises ``TelegramAPIError`` (a subclass of ``RuntimeError``) on failure so
    that callers can distinguish stale-message errors from network errors using
    structured fields rather than brittle string matching.
    """
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
    }

    if text:
        payload["text"] = text

    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(f"{_base_url()}/editMessageText", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        _raise_from_response("editMessageText", r, data)

    return data


def answer_callback_query(
    callback_query_id: str,
    text: str = "",
    show_alert: bool = False,
) -> Dict[str, Any]:
    """Acknowledge a Telegram callback query to dismiss the loading spinner."""
    payload: Dict[str, Any] = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert,
    }
    if text:
        payload["text"] = text

    r = requests.post(f"{_base_url()}/answerCallbackQuery", json=payload, timeout=10)
    data = r.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram answer_callback_query failed: {_safe_api_error(data)}")

    return data


# ---------------------------------------------------------------------------
# Deletion outcomes (structured classification for delete_message callers)
# ---------------------------------------------------------------------------

DELETE_OUTCOME_DELETED = "deleted"          # successful deletion
DELETE_OUTCOME_ABSENT = "message_absent"    # message not found (already gone)
DELETE_OUTCOME_FORBIDDEN = "forbidden"      # deletion forbidden / message too old
DELETE_OUTCOME_TRANSPORT = "transport_failure"  # network/connectivity problem
DELETE_OUTCOME_UNEXPECTED = "unexpected"    # any other API failure


def delete_message(chat_id: int, message_id: int) -> Dict[str, Any]:
    """Best-effort delete a Telegram message.

    Returns a structured result dict with:
        outcome:     one of the DELETE_OUTCOME_* constants
        chat_id:     echo of the input chat_id
        message_id:  echo of the input message_id
        error_code:  Telegram error_code if available, else None
        description: sanitized error description if available, else None

    Never raises; all outcomes are returned as structured data so that callers
    (especially the /start hard-reset path) can classify results without
    try/except and without ever being blocked by a failed deletion.
    """
    result: Dict[str, Any] = {
        "outcome": DELETE_OUTCOME_UNEXPECTED,
        "chat_id": chat_id,
        "message_id": message_id,
        "error_code": None,
        "description": None,
    }
    try:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "message_id": message_id,
        }
        r = requests.post(f"{_base_url()}/deleteMessage", json=payload, timeout=10)
        data = r.json()

        if data.get("ok"):
            result["outcome"] = DELETE_OUTCOME_DELETED
            return result

        error_code_raw = data.get("error_code")
        error_code: Optional[int] = None
        try:
            error_code = int(error_code_raw) if error_code_raw is not None else None
        except (TypeError, ValueError):
            pass
        description = _sanitize(str(data.get("description") or "no description"))
        result["error_code"] = error_code
        result["description"] = description
        nd = description.lower().strip()

        # Message already gone: absent outcome.
        if r.status_code == 400 and any(
            m in nd for m in (
                "message to delete not found",
                "message_id_invalid",
                "message can't be deleted",
                "chat not found",
                "peer_id_invalid",
            )
        ):
            result["outcome"] = DELETE_OUTCOME_ABSENT
            return result

        # Bot no longer has access to this chat.
        if r.status_code == 400 and "bad request" in nd and "message_id_invalid" in nd:
            result["outcome"] = DELETE_OUTCOME_ABSENT
            return result

        # Deletion forbidden / message too old.
        if r.status_code in (400, 403) and any(
            m in nd for m in (
                "message can't be deleted for everyone",
                "not enough rights",
                "bot was kicked",
                "bot was blocked",
                "user is deactivated",
                "forbidden",
            )
        ):
            result["outcome"] = DELETE_OUTCOME_FORBIDDEN
            return result

        result["outcome"] = DELETE_OUTCOME_UNEXPECTED
        return result

    except requests.exceptions.RequestException as transport_exc:
        result["outcome"] = DELETE_OUTCOME_TRANSPORT
        result["description"] = _sanitize(str(transport_exc))
        return result
    except Exception as unexpected_exc:
        result["outcome"] = DELETE_OUTCOME_UNEXPECTED
        result["description"] = _sanitize(str(unexpected_exc))
        return result


def send_document(
    chat_id: int,
    file_path: str,
    caption: Optional[str] = None,
    thread_id: Optional[int] = None,
) -> Dict[str, Any]:

    with open(file_path, "rb") as f:

        files = {
            "document": f,
        }

        data: Dict[str, Any] = {
            "chat_id": chat_id,
        }

        if caption:
            data["caption"] = caption

        if thread_id:
            data["message_thread_id"] = thread_id

        r = requests.post(
            f"{_base_url()}/sendDocument",
            data=data,
            files=files,
            timeout=20,
        )

    result = r.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram send_document failed: {_safe_api_error(result)}")

    return result
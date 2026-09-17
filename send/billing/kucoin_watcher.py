from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional
from urllib.parse import quote, urlencode

import requests

from billing import payment_ledger
from core import storage

PROVIDER = "KUCOIN"
SITE_BASE_URLS = {
    "global": "https://api.kucoin.com",
    "eu": "https://api.kucoin.eu",
}
ACCOUNT_MODE_CLASSIC = "classic"
PRIVATE_TOKEN_PATH = "/api/v1/bullet-private"
DEPOSIT_HISTORY_PATH = "/api/v1/deposits"
BALANCE_TOPIC = "/account/balance"
DEPOSIT_RELATION_EVENT = "main.deposit"
MAX_RETRIES = 3
MAX_HISTORY_PAGES = 10

EVENT_WS_TRIGGER = "KUCOIN_WS_DEPOSIT_TRIGGER"
EVENT_DEPOSIT_RECONCILED = "KUCOIN_DEPOSIT_RECONCILED"
EVENT_MANUAL_REVIEW = "KUCOIN_MANUAL_REVIEW_REQUIRED"
EVENT_PROVIDER_UNAVAILABLE = "KUCOIN_PROVIDER_UNAVAILABLE"
EVENT_WATCHER_RECONNECT = "KUCOIN_WATCHER_RECONNECT"

_LOCK_NAME = "billing_kucoin_watcher"
_EVENTS_RELATIVE = ("billing", "kucoin_watcher_events.jsonl")

_STATUS_TO_LEDGER = {
    "SUCCESS": "SETTLED",
    "PROCESSING": "PENDING",
    "PENDING": "PENDING",
    "WAITING": "PENDING",
    "FAILED": "FAILED",
    "FAILURE": "FAILED",
}


class KuCoinError(RuntimeError):
    """Raised when KuCoin evidence or configuration is invalid."""


class KuCoinProviderUnavailable(KuCoinError):
    """Raised for retryable transport/provider availability failures."""


def events_path() -> str:
    return storage.root_path(*_EVENTS_RELATIVE)


def _nonempty(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KuCoinError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _opaque_id() -> str:
    return str(uuid.uuid4())


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hmac_b64(secret: str, message: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _redact(value: Any, *secrets: str) -> str:
    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


def _read_events_unlocked(path: str) -> list[Dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise KuCoinError(f"Unable to read KuCoin adapter log: {target}") from exc

    records: list[Dict[str, Any]] = []
    event_ids: set[str] = set()
    sequences: set[int] = set()
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KuCoinError(
                f"KuCoin adapter JSON corruption at line {line_number}"
            ) from exc
        if not isinstance(row, dict):
            raise KuCoinError(
                f"KuCoin adapter record at line {line_number} is not an object"
            )
        event_id = _nonempty(row.get("kucoin_event_id"), label="kucoin_event_id")
        if event_id in event_ids:
            raise KuCoinError(f"Duplicate kucoin_event_id: {event_id}")
        event_ids.add(event_id)
        seq = row.get("kucoin_seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq <= 0:
            raise KuCoinError(f"Invalid kucoin_seq at line {line_number}")
        if seq in sequences:
            raise KuCoinError(f"Duplicate kucoin_seq: {seq}")
        sequences.add(seq)
        records.append(row)

    if records:
        expected = list(range(1, len(records) + 1))
        actual = [int(row["kucoin_seq"]) for row in records]
        if actual != expected:
            raise KuCoinError(
                f"KuCoin adapter sequence is non-contiguous: expected={expected} actual={actual}"
            )
    return records


def load_events(path: str | None = None) -> list[Dict[str, Any]]:
    return _read_events_unlocked(path or events_path())


def _append_event(
    *,
    path: str,
    payload: Mapping[str, Any],
    idempotency_key: str | None = None,
) -> tuple[Dict[str, Any], bool]:
    with storage.with_lock(_LOCK_NAME):
        records = _read_events_unlocked(path)
        if idempotency_key:
            for row in records:
                if row.get("idempotency_key") == idempotency_key:
                    return dict(row), False
        record = dict(payload)
        record["kucoin_event_id"] = _opaque_id()
        record["kucoin_seq"] = len(records) + 1
        if idempotency_key:
            record["idempotency_key"] = idempotency_key
        storage.append_jsonl(path, record)
        return record, True


def _raw_query(params: Iterable[tuple[str, Any]]) -> str:
    return "&".join(f"{key}={value}" for key, value in params if value is not None)


def _encoded_query(params: Iterable[tuple[str, Any]]) -> str:
    return urlencode([(key, value) for key, value in params if value is not None])


class KuCoinClient:
    """Read-only KuCoin Classic Account client for billing deposit observation."""

    def __init__(
        self,
        *,
        api_key: str,
        api_secret: str,
        api_passphrase: str,
        api_key_version: str,
        site: str = "global",
        account_mode: str = ACCOUNT_MODE_CLASSIC,
        request_fn: Callable[..., Any] = requests.request,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock_ms_fn: Callable[[], int] | None = None,
        max_retries: int = 2,
        allow_live_reads: bool = False,
    ) -> None:
        self._api_key = _nonempty(api_key, label="KuCoin API key")
        self._api_secret = _nonempty(api_secret, label="KuCoin API secret")
        self._api_passphrase = _nonempty(api_passphrase, label="KuCoin API passphrase")
        self.api_key_version = _nonempty(api_key_version, label="KuCoin API key version")
        self.site = _nonempty(site, label="KuCoin site").lower()
        if self.site not in SITE_BASE_URLS:
            raise KuCoinError("KuCoin site must be global or eu")
        self.base_url = SITE_BASE_URLS[self.site]
        self.account_mode = _nonempty(account_mode, label="KuCoin account mode").lower()
        if self.account_mode != ACCOUNT_MODE_CLASSIC:
            raise KuCoinError(
                "Only KuCoin Classic Account billing observation is implemented; "
                "UTA must remain fail-closed until separately governed"
            )
        if isinstance(max_retries, bool) or not isinstance(max_retries, int):
            raise KuCoinError("max_retries must be an integer")
        self.max_retries = max(0, min(max_retries, MAX_RETRIES))
        self.allow_live_reads = bool(allow_live_reads)
        self._request_fn = request_fn
        self._sleep_fn = sleep_fn
        self._clock_ms_fn = clock_ms_fn or (lambda: int(time.time() * 1000))

    @classmethod
    def from_env(
        cls,
        *,
        request_fn: Callable[..., Any] = requests.request,
        sleep_fn: Callable[[float], None] = time.sleep,
        clock_ms_fn: Callable[[], int] | None = None,
    ) -> "KuCoinClient":
        retries_raw = os.getenv("KUCOIN_MAX_RETRIES", "2").strip()
        try:
            retries = int(retries_raw)
        except ValueError as exc:
            raise KuCoinError("KUCOIN_MAX_RETRIES must be an integer") from exc
        return cls(
            api_key=os.getenv("KUCOIN_API_KEY", ""),
            api_secret=os.getenv("KUCOIN_API_SECRET", ""),
            api_passphrase=os.getenv("KUCOIN_API_PASSPHRASE", ""),
            api_key_version=os.getenv("KUCOIN_API_KEY_VERSION", ""),
            site=os.getenv("KUCOIN_SITE", "global"),
            account_mode=os.getenv("KUCOIN_ACCOUNT_MODE", ACCOUNT_MODE_CLASSIC),
            request_fn=request_fn,
            sleep_fn=sleep_fn,
            clock_ms_fn=clock_ms_fn,
            max_retries=retries,
            allow_live_reads=_env_flag("KUCOIN_ALLOW_LIVE_READS", default=False),
        )

    def safe_config(self) -> Dict[str, Any]:
        return {
            "provider": PROVIDER,
            "base_url": self.base_url,
            "site": self.site,
            "account_mode": self.account_mode,
            "api_key_version": self.api_key_version,
            "max_retries": self.max_retries,
            "allow_live_reads": self.allow_live_reads,
            "credentials_configured": True,
        }

    def _headers(
        self,
        *,
        method: str,
        endpoint_for_signature: str,
        body_text: str,
    ) -> Dict[str, str]:
        timestamp = str(int(self._clock_ms_fn()))
        prehash = f"{timestamp}{method.upper()}{endpoint_for_signature}{body_text}"
        return {
            "KC-API-KEY": self._api_key,
            "KC-API-SIGN": _hmac_b64(self._api_secret, prehash),
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-PASSPHRASE": _hmac_b64(self._api_secret, self._api_passphrase),
            "KC-API-KEY-VERSION": self.api_key_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Iterable[tuple[str, Any]] = (),
        json_body: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self.allow_live_reads:
            raise KuCoinError(
                "KuCoin live reads require explicit KUCOIN_ALLOW_LIVE_READS=true "
                "or allow_live_reads=True"
            )
        method_upper = _nonempty(method, label="HTTP method").upper()
        path_text = _nonempty(path, label="KuCoin API path")
        param_list = list(params)
        raw_query = _raw_query(param_list)
        encoded_query = _encoded_query(param_list)
        endpoint_for_signature = path_text + (f"?{raw_query}" if raw_query else "")
        url = self.base_url + path_text + (f"?{encoded_query}" if encoded_query else "")
        body_text = (
            json.dumps(dict(json_body), separators=(",", ":"), ensure_ascii=False)
            if json_body is not None
            else ""
        )

        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            # Each retry is a new authenticated request. Re-sign with a fresh
            # timestamp so backoff cannot replay an expired signature.
            headers = self._headers(
                method=method_upper,
                endpoint_for_signature=endpoint_for_signature,
                body_text=body_text,
            )
            try:
                response = self._request_fn(
                    method_upper,
                    url,
                    headers=headers,
                    data=body_text if body_text else None,
                    timeout=15,
                )
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    self._sleep_fn(min(0.25 * (2**attempt), 1.0))
                    continue
                raise KuCoinProviderUnavailable(
                    "KuCoin transport unavailable: "
                    + _redact(exc, self._api_key, self._api_secret, self._api_passphrase)
                ) from exc

            status = int(getattr(response, "status_code", 0) or 0)
            try:
                payload = response.json()
            except Exception:
                payload = None

            if status == 429 or status >= 500 or status == 0:
                last_error = KuCoinProviderUnavailable(
                    f"KuCoin provider unavailable: http={status}"
                )
                if attempt < self.max_retries:
                    self._sleep_fn(min(0.25 * (2**attempt), 1.0))
                    continue
                raise last_error
            if status < 200 or status >= 300:
                detail = ""
                if isinstance(payload, dict):
                    detail = str(
                        payload.get("msg")
                        or payload.get("message")
                        or payload.get("code")
                        or ""
                    )
                raise KuCoinError(
                    f"KuCoin API rejected request: http={status} "
                    f"detail={_redact(detail, self._api_key, self._api_secret, self._api_passphrase)[:300]}"
                )
            if not isinstance(payload, dict):
                raise KuCoinError("KuCoin API returned a non-object JSON response")
            if str(payload.get("code") or "") != "200000":
                detail = _redact(
                    payload.get("msg") or payload.get("message") or payload.get("code"),
                    self._api_key,
                    self._api_secret,
                    self._api_passphrase,
                )
                raise KuCoinError(f"KuCoin API returned non-success code: {detail[:300]}")
            return dict(payload)

        raise KuCoinProviderUnavailable(
            "KuCoin provider unavailable: "
            + _redact(last_error, self._api_key, self._api_secret, self._api_passphrase)
        )

    def get_private_ws_token(self) -> Dict[str, Any]:
        payload = self._request("POST", PRIVATE_TOKEN_PATH)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise KuCoinError("KuCoin private token response is missing data")
        token = _nonempty(data.get("token"), label="KuCoin websocket token")
        servers = data.get("instanceServers")
        if not isinstance(servers, list) or not servers:
            raise KuCoinError("KuCoin private token response is missing instanceServers")
        server = next((row for row in servers if isinstance(row, dict)), None)
        if server is None:
            raise KuCoinError("KuCoin private token response has no valid server")
        endpoint = _nonempty(server.get("endpoint"), label="KuCoin websocket endpoint")
        if not endpoint.startswith("wss://"):
            raise KuCoinError("KuCoin websocket endpoint must use wss://")
        ping_interval = int(server.get("pingInterval") or 0)
        ping_timeout = int(server.get("pingTimeout") or 0)
        if ping_interval <= 0 or ping_timeout <= 0:
            raise KuCoinError("KuCoin websocket heartbeat parameters are invalid")
        return {
            "token": token,
            "endpoint": endpoint.rstrip("/"),
            "ping_interval_ms": ping_interval,
            "ping_timeout_ms": ping_timeout,
        }

    def get_deposit_history(
        self,
        *,
        currency: str | None = None,
        status: str | None = None,
        start_at_ms: int | None = None,
        end_at_ms: int | None = None,
        current_page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        if current_page <= 0:
            raise KuCoinError("current_page must be positive")
        if page_size <= 0 or page_size > 500:
            raise KuCoinError("page_size must be between 1 and 500")
        params = [
            ("currency", _optional_text(currency)),
            ("status", _optional_text(status)),
            ("startAt", start_at_ms),
            ("endAt", end_at_ms),
            ("currentPage", current_page),
            ("pageSize", page_size),
        ]
        payload = self._request("GET", DEPOSIT_HISTORY_PATH, params=params)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise KuCoinError("KuCoin deposit history response is missing data")
        items = data.get("items")
        if not isinstance(items, list):
            raise KuCoinError("KuCoin deposit history response is missing items")
        return {
            "current_page": int(data.get("currentPage") or current_page),
            "page_size": int(data.get("pageSize") or page_size),
            "total_pages": int(data.get("totalPage") or 1),
            "total_items": int(data.get("totalNum") or len(items)),
            "items": [dict(row) for row in items if isinstance(row, dict)],
        }

    def list_deposit_history(
        self,
        *,
        currency: str | None = None,
        status: str | None = None,
        start_at_ms: int | None = None,
        end_at_ms: int | None = None,
        page_size: int = 50,
        max_pages: int = 5,
    ) -> list[Dict[str, Any]]:
        if max_pages <= 0 or max_pages > MAX_HISTORY_PAGES:
            raise KuCoinError(f"max_pages must be between 1 and {MAX_HISTORY_PAGES}")
        rows: list[Dict[str, Any]] = []
        page = 1
        while page <= max_pages:
            result = self.get_deposit_history(
                currency=currency,
                status=status,
                start_at_ms=start_at_ms,
                end_at_ms=end_at_ms,
                current_page=page,
                page_size=page_size,
            )
            rows.extend(result["items"])
            if page >= max(1, int(result["total_pages"])):
                break
            page += 1
        return rows


def _asset_scale(asset: str, asset_scales: Mapping[str, int]) -> int:
    raw = asset_scales.get(asset.upper())
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0 or raw > 18:
        raise KuCoinError(f"No governed minor-unit scale configured for asset: {asset}")
    return raw


def _amount_minor(amount_text: Any, scale: int) -> int:
    text = _nonempty(str(amount_text), label="deposit.amount")
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise KuCoinError("KuCoin deposit amount is not a valid decimal") from exc
    if amount < 0:
        raise KuCoinError("KuCoin deposit amount must be non-negative")
    scaled = amount * (Decimal(10) ** scale)
    if scaled != scaled.to_integral_value():
        raise KuCoinError(
            "KuCoin deposit amount has more precision than the governed asset scale"
        )
    return int(scaled)


def normalize_deposit(
    deposit: Mapping[str, Any],
    *,
    asset_scales: Mapping[str, int],
) -> Dict[str, Any]:
    if not isinstance(deposit, Mapping):
        raise KuCoinError("KuCoin deposit must be an object")
    deposit_id = _nonempty(deposit.get("id"), label="deposit.id")
    currency = _nonempty(deposit.get("currency"), label="deposit.currency").upper()
    provider_state = _nonempty(deposit.get("status"), label="deposit.status").upper()
    scale = _asset_scale(currency, asset_scales)
    amount_minor = _amount_minor(deposit.get("amount"), scale)
    raw_hash = _canonical_hash(dict(deposit))
    try:
        updated_ms = int(deposit["updatedAt"]) if deposit.get("updatedAt") is not None else None
        created_ms = int(deposit["createdAt"]) if deposit.get("createdAt") is not None else None
    except (TypeError, ValueError) as exc:
        raise KuCoinError("KuCoin deposit timestamps must be integer milliseconds") from exc
    version_marker = str(updated_ms) if updated_ms is not None else raw_hash[:16]
    provider_event_id = f"kucoin-deposit:{deposit_id}:{provider_state}:{version_marker}"
    return {
        "deposit_id": deposit_id,
        "currency": currency,
        "amount_minor": amount_minor,
        "amount_text": str(deposit.get("amount")),
        "asset_scale": scale,
        "provider_state": provider_state,
        "payment_state": _STATUS_TO_LEDGER.get(provider_state, "UNKNOWN"),
        "address": _optional_text(deposit.get("address")),
        "memo": _optional_text(deposit.get("memo")),
        "network": _optional_text(deposit.get("chain") or deposit.get("chainId")),
        "wallet_tx_id": _optional_text(deposit.get("walletTxId")),
        "created_at_ms": created_ms,
        "updated_at_ms": updated_ms,
        "pre_confirms": deposit.get("preConfirms"),
        "confirms": deposit.get("confirms"),
        "current_confirms": deposit.get("currentConfirms"),
        "provider_event_id": provider_event_id,
        "provider_tx_ref": deposit_id,
        "raw_event_hash": raw_hash,
    }


def _open_crypto_intents(payment_path: str | None = None) -> list[Dict[str, Any]]:
    rows = payment_ledger.load_ledger(payment_path)
    settled_ids = {
        str(row.get("payment_intent_id"))
        for row in rows
        if row.get("provider") == PROVIDER
        and row.get("payment_state") == "SETTLED"
        and row.get("reconciliation_result") == "MATCHED"
        and row.get("payment_intent_id")
    }
    return [
        dict(row)
        for row in rows
        if row.get("event_type") == payment_ledger.EVENT_INTENT_CREATED
        and row.get("payment_intent_id")
        and str(row.get("payment_intent_id")) not in settled_ids
        and row.get("provider") == PROVIDER
        and row.get("payment_method") == "CRYPTO"
    ]


def _existing_provider_event(
    evidence: Mapping[str, Any], payment_path: str | None = None
) -> Optional[Dict[str, Any]]:
    for row in payment_ledger.load_ledger(payment_path):
        if row.get("provider") != PROVIDER:
            continue
        if (
            row.get("provider_event_id") == evidence.get("provider_event_id")
            and row.get("raw_event_hash") == evidence.get("raw_event_hash")
        ):
            return dict(row)
    return None


def _attribution(
    evidence: Mapping[str, Any], candidates: list[Dict[str, Any]]
) -> tuple[str, Optional[str]]:
    same_currency = [
        row for row in candidates if row.get("currency") == evidence.get("currency")
    ]
    exact = [
        row
        for row in same_currency
        if row.get("amount_minor") == evidence.get("amount_minor")
    ]
    if len(exact) > 1:
        return "AMBIGUOUS", None
    if len(exact) == 1:
        return "MATCHED", str(exact[0]["payment_intent_id"])
    if len(same_currency) == 1:
        intended = int(same_currency[0].get("amount_minor") or 0)
        observed = int(evidence.get("amount_minor") or 0)
        if observed < intended:
            return "UNDERPAID", str(same_currency[0]["payment_intent_id"])
        if observed > intended:
            return "OVERPAID", str(same_currency[0]["payment_intent_id"])
    if same_currency:
        return "AMBIGUOUS", None
    return "UNMATCHED", None


def _fallback_evidence(deposit: Mapping[str, Any], *, prefix: str) -> Dict[str, Any]:
    raw_hash = _canonical_hash(dict(deposit))
    return {
        "deposit_id": _optional_text(deposit.get("id")),
        "currency": _optional_text(deposit.get("currency")),
        "amount_text": _optional_text(deposit.get("amount")),
        "provider_state": _optional_text(deposit.get("status")),
        "address": _optional_text(deposit.get("address")),
        "memo": _optional_text(deposit.get("memo")),
        "network": _optional_text(deposit.get("chain") or deposit.get("chainId")),
        "wallet_tx_id": _optional_text(deposit.get("walletTxId")),
        "provider_tx_ref": _optional_text(deposit.get("id")),
        "provider_event_id": f"{prefix}:{raw_hash[:24]}",
        "raw_event_hash": raw_hash,
    }


def _manual_review(
    *,
    evidence: Mapping[str, Any],
    reason: str,
    candidate_payment_intent_id: str | None,
    path: str,
    trigger: str,
    detail: str | None = None,
) -> Dict[str, Any]:
    payload = {
        "event_type": EVENT_MANUAL_REVIEW,
        "provider": PROVIDER,
        "status": "MANUAL_REVIEW_REQUIRED",
        "reason": reason,
        "candidate_payment_intent_id": candidate_payment_intent_id,
        "trigger": trigger,
        "detail": detail,
    }
    for key in (
        "deposit_id",
        "provider_event_id",
        "provider_tx_ref",
        "wallet_tx_id",
        "currency",
        "amount_minor",
        "amount_text",
        "asset_scale",
        "provider_state",
        "address",
        "memo",
        "network",
        "pre_confirms",
        "confirms",
        "current_confirms",
        "created_at_ms",
        "updated_at_ms",
        "raw_event_hash",
    ):
        payload[key] = evidence.get(key)
    idem = (
        f"kucoin-manual:{evidence.get('provider_event_id')}:{reason}:"
        f"{candidate_payment_intent_id or 'none'}"
    )
    row, appended = _append_event(
        path=path, payload=payload, idempotency_key=idem
    )
    return {
        "status": "MANUAL_REVIEW_REQUIRED",
        "reason": reason,
        "ledger_appended": False,
        "adapter_appended": appended,
        "record": row,
    }


def reconcile_deposit(
    deposit: Mapping[str, Any],
    *,
    asset_scales: Mapping[str, int],
    path: str | None = None,
    payment_path: str | None = None,
    trigger: str = "POLL",
) -> Dict[str, Any]:
    target = path or events_path()
    currency_hint = str(deposit.get("currency") or "").strip().upper()

    # #159 currently enforces a three-letter alphabetic currency. Do not
    # silently widen that authority in a provider adapter (e.g. USDT).
    if len(currency_hint) != 3 or not currency_hint.isalpha():
        return _manual_review(
            evidence=_fallback_evidence(
                deposit, prefix="kucoin-unsupported-currency"
            ),
            reason="LEDGER_CURRENCY_CONTRACT_UNSUPPORTED",
            candidate_payment_intent_id=None,
            path=target,
            trigger=trigger,
            detail=(
                "Current payment ledger requires a three-letter alphabetic currency; "
                "no settlement evidence was written."
            ),
        )

    try:
        evidence = normalize_deposit(deposit, asset_scales=asset_scales)
    except KuCoinError as exc:
        return _manual_review(
            evidence=_fallback_evidence(
                deposit, prefix="kucoin-normalization-review"
            ),
            reason="NORMALIZATION_REVIEW_REQUIRED",
            candidate_payment_intent_id=None,
            path=target,
            trigger=trigger,
            detail=str(exc),
        )

    existing = _existing_provider_event(evidence, payment_path)
    if existing is not None:
        return {
            "status": "DUPLICATE_PROVIDER_EVENT",
            "ledger_appended": False,
            "record": existing,
        }

    candidates = _open_crypto_intents(payment_path)
    attribution, candidate_id = _attribution(evidence, candidates)
    if attribution != "MATCHED" or candidate_id is None:
        return _manual_review(
            evidence=evidence,
            reason=attribution,
            candidate_payment_intent_id=candidate_id,
            path=target,
            trigger=trigger,
        )

    intent = next(
        row for row in candidates if str(row.get("payment_intent_id")) == candidate_id
    )
    settled_at_ts = None
    if evidence["payment_state"] == "SETTLED" and evidence.get("updated_at_ms") is not None:
        settled_at_ts = int(evidence["updated_at_ms"]) / 1000.0
    received_at_ts = (
        int(evidence["updated_at_ms"]) / 1000.0
        if evidence.get("updated_at_ms") is not None
        else None
    )
    ledger_result = payment_ledger.ingest_provider_event(
        payment_intent_id=candidate_id,
        provider=PROVIDER,
        payment_state=str(evidence["payment_state"]),
        provider_state=str(evidence["provider_state"]),
        amount_minor=int(evidence["amount_minor"]),
        currency=str(evidence["currency"]),
        raw_event_hash=str(evidence["raw_event_hash"]),
        idempotency_key=str(evidence["provider_event_id"]),
        provider_event_id=str(evidence["provider_event_id"]),
        provider_tx_ref=str(evidence["provider_tx_ref"]),
        wallet_tx_id=evidence.get("wallet_tx_id"),
        settled_at_ts=settled_at_ts,
        audit_correlation_id=str(intent.get("audit_correlation_id") or _opaque_id()),
        received_at_ts=received_at_ts,
        path=payment_path,
    )
    adapter_payload = {
        "event_type": EVENT_DEPOSIT_RECONCILED,
        "provider": PROVIDER,
        "payment_intent_id": candidate_id,
        "ledger_status": ledger_result.get("status"),
        "trigger": trigger,
    }
    for key in (
        "deposit_id",
        "provider_event_id",
        "provider_tx_ref",
        "wallet_tx_id",
        "currency",
        "amount_minor",
        "amount_text",
        "asset_scale",
        "provider_state",
        "payment_state",
        "address",
        "memo",
        "network",
        "pre_confirms",
        "confirms",
        "current_confirms",
        "created_at_ms",
        "updated_at_ms",
        "raw_event_hash",
    ):
        adapter_payload[key if key != "payment_state" else "normalized_payment_state"] = evidence.get(key)
    row, appended = _append_event(
        path=target,
        payload=adapter_payload,
        idempotency_key=f"kucoin-reconcile:{evidence['provider_event_id']}",
    )
    return {
        "status": str(ledger_result.get("status")),
        "ledger_appended": bool(ledger_result.get("appended")),
        "adapter_appended": appended,
        "ledger_result": ledger_result,
        "record": row,
    }


def reconcile_recent_deposits(
    *,
    client: KuCoinClient,
    asset_scales: Mapping[str, int],
    path: str | None = None,
    payment_path: str | None = None,
    trigger: str = "POLL",
    start_at_ms: int | None = None,
    end_at_ms: int | None = None,
    max_pages: int = 5,
) -> Dict[str, Any]:
    target = path or events_path()
    try:
        deposits = client.list_deposit_history(
            start_at_ms=start_at_ms,
            end_at_ms=end_at_ms,
            max_pages=max_pages,
        )
    except KuCoinProviderUnavailable as exc:
        row, appended = _append_event(
            path=target,
            payload={
                "event_type": EVENT_PROVIDER_UNAVAILABLE,
                "provider": PROVIDER,
                "status": "PROVIDER_UNAVAILABLE",
                "trigger": trigger,
                "error": _redact(exc),
            },
        )
        return {
            "status": "PROVIDER_UNAVAILABLE",
            "ledger_appended": False,
            "adapter_appended": appended,
            "record": row,
            "results": [],
        }

    ordered = sorted(
        deposits,
        key=lambda row: (
            int(row.get("updatedAt") or row.get("createdAt") or 0),
            str(row.get("id") or ""),
        ),
    )
    results = [
        reconcile_deposit(
            row,
            asset_scales=asset_scales,
            path=target,
            payment_path=payment_path,
            trigger=trigger,
        )
        for row in ordered
    ]
    return {
        "status": "RECONCILED",
        "deposit_count": len(ordered),
        "results": results,
    }


def _default_ws_connect(url: str, timeout: int):
    try:
        import websocket
    except ImportError as exc:
        raise KuCoinError("websocket-client dependency missing") from exc
    return websocket.create_connection(url, timeout=timeout)


class KuCoinAccountWatcher:
    """Classic private balance watcher; WS events only trigger REST reconciliation."""

    def __init__(
        self,
        *,
        client: KuCoinClient,
        asset_scales: Mapping[str, int],
        path: str | None = None,
        payment_path: str | None = None,
        ws_connect_fn: Callable[[str, int], Any] = _default_ws_connect,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.client = client
        self.asset_scales = dict(asset_scales)
        self.path = path or events_path()
        self.payment_path = payment_path
        self._ws_connect_fn = ws_connect_fn
        self._sleep_fn = sleep_fn

    def _record_trigger(self, message: Mapping[str, Any]) -> tuple[Dict[str, Any], bool]:
        data = message.get("data")
        if not isinstance(data, dict):
            data = {}
        raw_hash = _canonical_hash(dict(message))
        relation_event_id = _optional_text(data.get("relationEventId"))
        idem = (
            f"kucoin-ws-trigger:{relation_event_id}"
            if relation_event_id
            else f"kucoin-ws-trigger:{raw_hash}"
        )
        return _append_event(
            path=self.path,
            payload={
                "event_type": EVENT_WS_TRIGGER,
                "provider": PROVIDER,
                "topic": message.get("topic"),
                "relation_event": data.get("relationEvent"),
                "relation_event_id": relation_event_id,
                "currency": data.get("currency"),
                "raw_event_hash": raw_hash,
            },
            idempotency_key=idem,
        )

    def handle_message(self, raw_message: str | bytes | Mapping[str, Any]) -> Dict[str, Any]:
        if isinstance(raw_message, Mapping):
            message = dict(raw_message)
        else:
            try:
                text = (
                    raw_message.decode("utf-8")
                    if isinstance(raw_message, bytes)
                    else str(raw_message)
                )
                parsed = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise KuCoinError("KuCoin websocket message is invalid JSON") from exc
            if not isinstance(parsed, dict):
                raise KuCoinError("KuCoin websocket message must be an object")
            message = dict(parsed)

        data = message.get("data")
        relation_event = data.get("relationEvent") if isinstance(data, dict) else None
        is_deposit = (
            message.get("type") == "message"
            and message.get("topic") == BALANCE_TOPIC
            and relation_event == DEPOSIT_RELATION_EVENT
        )
        if not is_deposit:
            return {"status": "IGNORED"}

        trigger_row, appended = self._record_trigger(message)
        result = reconcile_recent_deposits(
            client=self.client,
            asset_scales=self.asset_scales,
            path=self.path,
            payment_path=self.payment_path,
            trigger=(
                f"WS:{trigger_row.get('relation_event_id') or trigger_row.get('raw_event_hash')}"
            ),
        )
        return {
            "status": "REST_RECONCILIATION_TRIGGERED",
            "trigger_appended": appended,
            "trigger_record": trigger_row,
            "reconciliation": result,
        }

    @staticmethod
    def _send_json(ws: Any, payload: Mapping[str, Any]) -> None:
        ws.send(json.dumps(dict(payload), separators=(",", ":")))

    def run_session(self, *, max_messages: int | None = None) -> Dict[str, Any]:
        token = self.client.get_private_ws_token()
        connect_id = _opaque_id()
        url = (
            f"{token['endpoint']}?token={quote(str(token['token']), safe='')}"
            f"&connectId={quote(connect_id, safe='')}"
        )
        timeout_seconds = max(1, int(token["ping_timeout_ms"]) // 1000)
        ws = self._ws_connect_fn(url, timeout_seconds)
        processed = 0
        try:
            welcome_raw = ws.recv()
            welcome = json.loads(
                welcome_raw.decode("utf-8")
                if isinstance(welcome_raw, bytes)
                else str(welcome_raw)
            )
            if not isinstance(welcome, dict) or welcome.get("type") != "welcome":
                raise KuCoinError("KuCoin websocket did not provide a welcome message")

            self._send_json(
                ws,
                {
                    "id": _opaque_id(),
                    "type": "subscribe",
                    "topic": BALANCE_TOPIC,
                    "response": True,
                    "privateChannel": "true",
                },
            )

            while True:
                if max_messages is not None and processed >= max_messages:
                    return {"status": "SESSION_COMPLETE", "processed": processed}
                try:
                    raw = ws.recv()
                except Exception as exc:
                    if "timeout" in type(exc).__name__.lower():
                        self._send_json(ws, {"id": _opaque_id(), "type": "ping"})
                        continue
                    raise
                if raw in (None, ""):
                    raise KuCoinProviderUnavailable("KuCoin websocket connection closed")
                try:
                    message = json.loads(
                        raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                    )
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise KuCoinError("KuCoin websocket message is invalid JSON") from exc
                if isinstance(message, dict) and message.get("type") == "ping":
                    self._send_json(
                        ws,
                        {"id": str(message.get("id") or _opaque_id()), "type": "pong"},
                    )
                    continue
                if isinstance(message, dict) and message.get("type") == "pong":
                    continue
                self.handle_message(message)
                processed += 1
        finally:
            close = getattr(ws, "close", None)
            if callable(close):
                close()

    def run_with_reconnect(
        self,
        *,
        max_reconnects: int = 3,
        max_messages_per_session: int | None = None,
    ) -> Dict[str, Any]:
        if max_reconnects < 0 or max_reconnects > 100:
            raise KuCoinError("max_reconnects must be between 0 and 100")
        attempts = 0
        while True:
            try:
                result = self.run_session(max_messages=max_messages_per_session)
                return {**result, "reconnects": attempts}
            except Exception as exc:
                retryable = isinstance(
                    exc,
                    (KuCoinProviderUnavailable, OSError, ConnectionError, TimeoutError),
                ) or any(
                    marker in type(exc).__name__.lower()
                    for marker in ("websocket", "connection", "timeout")
                )
                if isinstance(exc, KuCoinError) and not isinstance(
                    exc, KuCoinProviderUnavailable
                ):
                    retryable = False
                if not retryable:
                    raise
                if attempts >= max_reconnects:
                    raise KuCoinProviderUnavailable(
                        f"KuCoin websocket unavailable after {attempts} reconnects: {_redact(exc)}"
                    ) from exc
                attempts += 1
                _append_event(
                    path=self.path,
                    payload={
                        "event_type": EVENT_WATCHER_RECONNECT,
                        "provider": PROVIDER,
                        "attempt": attempts,
                        "error_type": type(exc).__name__,
                    },
                )
                self._sleep_fn(min(0.5 * (2 ** (attempts - 1)), 4.0))

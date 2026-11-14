"""Reuse existing contracts; never copy/reimplement the strategy or change canon."""
from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
SEND = REPO / "send"
if str(SEND) not in sys.path:
    sys.path.insert(0, str(SEND))

from billing.contracts import get_strategy_product, load_billing_contract
from billing.subscription_registry import load_subscription_events, resolve_entitlement
from core.signal_event import SignalEvent

PRODUCT = "BINARY_TRADING"


def channels() -> list[dict]:
    contract = load_billing_contract()
    config = json.loads((SEND / "config/channel_config.json").read_text())
    result = []
    for plan in get_strategy_product(PRODUCT, contract)["plans"]:
        tier = plan["tier"]
        result.append({
            "id": tier, "name": tier.title(), "plan_id": plan["plan_id"],
            "daily_limit": config.get(plan["signal_limit_ref"]),
            "requires_payment": plan["requires_payment"],
            "pricing": plan["pricing"],
        })
    return result


def signal(candidate: dict) -> SignalEvent:
    """Validate the actual shared engine contract, including exact Execution Time."""
    names = {field.name for field in fields(SignalEvent)}
    try:
        obj = SignalEvent(**{key: value for key, value in candidate.items() if key in names})
    except (TypeError,ValueError) as exc:
        raise ValueError("A complete, valid canonical SignalEvent is required.") from exc
    if not all((obj.fsm_transition_id, obj.execution_attempt_id, obj.decision_id)):
        raise ValueError("Canonical FSM/execution/decision references are required")
    return obj


def public_signal(obj: SignalEvent) -> dict:
    return {
        "signal_id": obj.signal_id, "stage": obj.stage, "symbol": obj.symbol,
        "timeframe": obj.timeframe, "direction": obj.direction,
        "score_total": obj.score_total, "buffer_mode": obj.buffer_mode,
        "buffer_distance": obj.buffer_distance, "entry_price": obj.entry_price,
        "created_ts": obj.created_ts, "candle_ts": obj.candle_ts,
        "execution_time_available": obj.execution_time_available,
        "confirm_expiry_min_minutes": obj.confirm_expiry_min_minutes,
        "confirm_expiry_max_minutes": obj.confirm_expiry_max_minutes,
        "open_now_expiry_minutes": obj.open_now_expiry_minutes,
        "expires_at": (obj.created_ts + obj.open_now_expiry_minutes * 60)
        if obj.stage == "OPEN_NOW" else None,
        "strategy_product_id": PRODUCT,
    }


def manifest() -> dict:
    root = SEND / "docs/canonical/active"
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return {
        "strategy": "BINARY_STRATEGY_V2", "strategy_product_id": PRODUCT,
        "canonical_files": len(files), "canonical_sha256": digest.hexdigest(),
        "master_index": "send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md",
        "strategy_source": "send/core/strategy_v2.py",
        "engine_source": "send/core/signal_engine.py",
        "membership_model": "EXCLUSIVE", "transport": "APP",
    }

from __future__ import annotations

from typing import Mapping, Tuple


def _value(snapshot: Mapping[str, object], key: str) -> str:
    value = snapshot.get(key)
    return str(value).strip().upper() if value is not None else "UNKNOWN"


def human_status_summary(snapshot: Mapping[str, object]) -> Tuple[str, ...]:
    """Translate runtime evidence into plain language without inventing state."""
    phase = _value(snapshot, "runtime_phase")
    market = _value(snapshot, "market_data_state")
    recovery = _value(snapshot, "recovery_state")
    shadow = _value(snapshot, "shadow_mode")
    broker = _value(snapshot, "broker_state")
    history_ready = snapshot.get("market_data_history_ready")

    if phase == "RUNNING":
        bot = "Bot: online and running."
    elif phase == "UNKNOWN":
        bot = "Bot: current operating state is not reported."
    else:
        bot = f"Bot: not in the normal running state ({phase})."

    if market == "READY":
        market_meaning = "Market information: usable for strategy evaluation."
    elif market == "MARKET_DATA_COLLECTING":
        market_meaning = "Market information: real history is still being prepared; decisions are blocked."
    elif market in {"MARKET_DATA_UNAVAILABLE", "UNAVAILABLE"}:
        market_meaning = "Market information: unusable right now; decisions are blocked."
    elif market == "MARKET_DATA_LIMITED":
        market_meaning = "Market information: only partially available; normal decisions are not trusted."
    elif market == "UNKNOWN":
        market_meaning = "Market information: the system has not reported enough evidence to judge it."
    else:
        market_meaning = f"Market information: reported as {market}; check the detailed evidence below."

    if history_ready is True and market == "READY":
        decisions = "Strategy: enough recorded history is available for evaluation."
    elif history_ready is False:
        decisions = "Strategy: no decision can pass while the required history is incomplete."
    else:
        decisions = "Strategy: readiness cannot be confirmed from the available evidence."

    if shadow == "ON" and broker.startswith("DISABLED"):
        trading = "Real trading: impossible; the bot can observe and calculate only."
    elif broker.startswith("ENABLED"):
        trading = "Real trading: broker execution is enabled; owner attention is required."
    elif shadow == "OFF":
        trading = "Real trading protection: shadow mode is off; owner attention is required."
    else:
        trading = "Real trading: safety state cannot be fully confirmed from the available evidence."

    if broker.startswith("ENABLED") or shadow == "OFF":
        action = "Required action: inspect execution safety settings before continuing."
    elif recovery == "DEGRADED_SAFE":
        action = "Required action: none; the bot is protecting itself and blocking unsafe decisions."
    elif market in {"MARKET_DATA_UNAVAILABLE", "MARKET_DATA_LIMITED", "MARKET_DATA_COLLECTING", "UNAVAILABLE"}:
        action = "Required action: none; the bot has already blocked decisions automatically."
    elif phase == "RUNNING" and market == "READY":
        action = "Required action: none; reported operating evidence is normal."
    else:
        action = "Required action: inspect the detailed evidence below; normal operation is not confirmed."

    return bot, market_meaning, decisions, trading, action

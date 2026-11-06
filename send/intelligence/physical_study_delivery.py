"""Private prospective study notifications, outside canonical trade publication.

These are explicitly uncalibrated Model Time observations. They never build a
SignalEvent, approve an expiry artifact, count a canonical OPEN, or call a broker.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import time
import threading

from core import owner_signal_delivery as owner, storage, telegram_publisher
from intelligence import buffer_expiry_evidence
from intelligence import physical_expiry_calibration as study

STATUSES = {"RESERVED", "API_ACCEPTED", "FAILED", "UNKNOWN", "SKIPPED_STALE", "SKIPPED_STAGE_GUARD"}
_DELIVERY_IN_FLIGHT = threading.Lock()


def validate_delivery(row):
    delivery = row.get("study_delivery")
    if delivery is None:
        return
    if not isinstance(delivery, dict) or set(delivery) != {"entry", "result"}:
        raise ValueError("INVALID_STUDY_DELIVERY")
    snapshot = row.get("decision_snapshot") or {}
    if (snapshot.get("decision_kind") != "OPEN_NOW"
        or snapshot.get("structure", {}).get("feasibility_state") != "VALID"
        or snapshot.get("time", {}).get("time_state") != "READY"
        or snapshot.get("market_context", {}).get("noise_context") != "STABLE"
        or snapshot.get("market_context", {}).get("volatility_state") != "ACTIVE"):
        raise ValueError("STUDY_DELIVERY_REQUIRES_ACCEPTED_PHYSICAL_OPEN")
    for phase, receipt in delivery.items():
        if receipt is None:
            continue
        if (not isinstance(receipt, dict) or receipt.get("status") not in STATUSES
            or type(receipt.get("attempted_ts")) not in (int, float)
            or receipt["attempted_ts"] < row["created_ts"]):
            raise ValueError("INVALID_STUDY_RECEIPT")
        study._number(receipt["attempted_ts"])
        if receipt["status"] == "API_ACCEPTED":
            if (type(receipt.get("message_id")) is not int or receipt["message_id"] <= 0
                or study._number(receipt.get("api_accepted_ts")) < receipt["attempted_ts"]):
                raise ValueError("INVALID_STUDY_API_ACCEPTANCE")
        if phase == "result" and receipt["status"] == "API_ACCEPTED":
            if (delivery.get("entry") or {}).get("status") != "API_ACCEPTED":
                raise ValueError("STUDY_RESULT_WITHOUT_ENTRY_RECEIPT")


def _stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime("%H:%M:%S UTC")


def render_entry(identity, row):
    entry = row["entry"]
    return ("🧪 OPEN_NOW · STUDIU V3\n"
            f"EUR/USD · {row['direction']}\n"
            f"Preț observat: {entry['price']:.15g}\n"
            f"Început observare: {_stamp(entry['observed_ts'])}\n"
            f"Expirare simulată: {row['model_seconds']/60:.15g} min · "
            f"{_stamp(entry['observed_ts'] + row['model_seconds'])}\n"
            f"Buffer urmărit: {row['buffer_snapshot']['buffer_distance']:.15g}\n"
            "Simulare pe cotații reale · calibrare în colectare\n"
            f"ID studiu: {identity[:12]}")


def render_result(identity, row):
    baseline = row["candidates"][0]  # predeclared Model Time, never the best eventual candidate
    measured = buffer_expiry_evidence.measure(row["direction"], row["entry"],
                                              baseline["quote"], row["buffer_snapshot"])
    label = {"MET": "ATINS", "NOT_MET": "NEATINS", "UNAVAILABLE": "DATE INDISPONIBILE"}[measured["status"]]
    observed = _stamp(baseline["quote"]["observed_ts"]) if baseline["quote"] else "cotație lipsă"
    return ("🧪 REZULTAT STUDIU V3\n"
            f"EUR/USD · {row['direction']} · {row['model_seconds']/60:.15g} min\n"
            f"Observație la expirare: {observed}\n"
            f"Direcție la expirare: {baseline['outcome']}\n"
            f"Buffer la expirare: {label}\n"
            "Rezultat al simulării pe cotații observate\n"
            f"ID studiu: {identity[:12]}")


def _reserve(path, phase, now):
    with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=.2):
        state = study._read(path)
        if state is None:
            return None
        changed = False
        for identity, row in sorted(state["records"].items(), key=lambda pair: pair[1]["created_ts"]):
            delivery = row.get("study_delivery")
            if (not isinstance(delivery, dict) or delivery.get(phase) is not None
                or row["entry"] is None or now < row["created_ts"]):
                continue
            status = "RESERVED"
            if phase == "entry":
                if now - row["created_ts"] > study.quotes.MAX_ENTRY_DELAY_SECONDS:
                    status = "SKIPPED_STALE"
                else:
                    context = row["policies"]["PHYSICAL_ONLY_V3"]
                    reason = owner.stage_block_reason({"stage": "OPEN_NOW",
                        "signal_id": context["opportunity_signal_id"]}, now_ts=row["created_ts"])
                    if reason is not None:
                        status = "SKIPPED_STAGE_GUARD"
            elif ((delivery.get("entry") or {}).get("status") != "API_ACCEPTED"
                  or row["candidates"][0]["outcome"] in {"PENDING", "INFEASIBLE"}):
                continue
            delivery[phase] = {"status": status, "attempted_ts": now}
            changed = True
            if status == "RESERVED":
                study._save(path, state)  # reserve before transport; ambiguous delivery is never retried
                return identity, deepcopy(row)
        if changed:
            study._save(path, state)
    return None


def dispatch(*, now_ts, active_provider):
    destination = owner.destination()
    path = study._path()
    if destination is None or path is None or active_provider != "FINNHUB":
        return
    for phase in ("entry", "result"):
        reserved = _reserve(path, phase, now_ts)
        if reserved is None:
            continue
        identity, row = reserved
        text = render_entry(identity, row) if phase == "entry" else render_result(identity, row)
        receipt = {"status": "UNKNOWN", "attempted_ts": now_ts}
        try:
            response = telegram_publisher.send_message(chat_id=destination, text=text)
            message_id = (response.get("result") or {}).get("message_id")
            accepted_ts = time.time()
            if (response.get("ok") is True and type(message_id) is int and message_id > 0
                and accepted_ts >= now_ts):
                receipt.update(status="API_ACCEPTED", message_id=message_id,
                               api_accepted_ts=accepted_ts)
            elif response.get("ok") is False:
                receipt["status"] = "FAILED"
        except telegram_publisher.TelegramAPIError:
            receipt["status"] = "FAILED"
        except Exception:
            pass  # ambiguous network acceptance: retain UNKNOWN and do not retry an OPEN
        with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=.2):
            state = study._read(path)
            state["records"][identity]["study_delivery"][phase] = receipt
            study._save(path, state)
        print("TSP_PHYSICAL_STUDY_DELIVERY " + json.dumps({
            "phase": phase, "status": receipt["status"], "study_id": identity,
            "observed_at": now_ts, "truth_domain": "HYPOTHETICAL_RESEARCH",
            "execution_calibration_proven": False, "broker_executed": False,
        }, sort_keys=True), flush=True)


def dispatch_async(*, now_ts, active_provider):
    """Keep transport latency outside the quote-measurement loop; one sender."""
    if not _DELIVERY_IN_FLIGHT.acquire(blocking=False):
        return None
    def run():
        try:
            dispatch(now_ts=time.time(), active_provider=active_provider)
        except Exception as exc:
            print("TSP_PHYSICAL_STUDY_DELIVERY_UNAVAILABLE " + json.dumps({
                "error_class": type(exc).__name__, "broker_executed": False}), flush=True)
        finally:
            _DELIVERY_IN_FLIGHT.release()
    thread = threading.Thread(target=run, name="physical-study-delivery", daemon=True)
    try:
        thread.start()
    except Exception:
        _DELIVERY_IN_FLIGHT.release()
        raise
    return thread

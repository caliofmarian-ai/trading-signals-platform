"""Private prospective study notifications, outside canonical trade publication.

These are explicitly uncalibrated Model Time observations. They never build a
SignalEvent, approve an expiry artifact, count a canonical OPEN, or call a broker.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import time
import threading

from core import owner_signal_delivery as owner, owner_signal_number, storage, telegram_publisher
from core.buffer_zone import BUFFER_POSITION_LABELS, classify_buffer_position
from intelligence import buffer_expiry_evidence
from intelligence import physical_expiry_calibration as study
from core.signal_presentation import direction_label

STATUSES = {"RESERVED", "API_ACCEPTED", "FAILED", "UNKNOWN", "SKIPPED_STALE", "SKIPPED_STAGE_GUARD", "SKIPPED_DESTINATION_CHANGED"}
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
        if "format" in receipt and receipt["format"] not in {"TEXT", "PHOTO"}:
            raise ValueError("INVALID_STUDY_RECEIPT_FORMAT")
        if "signal_label" in receipt and (not isinstance(receipt["signal_label"], str)
                or not receipt["signal_label"].strip() or len(receipt["signal_label"]) > 128):
            raise ValueError("INVALID_STUDY_RECEIPT_SIGNAL_LABEL")
        if "destination_id" in receipt and (type(receipt["destination_id"]) is not int or receipt["destination_id"] <= 0):
            raise ValueError("INVALID_STUDY_RECEIPT_DESTINATION")
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


def _entry_event(row):
    """Project the frozen study observation without creating an execution signal."""
    entry = row["entry"]
    return {"stage": "OPEN_NOW", "symbol": "EUR/USD", "direction": row["direction"],
            "entry_price": entry["price"], "created_ts": row["created_ts"],
            "entry_ts": entry["observed_ts"],
            "expiry_ts": entry["observed_ts"] + row["model_seconds"],
            "study_duration_minutes": row["model_seconds"] / 60}


def render_entry(row, signal_label):
    from core.signal_card import render_signal_caption

    return render_signal_caption(_entry_event(row), signal_label, study=True)


def _render_entry_card(row, signal_label):
    from core.signal_card import render_signal_card

    return render_signal_card(_entry_event(row), signal_label, study=True)


def render_result(identity, row, signal_label):
    baseline = row["candidates"][0]  # predeclared Model Time, never the best eventual candidate
    expiry_quote = baseline["quote"]
    measured = buffer_expiry_evidence.measure(row["direction"], row["entry"],
                                              expiry_quote, row["buffer_snapshot"])
    label = {"MET": "DA", "NOT_MET": "NU", "UNAVAILABLE": "DATE INDISPONIBILE"}[measured["status"]]
    position = classify_buffer_position(row["direction"], row["entry"]["price"],
        row["buffer_snapshot"]["buffer_distance"], expiry_quote["price"] if expiry_quote else None)
    result = "WIN fragil" if baseline["outcome"] == "WIN" and position == "INSIDE_BUFFER" else baseline["outcome"]
    observed = (f"{expiry_quote['price']:.10g} la {_stamp(expiry_quote['observed_ts'])}"
                if expiry_quote else "cotație lipsă")
    expiry_ts = row["entry"]["observed_ts"] + baseline["horizon_seconds"]
    return ("🧪 REZULTAT STUDIU V3\n"
            f"EUR/USD · {direction_label(row['direction'])} · {row['model_seconds']/60:.15g} min\n"
            f"Intrare observată: {row['entry']['price']:.10g} la {_stamp(row['entry']['observed_ts'])}\n"
            f"Expirare simulată: {_stamp(expiry_ts)}\n"
            f"Observație la expirare: {observed}\n"
            f"Direcție la expirare: {result}\n"
            f"Poziție la expirare: {BUFFER_POSITION_LABELS[position]}\n"
            f"Marjă completă la expirare: {label}\n"
            "Rezultat al simulării pe cotații observate"
            + (f"\n{signal_label} · Dublin" if signal_label else "\nNumăr indisponibil"))


def _render_chart(row, signal_label):
    from intelligence.physical_study_chart import render_market_chart

    entry = row["entry"]
    baseline = row["candidates"][0]
    expiry_ts = entry["observed_ts"] + baseline["horizon_seconds"]
    quote = baseline["quote"] or {}
    return render_market_chart(direction=row["direction"], entry_ts=entry["observed_ts"],
                               entry_price=entry["price"], expiry_ts=expiry_ts,
                               expiry_quote_ts=quote.get("observed_ts"), expiry_price=quote.get("price"),
                               buffer_distance=row["buffer_snapshot"]["buffer_distance"],
                               outcome=baseline["outcome"], signal_label=signal_label)


def _reserve(path, phase, now, destination):
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
            elif delivery["entry"].get("destination_id", destination) != destination:
                status = "SKIPPED_DESTINATION_CHANGED"
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
        reserved = _reserve(path, phase, now_ts, destination)
        if reserved is None:
            continue
        identity, row = reserved
        signal_id = row["policies"]["PHYSICAL_ONLY_V3"]["opportunity_signal_id"]
        receipt = {"status": "UNKNOWN", "attempted_ts": now_ts, "format": "TEXT", "destination_id": destination}
        signal_label = None
        try:
            photo = None
            if phase == "entry":
                signal_label = owner_signal_number.reserve_lifecycle(signal_id, now_ts)
                text = render_entry(row, signal_label)
                try:
                    photo = _render_entry_card(row, signal_label)
                except Exception as exc:
                    print("TSP_PHYSICAL_STUDY_CARD_UNAVAILABLE " + json.dumps({
                        "study_id": identity, "error_class": type(exc).__name__}), flush=True)
                    text += "\nImagine indisponibilă pentru această observație."
            else:
                signal_label = (row["study_delivery"]["entry"].get("signal_label")
                                or owner_signal_number.lookup(signal_id, study=True)
                                or owner_signal_number.lookup_lifecycle(signal_id))
                text = render_result(identity, row, signal_label)
                try:
                    photo = _render_chart(row, signal_label)
                except Exception as exc:
                    print("TSP_PHYSICAL_STUDY_CHART_UNAVAILABLE " + json.dumps({
                        "study_id": identity, "error_class": type(exc).__name__}), flush=True)
                    text += "\nGrafic indisponibil pentru această observație."
            if signal_label is not None:
                receipt["signal_label"] = signal_label
            entry_receipt = row["study_delivery"]["entry"] if phase == "result" else {}
            reply_id = entry_receipt["message_id"] if entry_receipt.get("destination_id") == destination else None
            if photo is not None:
                receipt["format"] = "PHOTO"
                response = telegram_publisher.send_photo(chat_id=destination, photo=photo, caption=text,
                    reply_to_message_id=reply_id)
            elif reply_id is not None:
                response = telegram_publisher.send_message(chat_id=destination, text=text, reply_to_message_id=reply_id)
            else:
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
            "format": receipt["format"], "signal_label": signal_label,
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


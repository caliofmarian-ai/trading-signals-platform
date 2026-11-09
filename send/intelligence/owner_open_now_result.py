"""Private expiry reports for prospectively published canonical OPEN_NOW signals."""

import json
import threading
import time

from core import owner_signal_delivery as owner, storage, telegram_publisher
from core import trade_temporal_telemetry as telemetry
from core.buffer_zone import BUFFER_POSITION_LABELS, classify_buffer_position
from core.signal_presentation import direction_label, stamp
from intelligence import buffer_expiry_evidence, physical_study_chart


_IN_FLIGHT = threading.Lock()
_TITLE = "OPEN NOW  /  REZULTAT DE PIAȚĂ V3"


def _next_ready(registry, destination):
    reports = registry.get("owner_expiry_reports", {})
    if not isinstance(reports, dict):
        return None
    for trade_id, report in reports.items():
        if report.get("status") != "PENDING":
            continue
        publication = report["publication"]
        if publication["destination_id"] != destination:
            continue
        record = registry["trades"].get(trade_id)
        if (record is None or record.get("stage") != "OPEN_NOW" or record.get("market_provider") != "FINNHUB"
                or record["symbol"].upper().replace("/", "") != "EURUSD"
                or record.get("pre_trade_snapshot", {}).get("decision_policy") != "PHYSICAL_ONLY_V3"
                or publication["route"] != "OWNER_PRIVATE" or publication not in record["publication_evidence"]):
            continue
        expiry = record["checkpoints"]["expiry"]
        observed = (expiry["state"] == "OBSERVED" and expiry["provider"] == "FINNHUB"
                    and expiry["directional_result"] in {"WIN", "LOSS", "DRAW"})
        if observed or (expiry["state"] == "EVIDENCE_GAP" and expiry["gap_reason"]):
            return trade_id, record, report
    return None


def _reserve(destination, now):
    with storage.with_lock("trade_temporal_telemetry", timeout_sec=0.2):
        registry = telemetry._load_registry()
        result = _next_ready(registry, destination)
        if result is not None:
            result[2].update(status="RESERVED", attempted_ts=now)
            telemetry._save_registry(registry)
        return result


def _caption(record, expiry, outcome, number):
    frozen = buffer_expiry_evidence.snapshot(record["buffer_price"], None)
    measured = buffer_expiry_evidence.measure(
        record["direction"], {"price": record["entry_price"]},
        expiry if outcome != "UNKNOWN" else None, frozen,
    )
    buffer_status = {"MET": "DA", "NOT_MET": "NU", "UNAVAILABLE": "DATE INDISPONIBILE"}[measured["status"]]
    position = classify_buffer_position(record["direction"], record["entry_price"],
        record["buffer_price"], expiry.get("price") if outcome != "UNKNOWN" else None)
    result = "WIN fragil" if outcome == "WIN" and position == "INSIDE_BUFFER" else outcome
    quote = "indisponibilă"
    if outcome != "UNKNOWN":
        lag = expiry["observed_ts"] - expiry["target_ts"]
        quote = f"{expiry['price']:.15g} la {stamp(expiry['observed_ts'])} (+{lag:.3f} s)"
    return ("📊 OPEN NOW · REZULTAT DE PIAȚĂ V3\n"
            f"EUR/USD · {direction_label(record['direction'])}\n"
            f"Semnal: {number or 'număr indisponibil'}\n"
            f"Preț de referință: {record['entry_price']:.15g}\n"
            f"Expirare programată: {stamp(expiry['target_ts'])}\n"
            f"Prima cotație la sau după expirare: {quote}\n"
            f"Rezultat: {result}\n"
            f"Poziție la cotația observată: {BUFFER_POSITION_LABELS[position]}\n"
            f"Marjă completă la cotația observată: {buffer_status}\n"
            "Evaluare de piață a semnalului. Execuția la broker este neconfirmată.")


def dispatch():
    destination = owner.destination()
    if destination is None:
        return None
    now = time.time()
    selected = _reserve(destination, now)
    if selected is None:
        return None
    trade_id, record, report = selected
    expiry = record["checkpoints"]["expiry"]
    outcome = expiry["directional_result"] if expiry["state"] == "OBSERVED" else "UNKNOWN"
    receipt = {"status": "UNKNOWN", "attempted_ts": now, "format": "TEXT"}
    try:
        from core import owner_signal_number

        number = owner_signal_number.lookup(record["signal_id"])
        caption = _caption(record, expiry, outcome, number)
        try:
            photo = physical_study_chart.render_market_chart(direction=record["direction"],
                entry_ts=record["open_ts"], entry_price=record["entry_price"], expiry_ts=expiry["target_ts"],
                expiry_quote_ts=expiry["observed_ts"], expiry_price=expiry["price"],
                buffer_distance=record["buffer_price"], outcome=outcome, report_title=_TITLE,
                entry_label="PREȚ DE REFERINȚĂ", signal_label=number,
                expiry_observation_label="PRIMA COTAȚIE DE LA EXPIRARE")
        except Exception:
            photo = None  # preserve the textual result if rendering fails before any send
        if owner.destination() != destination:
            receipt["status"] = "SKIPPED_DESTINATION_CHANGED"
        else:
            if photo is None:
                response = telegram_publisher.send_message(chat_id=destination, text=caption + "\nGrafic indisponibil.",
                    reply_to_message_id=report["publication"]["message_id"])
            else:
                receipt["format"] = "PHOTO"
                response = telegram_publisher.send_photo(chat_id=destination, photo=photo, caption=caption,
                    reply_to_message_id=report["publication"]["message_id"])
            message_id = (response.get("result") or {}).get("message_id")
            if response.get("ok") is True and type(message_id) is int and message_id > 0:
                receipt.update(status="API_ACCEPTED", message_id=message_id, api_accepted_ts=time.time())
            elif response.get("ok") is False:
                receipt["status"] = "FAILED"
    except telegram_publisher.TelegramAPIError:
        receipt["status"] = "FAILED"
    except Exception:
        pass  # ambiguous acceptance must never be retried or followed by a text send

    with storage.with_lock("trade_temporal_telemetry", timeout_sec=0.2):
        registry = telemetry._load_registry()
        registry["owner_expiry_reports"][trade_id].update(receipt)
        telemetry._save_registry(registry)
    print("TSP_OWNER_OPEN_NOW_RESULT " + json.dumps({
        "status": receipt["status"], "outcome": outcome, "format": receipt["format"],
    }), flush=True)
    return receipt["status"]


def dispatch_async():
    destination = owner.destination()
    if destination is None or not _IN_FLIGHT.acquire(blocking=False):
        return None

    def run():
        try:
            dispatch()
        except Exception as exc:
            print("TSP_OWNER_OPEN_NOW_RESULT_UNAVAILABLE " + json.dumps({"error_class": type(exc).__name__}), flush=True)
        finally:
            _IN_FLIGHT.release()

    try:
        if _next_ready(telemetry._load_registry(), destination) is None:
            _IN_FLIGHT.release()
            return None
        thread = threading.Thread(target=run, name="owner-open-now-result", daemon=True)
        thread.start()
    except Exception:
        _IN_FLIGHT.release()
        raise
    return thread


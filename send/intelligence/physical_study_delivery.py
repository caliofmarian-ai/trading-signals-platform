"""Private prospective study notifications, outside canonical trade publication.

These are explicitly uncalibrated Model Time observations. They never build a
SignalEvent, approve an expiry artifact, count a canonical OPEN, or call a broker.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import time
import threading

from core import owner_signal_delivery as owner, owner_signal_number, storage, telegram_publisher
from core.buffer_zone import BUFFER_POSITION_LABELS, classify_buffer_position
from intelligence import buffer_expiry_evidence
from intelligence import physical_expiry_calibration as study
from intelligence.observation_issue_presentation import collection_issue_label
from core.signal_presentation import direction_label
from core import confirmed_study_duration as second_duration

STATUSES = {"RESERVED", "API_ACCEPTED", "FAILED", "UNKNOWN", "SKIPPED_STALE", "SKIPPED_STAGE_GUARD", "SKIPPED_DESTINATION_CHANGED", "SKIPPED_DURATION_INFEASIBLE"}
RESULT_PRESENTATION_CONTRACT = "EXPLICIT_PRICE_EVIDENCE_V1"
ESTIMATED_RESULT_PRESENTATION_CONTRACT = "EXPLICIT_PRICE_ESTIMATE_V2"
ESTIMATE_WAIT_CONTRACT = "MISSING_ESTIMATE_BOUNDED_WAIT_V1"
RECEIPT_JOURNAL_PROTOCOL = "PHYSICAL_STUDY_DELIVERY_RECEIPT_JOURNAL_V1"
RECEIPT_JOURNAL_MAX_RECORDS = 1024
RECEIPT_JOURNAL_MAX_BYTES = 1024 * 1024
RESERVATION_RECOVERY_GRACE_SECONDS = 300.0
RECONCILE_INTERVAL_SECONDS = 5.0
_last_reconciliation = {}
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
            if study.displayed_study_observation(row)["outcome"] == "INFEASIBLE":
                raise ValueError("INFEASIBLE_CONFIRMED_STUDY_PUBLICATION")
        if phase == "result" and receipt["status"] == "API_ACCEPTED":
            if (delivery.get("entry") or {}).get("status") != "API_ACCEPTED":
                raise ValueError("STUDY_RESULT_WITHOUT_ENTRY_RECEIPT")


def _stamp(value):
    observed = datetime.fromtimestamp(value, timezone.utc)
    stamp = observed.strftime("%H:%M:%S")
    if observed.microsecond:
        stamp += observed.strftime(".%f").rstrip("0")
    return stamp + " UTC"


def _entry_event(row):
    """Project the frozen study observation without creating an execution signal."""
    entry = row["entry"]
    observation = study.displayed_study_observation(row)
    event = {"stage": "OPEN_NOW", "symbol": "EUR/USD", "direction": row["direction"],
            "entry_price": entry["price"], "created_ts": row["created_ts"],
            "entry_ts": entry["observed_ts"],
            "expiry_ts": entry["observed_ts"] + observation["horizon_seconds"],
            "study_duration_minutes": observation["horizon_seconds"] / 60}
    if "study_observation" in row:
        event.update(study_confirmed_ts=observation["confirmed_ts"],
                     study_duration_source=observation["duration_source"])
    if "duration_policy" in observation:
        event.update(second_duration.event_fields(observation["duration_plan"]))
    return event


def render_entry(row, signal_label):
    from core.signal_card import render_signal_caption

    return render_signal_caption(_entry_event(row), signal_label, study=True)


def _render_entry_card(row, signal_label):
    from core.signal_card import render_signal_card

    return render_signal_card(_entry_event(row), signal_label, study=True)


def _result_evidence(row):
    """One bounded read-only projection for the caption and delivery evidence."""
    observation = study.displayed_study_observation(row)
    entry, expiry = row["entry"], observation["quote"]
    frozen = row.get("buffer_snapshot")
    distance = frozen.get("buffer_distance") if frozen else None
    measured = buffer_expiry_evidence.measure(row["direction"], entry, expiry, frozen)

    def source(quote):
        if quote is None:
            return None
        value = quote.get("source")
        return value if value in ("LIVE_STREAM_CURRENT_M1_CLOSE", "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1",
                                 "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1") else "UNSPECIFIED"

    reason = observation.get("reason")
    if reason not in (None, "OBSERVED_PAIRED_EXPIRY", "ENTRY_OBSERVATION_MISSING",
                       "EXPIRY_OBSERVATION_MISSING", "PROVIDER_CHANGED"):
        reason = "UNSPECIFIED"
    estimate = _expiry_estimate(row)
    return {"presentation_contract": (ESTIMATED_RESULT_PRESENTATION_CONTRACT if estimate is not None
                                       else RESULT_PRESENTATION_CONTRACT),
            "estimate_wait_contract": ESTIMATE_WAIT_CONTRACT,
            "direction": row["direction"], "study_outcome": observation["outcome"],
            "entry_price": entry["price"] if entry else None,
            "entry_observed_ts": entry["observed_ts"] if entry else None,
            "entry_quote_source": source(entry),
            "expiry_price": expiry["price"] if expiry else None,
            "expiry_quote_ts": expiry["observed_ts"] if expiry else None,
            "expiry_quote_source": source(expiry), "observation_reason": reason,
            "buffer_position": classify_buffer_position(row["direction"], entry["price"] if entry else None,
                distance, expiry["price"] if expiry else None),
            "buffer_full_margin_status": measured["status"],
            "expiry_price_estimate": deepcopy(estimate)}


def _expiry_estimate(row):
    """Keep adjacent-price context separate from genuine settlement evidence."""
    observation = study.displayed_study_observation(row)
    estimate = row.get("expiry_price_estimate")
    entry = row.get("entry")
    if (estimate is None or entry is None or observation.get("quote") is not None
            or observation.get("outcome") != "UNKNOWN"
            or observation.get("reason") != "EXPIRY_OBSERVATION_MISSING"):
        return None
    from intelligence.expiry_price_estimate import validate_estimate
    try:
        validate_estimate(estimate, direction=row["direction"], entry=entry,
                         expiry_ts=entry["observed_ts"] + observation["horizon_seconds"])
    except (TypeError, ValueError, KeyError):
        return None
    return estimate


def _render_estimated_result(row, signal_label, estimate):
    from core.signal_card import _duration

    observation = study.displayed_study_observation(row)
    entry = row["entry"]
    target = entry["observed_ts"] + observation["horizon_seconds"]
    labels = {"WIN": "WIN estimat", "LOSS": "LOSS estimat",
              "INCONCLUSIVE": "neconcludentă", "UNAVAILABLE": "indisponibilă"}

    def endpoint(name, quote):
        if quote is None:
            return f"{name}: LIPSĂ în limita de 60s"
        source = "arhivă" if quote["source"].startswith("DURABLE_") else "flux"
        return f"{name}: {quote['price']} · {_stamp(quote['observed_ts'])} · Finnhub {source}"

    lines = ["🧪 REZULTAT STUDIU V3", f"Estimare: {labels[estimate['estimated_outcome']]}",
             f"EUR/USD · {row['direction']} · {_duration(observation['horizon_seconds']/60, seconds=observation.get('duration_seconds'))}",
             f"Intrare: {entry['price']} · {_stamp(entry['observed_ts'])}",
             f"Expirare declarată: {_stamp(target)}",
             endpoint("Înainte", estimate["before"]), endpoint("După", estimate["after"])]
    if estimate["lower_price"] is not None:
        lines.append(f"Interval orientativ: {estimate['lower_price']} – {estimate['upper_price']}")
        lines.append(f"Gol între cotații: {estimate['gap_seconds']:g}s")
    else:
        lines.append("Interval orientativ: indisponibil fără ambele cotații.")
    delay = row.get("quote_recovery_policy", {}).get("expiry_window_seconds", study.quotes.MAX_SAMPLE_DELAY_SECONDS)
    lines.extend([f"Rezultat: {collection_issue_label(observation['reason'])}",
                  f"Fereastră verificată: {_stamp(target)} – {_stamp(target + delay)}",
                  "Prețul dintre observații poate ieși din interval.",
                  "Estimarea nu intră în rata WIN verificată.",
                  f"{signal_label} · Dublin" if signal_label else "Număr indisponibil"])
    caption = "\n".join(lines)
    # Dispatch falls back to text when unusual numeric widths exceed the
    # photo-caption budget; every evidence field and qualifier is preserved.
    return caption


def render_result(identity, row, signal_label):
    from core.signal_card import _duration

    baseline = study.displayed_study_observation(row)
    entry = row["entry"]
    expiry_quote = baseline["quote"]
    evidence = _result_evidence(row)
    if evidence["expiry_price_estimate"] is not None:
        return _render_estimated_result(row, signal_label, evidence["expiry_price_estimate"])
    direction, outcome = evidence["direction"], evidence["study_outcome"]
    frozen = row.get("buffer_snapshot")
    distance = frozen.get("buffer_distance") if frozen else None
    label = {"MET": "DA", "NOT_MET": "NU", "UNAVAILABLE": "DATE INDISPONIBILE"}[evidence["buffer_full_margin_status"]]
    position = evidence["buffer_position"]
    result = collection_issue_label(evidence["observation_reason"]) if outcome == "UNKNOWN" else outcome
    expiry_ts = entry["observed_ts"] + baseline["horizon_seconds"] if entry else None

    def price(value):
        # Shortest round-trip form keeps distinct source prices visibly distinct.
        return str(value)

    def observation(name, quote):
        if quote is None:
            return f"{name}: LIPSĂ"
        return f"{name} colectată: {price(quote['price'])} · {_stamp(quote['observed_ts'])}"

    def source(value):
        if value is None:
            return "lipsă"
        return {
            "LIVE_STREAM_CURRENT_M1_CLOSE": "Finnhub flux",
            "LIVE_STREAM_PROVIDER_TICK_BUFFER_V1": "Finnhub memorie",
            "DURABLE_STREAM_PROVIDER_TICK_BUFFER_V1": "Finnhub arhivă",
        }.get(value, "sursă nedetaliată")

    lines = ["🧪 REZULTAT STUDIU V3", f"Rezultat: {result}",
             f"EUR/USD · {direction} · {_duration(baseline['horizon_seconds']/60, seconds=baseline.get('duration_seconds'))}",
             observation("Intrare", entry),
             f"Expirare declarată: {_stamp(expiry_ts) if expiry_ts is not None else 'nedeterminată fără intrare'}",
             observation("Cotație expirare", expiry_quote)]
    if entry is not None and expiry_quote is not None:
        relation = ">" if expiry_quote["price"] > entry["price"] else "<" if expiry_quote["price"] < entry["price"] else "="
        lines.append(f"Comparație {direction}: {price(expiry_quote['price'])} {relation} {price(entry['price'])} → {outcome}")
    else:
        lines.append("Comparație: indisponibilă; prețuri incomplete.")
    lines.append(f"Surse intrare/expirare: {source(evidence['entry_quote_source'])} / {source(evidence['expiry_quote_source'])}")
    if outcome == "UNKNOWN":
        if expiry_ts is not None:
            # Show the frozen source-time window, never the later arrival grace.
            delay = row.get("quote_recovery_policy", {}).get("expiry_window_seconds", study.quotes.MAX_SAMPLE_DELAY_SECONDS)
            lines.append(f"Interval expirare: {_stamp(expiry_ts)} – {_stamp(expiry_ts + delay)}")
        elif row.get("created_ts") is not None:
            delay = row.get("quote_recovery_policy", {}).get("entry_window_seconds", study.quotes.MAX_ENTRY_DELAY_SECONDS)
            lines.append(f"Interval intrare: {_stamp(row['created_ts'])} – {_stamp(row['created_ts'] + delay)}")
    limit = "LIPSĂ"
    if entry is not None and distance is not None:
        with localcontext() as context:
            context.prec = 1100
            edge = Decimal(str(entry["price"])) + (1 if direction == "BUY" else -1) * Decimal(str(distance))
            exact_limit = str(edge)
            # Keep a short exact boundary distinct from a nearby actual quote.
            # Very long computed references are bounded and visibly approximate.
            limit = exact_limit if len(exact_limit) <= 22 else f"~{format(edge, '.17g')} (aprox.)"
    lines.extend([f"Poziție buffer: {BUFFER_POSITION_LABELS[position]}",
                  f"Limită buffer: {limit}", f"Marjă completă la expirare: {label}",
                  "Studiu pe cotații observate.",
                  f"{signal_label} · Dublin" if signal_label else "Număr indisponibil"])
    caption = "\n".join(lines)
    # Conservatively count UTF-16 units, including emoji and the full lifecycle
    # label; never send a caption that Telegram would reject or silently trim.
    if len(caption.encode("utf-16-le")) // 2 > 1024:
        raise ValueError("STUDY_RESULT_CAPTION_TOO_LONG")
    return caption


def _render_chart(row, signal_label):
    from intelligence.physical_study_chart import render_market_chart

    entry = row["entry"]
    baseline = study.displayed_study_observation(row)
    expiry_ts = entry["observed_ts"] + baseline["horizon_seconds"]
    quote = baseline["quote"] or {}
    return render_market_chart(direction=row["direction"], entry_ts=entry["observed_ts"],
                               entry_price=entry["price"], expiry_ts=expiry_ts,
                               expiry_quote_ts=quote.get("observed_ts"), expiry_price=quote.get("price"),
                               buffer_distance=row["buffer_snapshot"]["buffer_distance"],
                               outcome=baseline["outcome"], signal_label=signal_label,
                               observation_reason=baseline.get("reason"),
                               expiry_estimate=_expiry_estimate(row))



def _receipt_journal_path(path):
    # study._path and _delivery_paths use pathlib.Path in the canonical store.
    path = str(path) if path is not None else ""
    if not path:
        raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL_PATH")
    stem = path[:-5] if path.endswith(".json") else path
    return stem + ".delivery_receipts.json"


def _receipt_journal_key(identity, phase):
    if (not isinstance(identity, str) or not identity
        or phase not in {"entry", "result"}):
        raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL_KEY")
    return f"{identity}:{phase}"


def _read_receipt_journal(path):
    journal_path = _receipt_journal_path(path)
    try:
        with open(journal_path, "rb") as handle:
            raw = handle.read(RECEIPT_JOURNAL_MAX_BYTES + 1)
    except FileNotFoundError:
        return {"protocol": RECEIPT_JOURNAL_PROTOCOL, "records": {}}
    if len(raw) > RECEIPT_JOURNAL_MAX_BYTES:
        raise ValueError("STUDY_RECEIPT_JOURNAL_SIZE_LIMIT")
    state = json.loads(raw.decode("utf-8"),
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_STUDY_RECEIPT_JOURNAL")))
    if (not isinstance(state, dict) or state.get("protocol") != RECEIPT_JOURNAL_PROTOCOL
        or not isinstance(state.get("records"), dict)
        or len(state["records"]) > RECEIPT_JOURNAL_MAX_RECORDS):
        raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL")
    for key, record in state["records"].items():
        if not isinstance(record, dict) or record.get("phase") not in {"entry", "result"}:
            raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL_RECORD")
        identity = record.get("study_id")
        receipt = record.get("receipt")
        attempted = study._number(record.get("attempted_ts"))
        if (key != _receipt_journal_key(identity, record["phase"])
            or not isinstance(receipt, dict) or receipt.get("status") not in STATUSES - {"RESERVED"}
            or study._number(receipt.get("attempted_ts")) != attempted):
            raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL_RECEIPT")
        study._number(record.get("written_ts"))
    return state


def _write_receipt_journal(path, identity, phase, receipt):
    if (not isinstance(receipt, dict) or receipt.get("status") not in STATUSES - {"RESERVED"}
        or study._number(receipt.get("attempted_ts")) is None):
        raise ValueError("INVALID_STUDY_RECEIPT_JOURNAL_WRITE")
    key = _receipt_journal_key(identity, phase)
    journal_path = _receipt_journal_path(path)
    record = {"study_id": identity, "phase": phase,
              "attempted_ts": receipt["attempted_ts"],
              "receipt": deepcopy(receipt), "written_ts": time.time()}
    with storage.with_lock("physical_v3_study_delivery_receipts", timeout_sec=.2):
        state = _read_receipt_journal(path)
        existing = state["records"].get(key)
        if existing is not None and existing.get("attempted_ts") != record["attempted_ts"]:
            raise ValueError("STUDY_RECEIPT_JOURNAL_COLLISION")
        state["records"][key] = record
        if len(state["records"]) > RECEIPT_JOURNAL_MAX_RECORDS:
            raise ValueError("STUDY_RECEIPT_JOURNAL_RECORD_LIMIT")
        storage.save_json_atomic(journal_path, state)
    return True


def _forget_receipt_journal(path, identity, phase, attempted_ts):
    key = _receipt_journal_key(identity, phase)
    journal_path = _receipt_journal_path(path)
    with storage.with_lock("physical_v3_study_delivery_receipts", timeout_sec=.2):
        state = _read_receipt_journal(path)
        record = state["records"].get(key)
        if record is None or record.get("attempted_ts") != attempted_ts:
            return False
        del state["records"][key]
        storage.save_json_atomic(journal_path, state)
    return True


def _reconcile_receipts(path, now, *, force=False):
    now = study._number(now)
    last = _last_reconciliation.get(path)
    empty = {"recovered_receipts": 0, "orphaned_reservations": 0,
             "orphaned_by_phase": {"entry": 0, "result": 0},
             "unresolved_reservations": 0, "journal_available": True}
    if not force and last is not None and now - last < RECONCILE_INTERVAL_SECONDS:
        return {**empty, "throttled": True}
    _last_reconciliation[path] = now
    journal_path = _receipt_journal_path(path)
    journal_error = None
    try:
        # Lock order is always receipt-journal then study-ledger. The sender
        # never acquires these in reverse order.
        with storage.with_lock("physical_v3_study_delivery_receipts", timeout_sec=.2):
            try:
                journal = _read_receipt_journal(path)
            except Exception as exc:
                journal = {"protocol": RECEIPT_JOURNAL_PROTOCOL, "records": {}}
                journal_error = type(exc).__name__
            with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=.2):
                state = study._read(path)
                if state is None:
                    return empty
                changed = False
                result = dict(empty)
                for identity, row in state["records"].items():
                    delivery = row.get("study_delivery")
                    if not isinstance(delivery, dict):
                        continue
                    for phase in ("entry", "result"):
                        current = delivery.get(phase)
                        if not isinstance(current, dict) or current.get("status") != "RESERVED":
                            continue
                        attempted = study._number(current.get("attempted_ts"))
                        record = None if journal_error else journal["records"].get(
                            _receipt_journal_key(identity, phase))
                        if (record is not None and record.get("attempted_ts") == attempted):
                            recovered = deepcopy(record["receipt"])
                            recovered["recovered_from_journal"] = True
                            recovered["recovered_ts"] = now
                            delivery[phase] = recovered
                            result["recovered_receipts"] += 1
                            changed = True
                        elif now >= attempted and now - attempted >= RESERVATION_RECOVERY_GRACE_SECONDS:
                            current.update(status="UNKNOWN",
                                resolution_reason="ORPHANED_RESERVATION_RECEIPT_UNAVAILABLE",
                                resolved_ts=now, no_retry=True)
                            result["orphaned_reservations"] += 1
                            result["orphaned_by_phase"][phase] += 1
                            changed = True
                        else:
                            result["unresolved_reservations"] += 1
                if changed:
                    study._save(path, state)
                if journal_error is None:
                    pruned = False
                    for key, record in list(journal["records"].items()):
                        row = state["records"].get(record["study_id"])
                        current = ((row.get("study_delivery") or {}).get(record["phase"])
                                   if row is not None else None)
                        if not isinstance(current, dict) or current.get("status") != "RESERVED":
                            del journal["records"][key]
                            pruned = True
                    if pruned:
                        try:
                            storage.save_json_atomic(journal_path, journal)
                        except Exception:
                            pass
                result["journal_available"] = journal_error is None
                if journal_error is not None:
                    result["journal_error_class"] = journal_error
    except Exception as exc:
        result = {**empty, "unavailable": True, "error_class": type(exc).__name__}
        print("TSP_PHYSICAL_STUDY_DELIVERY_RECONCILIATION_UNAVAILABLE " + json.dumps({
            "error_class": type(exc).__name__, "broker_executed": False,
            "execution_authority": False,
        }, sort_keys=True), flush=True)
        return result
    if (result["recovered_receipts"] or result["orphaned_reservations"]
        or journal_error is not None):
        print("TSP_PHYSICAL_STUDY_DELIVERY_RECONCILIATION " + json.dumps({
            "protocol": RECEIPT_JOURNAL_PROTOCOL,
            "recovered_receipts": result["recovered_receipts"],
            "orphaned_reservations": result["orphaned_reservations"],
            "orphaned_by_phase": result["orphaned_by_phase"],
            "unresolved_reservations": result["unresolved_reservations"],
            "journal_available": result["journal_available"],
            "error_class": journal_error,
            "no_retry_ambiguous": True,
            "broker_executed": False,
            "execution_authority": False,
        }, sort_keys=True), flush=True)
    return result


def _commit_receipt(path, identity, phase, receipt):
    for attempt in range(2):
        try:
            with storage.with_lock("physical_v3_expiry_calibration", timeout_sec=.2):
                state = study._read(path)
                if state is None:
                    return False
                row = state["records"].get(identity)
                current = ((row.get("study_delivery") or {}).get(phase)
                           if row is not None else None)
                if (not isinstance(current, dict) or current.get("status") != "RESERVED"
                    or current.get("attempted_ts") != receipt.get("attempted_ts")):
                    return False
                row["study_delivery"][phase] = deepcopy(receipt)
                study._save(path, state)
            return True
        except TimeoutError:
            if attempt == 1:
                raise
    return False


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
                elif study.displayed_study_observation(row)["outcome"] == "INFEASIBLE":
                    status = "SKIPPED_DURATION_INFEASIBLE"
                else:
                    context = row["policies"]["PHYSICAL_ONLY_V3"]
                    event = {"stage": "OPEN_NOW", "signal_id": context["opportunity_signal_id"]}
                    if "study_observation" in row:
                        event.update({key: value for key, value in _entry_event(row).items()
                                      if key.startswith("study_")})
                    reason = owner.stage_block_reason(event, now_ts=row["created_ts"])
                    if reason is not None:
                        status = "SKIPPED_STAGE_GUARD"
            elif ((delivery.get("entry") or {}).get("status") != "API_ACCEPTED"
                  or study.displayed_study_observation(row)["outcome"] in {"PENDING", "INFEASIBLE"}):
                continue
            elif delivery["entry"].get("destination_id", destination) != destination:
                status = "SKIPPED_DESTINATION_CHANGED"
            elif phase == "result":
                target = study._estimate_target(row)
                if target is not None:
                    estimate = _expiry_estimate(row)
                    from intelligence.expiry_price_estimate import MAX_SIDE_SECONDS
                    deadline = target + MAX_SIDE_SECONDS + study.EXPIRY_ESTIMATE_ARRIVAL_GRACE_SECONDS
                    if now < deadline and (estimate is None or estimate["estimated_outcome"] == "UNAVAILABLE"):
                        # No metadata may mean a failed/deferred lookup, not an
                        # observed absence of neighbors. Reconstruct the wait
                        # from the frozen expiry, including after restart.
                        # Do not reserve a message until a valid complete pair
                        # (also inconclusive) or the original bounded deadline.
                        # This never postpones exact settlement or other results.
                        continue
            delivery[phase] = {"status": status, "attempted_ts": now}
            if status == "RESERVED":
                delivery[phase]["destination_id"] = destination
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
    paths = study._delivery_paths(path)
    for ledger_path in paths:
        _reconcile_receipts(ledger_path, now_ts)
    for phase in ("entry", "result"):
        for path in paths:
            reserved = _reserve(path, phase, now_ts, destination)
            if reserved is not None:
                break
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
                    from core.signal_card import render_signal_text
                    text = render_signal_text(_entry_event(row), signal_label, study=True)
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
            if photo is not None and len(text.encode("utf-16-le")) // 2 > 1024:
                photo = None  # Full evidence remains available in the text result.
            # Reservation precedes rendering, which can outlast the entry window.
            if phase == "entry" and time.time() - row["created_ts"] > study.quotes.MAX_ENTRY_DELAY_SECONDS:
                receipt["status"] = "SKIPPED_STALE"
            else:
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
        journal_persisted = False
        try:
            journal_persisted = _write_receipt_journal(path, identity, phase, receipt)
        except Exception as exc:
            print("TSP_PHYSICAL_STUDY_DELIVERY_RECEIPT_JOURNAL_UNAVAILABLE " + json.dumps({
                "error_class": type(exc).__name__, "broker_executed": False,
                "execution_authority": False,
            }, sort_keys=True), flush=True)
        receipt_commit_persisted = False
        try:
            receipt_commit_persisted = _commit_receipt(path, identity, phase, receipt)
        except Exception as exc:
            print("TSP_PHYSICAL_STUDY_DELIVERY_RECEIPT_COMMIT_UNAVAILABLE " + json.dumps({
                "error_class": type(exc).__name__, "broker_executed": False,
                "execution_authority": False,
                "journal_persisted": journal_persisted,
            }, sort_keys=True), flush=True)
        if receipt_commit_persisted:
            try:
                _forget_receipt_journal(path, identity, phase, receipt["attempted_ts"])
            except Exception as exc:
                print("TSP_PHYSICAL_STUDY_DELIVERY_RECEIPT_JOURNAL_CLEANUP_UNAVAILABLE " + json.dumps({
                    "error_class": type(exc).__name__, "broker_executed": False,
                    "execution_authority": False,
                }, sort_keys=True), flush=True)
        observation = study.displayed_study_observation(row)
        expiry_quote = observation.get("quote") or {}
        print("TSP_PHYSICAL_STUDY_DELIVERY " + json.dumps({
            "phase": phase, "status": receipt["status"], "study_id": identity,
            "format": receipt["format"], "signal_label": signal_label,
            "observed_at": now_ts, "truth_domain": "HYPOTHETICAL_RESEARCH",
            "study_duration_seconds": study.displayed_study_observation(row)["horizon_seconds"],
            "study_duration_source": study.displayed_study_observation(row).get("duration_source", "LEGACY_OPEN_MODEL_TIME"),
            "study_confirmed_ts": study.displayed_study_observation(row).get("confirmed_ts"),
            "study_duration_policy": second_duration.observation_policy(row),
            "study_plan_id": (observation.get("duration_plan") or {}).get("plan_id"),
            "study_outcome": observation["outcome"] if phase == "result" else None,
            "expiry_quote_ts": expiry_quote.get("observed_ts") if phase == "result" else None,
            "expiry_price": expiry_quote.get("price") if phase == "result" else None,
            "entry_observed_ts": row["entry"]["observed_ts"],
            "expiry_ts": row["entry"]["observed_ts"] + study.displayed_study_observation(row)["horizon_seconds"],
            "execution_calibration_proven": False, "broker_executed": False,
            "receipt_journal_persisted": journal_persisted,
            "receipt_commit_persisted": receipt_commit_persisted,
            **(_result_evidence(row) if phase == "result" else {}),
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


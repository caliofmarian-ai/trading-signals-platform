"""Human-readable V3 signal projection; no strategy or expiry computation."""
from datetime import datetime, timezone
from math import isfinite


def _number(value):
    return float(value) if type(value) in (int, float) and isfinite(value) and value > 0 else None


def stamp(value):
    number = _number(value)
    if number is None or number >= 253402300800:
        return "indisponibilă"
    return datetime.fromtimestamp(number, timezone.utc).strftime("%H:%M:%S UTC")


def direction_label(direction):
    return {"BUY": "↑ CREȘTERE · BUY / CALL", "SELL": "↓ SCĂDERE · SELL / PUT"}.get(direction, "Direcție indisponibilă")


def _price(value):
    number = _number(value)
    return format(number, ".15g") if number is not None else "indisponibil"


def render_physical_signal(event, tier_label=""):
    stage = event["stage"]
    title, meaning = {
        "PRE": ("🟡 PRE · URMĂREȘTE", "Urmărește simbolul. Așteaptă OPEN_NOW; oportunitatea poate fi anulată."),
        "CONFIRM": ("🔵 CONFIRM · PREGĂTEȘTE-TE", "Condițiile au fost reconfirmate. Așteaptă OPEN_NOW pentru intrare."),
        "OPEN_NOW": ("🟢 OPEN_NOW · INTRARE", "Folosește numai durata validată afișată; condițiile se pot schimba."),
    }[stage]
    lines = [title, f"{event['symbol']} · {direction_label(event['direction'])}",
             f"Analiză: {event['timeframe']} · Emis: {stamp(event.get('created_ts'))}",
             f"Preț de referință: {_price(event.get('entry_price'))}"]
    buffer = _number(event.get("buffer_distance"))
    if buffer is not None:
        lines.append(f"Buffer: {buffer:.15g} unități de preț · {event.get('buffer_mode')}")
        side = "deasupra" if event["direction"] == "BUY" else "dedesubtul"
        lines.append(f"Buffer = banda imediat {side} prețului de intrare; nu garantează rezultatul.")
        lines.append("Închiderea în interiorul benzii: câștig fragil.")
    if stage == "OPEN_NOW":
        duration = _number(event.get("open_now_expiry_minutes"))
        if not event.get("execution_time_available") or duration is None:
            raise ValueError("OPEN_NOW_REQUIRES_VALIDATED_EXECUTION_TIME")
        lines.append(f"Expirare validată: {duration:.15g} min de la intrarea efectivă")
    elif stage == "CONFIRM":
        minimum = _number(event.get("confirm_expiry_min_minutes"))
        maximum = _number(event.get("confirm_expiry_max_minutes"))
        if event.get("execution_time_available") and minimum is not None and maximum is not None:
            lines.append(f"Interval de expirare validat: {minimum:.15g}–{maximum:.15g} min")
        else:
            lines.append("Expirare de execuție: indisponibilă · calibrare în colectare")
    lines.extend([meaning, f"ID: {event['signal_id']}"])
    if tier_label and tier_label not in {"PERSONAL", "ADMIN"}:
        lines.append(f"Canal: {tier_label}")
    return "\n".join(lines)


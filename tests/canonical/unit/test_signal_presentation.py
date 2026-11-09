import pytest
from core.signal_presentation import render_physical_signal


def _event(stage):
    return {"stage":stage,"signal_id":"sig-v3-example","symbol":"EUR/USD","direction":"BUY",
            "timeframe":"M1","created_ts":1_800_000_000,"entry_price":1.1002,
            "buffer_distance":0.00008,"buffer_mode":"MEDIUM","execution_time_available":False,
            "model_expiry":12,"payload":{"decision_policy":"PHYSICAL_ONLY_V3"}}


def test_pre_and_confirm_are_clear_without_invented_expiry_or_score():
    pre, confirm = (render_physical_signal(_event(stage)) for stage in ("PRE","CONFIRM"))
    assert "URMĂREȘTE" in pre and "așteaptă open_now" in pre.lower()
    assert "PREGĂTEȘTE-TE" in confirm and "indisponibilă" in confirm
    for text in (pre,confirm):
        assert "BUY / CALL" in text and "UTC" in text and "1.1002" in text
        assert "unități de preț" in text and "nu garantează" in text
        assert not any(term in text for term in ("Score","TPS","12 min","80%"))


def test_open_requires_exact_execution_duration_and_does_not_use_model_time():
    event = _event("OPEN_NOW")
    with pytest.raises(ValueError):
        render_physical_signal(event)
    event.update(execution_time_available=True,open_now_expiry_minutes=2.375)
    text = render_physical_signal(event)
    assert "2.375 min de la intrarea efectivă" in text and "12 min" not in text


def test_actual_v3_router_uses_physical_projection():
    from core.distribution_router_v3 import _render_signal_text
    text = _render_signal_text(_event("PRE"),"BASIC")
    assert "URMĂREȘTE" in text and "Canal: BASIC" in text


@pytest.mark.parametrize(("direction", "side"), [("BUY", "deasupra"), ("SELL", "dedesubtul")])
def test_buffer_definition_is_adjacent_to_entry_in_the_favorable_direction(direction, side):
    event = _event("PRE")
    event["direction"] = direction
    text = render_physical_signal(event)
    assert f"banda imediat {side} prețului de intrare" in text
    assert "Închiderea în interiorul benzii: câștig fragil" in text

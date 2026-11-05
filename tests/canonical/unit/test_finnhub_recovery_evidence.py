"""Offline socket sessions; none of these fixtures are real market evidence."""

from __future__ import annotations

import importlib
import json

import pytest
from websocket import ABNF


class _ControlSocket:
    def settimeout(self, seconds):
        assert 0 < seconds <= 5

    def recv_data(self, control_frame=False):
        assert control_frame
        return ABNF.OPCODE_TEXT, self.recv()


def trade(timestamp_ms, *, symbol="OANDA:EUR_USD"):
    return {"type": "trade", "data": [{"s": symbol, "p": 1.12, "t": timestamp_ms, "v": 0}]}


def events(capsys):
    return [json.loads(line.split(" ", 1)[1]) for line in capsys.readouterr().out.splitlines()
            if line.startswith("TSP_FINNHUB_STREAM_EVIDENCE ")]


def test_first_batch_with_multiple_ticks_has_one_first_tick_event(tmp_path, capsys):
    module = importlib.import_module("runtime.finnhub_market_data")
    feed = module.FinnhubForexFeed(token="PRIVATE", store_path=tmp_path / "prices.json",
                                  clock=lambda: 1793812202)
    batch = trade(1793812200000)
    batch["data"].append(trade(1793812201000)["data"][0])
    feed.ingest_message(batch)
    feed.ingest_message(trade(1793812202000))
    records = events(capsys)
    assert [row["event"] for row in records] == ["FIRST_REAL_TICK"]
    assert records[0]["valid_trade_tick_count"] == 2
    assert records[0]["observed_at"] == 1793812202
    assert records[0]["price_age_seconds"] == 1
    assert records[0]["freshness_limit_seconds"] == feed.freshness_seconds


@pytest.mark.parametrize("intermediate", [
    {"type": "ping"},
    trade(1793812201000, symbol="OTHER"),
    trade(1793812200000),  # equal previous timestamp
    trade(1793812199000),  # older than the previous tick
    trade(1793812201000),  # newer but 29 seconds stale
    trade(1793812231000),  # future relative to the frozen receive clock
])
def test_reconnect_waits_for_a_new_fresh_quote(tmp_path, capsys, intermediate):
    module = importlib.import_module("runtime.finnhub_market_data")
    clock = [1793812200]
    checks = []

    class Socket(_ControlSocket):
        def __init__(self, session):
            self.session, self.receives, self.closed = session, 0, False

        def send(self, message):
            assert json.loads(message)["symbol"] == "OANDA:EUR_USD"

        def recv(self):
            self.receives += 1
            if self.session == 0:
                if self.receives == 1:
                    return trade(1793812200000)
                raise ConnectionError("test disconnect with PRIVATE in message")
            if self.receives == 1:
                clock[0] = 1793812230
                return intermediate
            if self.receives == 2:
                checks.extend(row["event"] for row in events(capsys))
                # Also move beyond the future-frame fixture before recovery.
                clock[0] = 1793812232
                return trade(1793812232000)
            feed._stop_event.set()
            return {"type": "ping"}

        def close(self):
            self.closed = True

    sockets = []

    def connect(*args, **kwargs):
        socket = Socket(len(sockets))
        sockets.append(socket)
        return socket

    feed = module.FinnhubForexFeed(token="PRIVATE", store_path=tmp_path / "prices.json",
                                  clock=lambda: clock[0], websocket_connector=connect)
    feed._stop_event.wait = lambda seconds: False
    feed._stream_forever()
    records = events(capsys)
    recovered = [row for row in records if row["event"] == "REAL_TICK_RESUMED"]
    assert "REAL_TICK_RESUMED" not in checks
    assert len(sockets) == 2 and all(socket.closed for socket in sockets)
    assert len(recovered) == 1
    row = recovered[0]
    assert row["last_real_tick_ts"] == row["observed_at"] == 1793812232
    assert row["price_age_seconds"] == 0
    assert row["connection_attempts"] == 2
    assert row["failure_count"] == 1
    assert row["failure_class"] is None
    assert row["stream_state"] == "RECEIVING_REAL_TICKS"
    assert row["subscription_state"] == "REAL_TICK_CONFIRMED"
    assert row["usable_real_history_and_fresh_tick"] is False  # history still insufficient
    assert "PRIVATE" not in json.dumps(records)
    assert not {"price", "open", "close", "high", "low", "token"} & row.keys()


def test_each_recovery_is_visible_inside_five_minutes_but_not_each_tick(tmp_path, capsys):
    module = importlib.import_module("runtime.finnhub_market_data")
    clock = [1793812200]
    attempts = []

    class Socket(_ControlSocket):
        def __init__(self, session):
            self.session, self.reads = session, 0

        def send(self, message):
            pass

        def recv(self):
            self.reads += 1
            clock[0] += 1
            if self.reads <= 2:
                return trade(clock[0] * 1000)
            if self.session < 2:
                raise ConnectionError("offline disconnect")
            feed._stop_event.set()
            return {"type": "ping"}

        def close(self):
            pass

    def connect(*args, **kwargs):
        socket = Socket(len(attempts))
        attempts.append(socket)
        return socket

    feed = module.FinnhubForexFeed(token="PRIVATE", store_path=tmp_path / "prices.json",
                                  clock=lambda: clock[0], websocket_connector=connect)
    feed._stop_event.wait = lambda seconds: False
    feed._stream_forever()
    rows = events(capsys)
    assert [row["connection_attempts"] for row in rows
            if row["event"] == "REAL_TICK_RESUMED"] == [2, 3]
    assert len([row for row in rows if row["event"] == "FIRST_REAL_TICK"]) == 1
    assert feed.health()["valid_trade_tick_count"] == 6

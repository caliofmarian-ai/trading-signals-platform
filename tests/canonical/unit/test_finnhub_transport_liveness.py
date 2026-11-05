"""OFFLINE transport regressions; fixtures never count as market observations."""

from __future__ import annotations

import importlib
import json

import pytest
from websocket import ABNF, WebSocketTimeoutException


BASE = 1793839000


def trade(ts):
    return json.dumps({"type": "trade", "data": [
        {"s": "OANDA:EUR_USD", "p": 1.12, "t": int(ts * 1000), "v": 0}
    ]})


class ScriptedSocket:
    def __init__(self, steps, elapsed):
        self.steps = iter(steps)
        self.elapsed = elapsed
        self.sent = []
        self.pings = []
        self.closed = False
        self.timeout = None
        self.feed = None
        self.ping_error = None

    def settimeout(self, seconds):
        self.timeout = seconds

    def send(self, message):
        self.sent.append(json.loads(message))

    def ping(self, payload):
        if self.ping_error:
            raise self.ping_error
        self.pings.append(payload)

    def recv_data(self, control_frame=False):
        assert control_frame
        try:
            delta, item = next(self.steps)
        except StopIteration:
            self.feed._stop_event.set()
            return ABNF.OPCODE_TEXT, b'{"type":"ping"}'
        self.elapsed[0] += delta
        if isinstance(item, Exception):
            raise item
        return item(self) if callable(item) else item

    def recv(self):
        # The pre-fix receiver uses this and disconnects on the first idle read.
        return self.recv_data(control_frame=True)[1]

    def close(self):
        self.closed = True


def idle(count=4):
    return [(5, WebSocketTimeoutException("PRIVATE idle socket"))
            for _ in range(count)]


def pong(socket):
    return ABNF.OPCODE_PONG, socket.pings[-1]


def make_feed(tmp_path, steps):
    module = importlib.import_module("runtime.finnhub_market_data")
    elapsed = [0]
    socket = ScriptedSocket(steps, elapsed)
    feed = module.FinnhubForexFeed(
        token="PRIVATE", store_path=tmp_path / "market.json",
        clock=lambda: BASE + elapsed[0],
        websocket_connector=lambda *args, **kwargs: socket,
    )
    feed._transport_clock = lambda: elapsed[0]
    feed._stop_event.wait = lambda _seconds: True
    socket.feed = feed
    return feed, socket, elapsed


def test_quiet_responsive_connection_survives_idle_reads(tmp_path, capsys):
    feed, socket, _ = make_feed(tmp_path, idle() + [(0, pong)] + idle() + [(0, pong)])
    feed._stream_forever()
    health = feed.health()
    assert health["stream_connection_attempts"] == 1
    assert health["stream_failure_count"] == 0
    assert socket.sent == [{"type": "subscribe", "symbol": "OANDA:EUR_USD"}]
    assert len(socket.pings) == len(set(socket.pings)) == 2
    assert socket.timeout == 5
    assert socket.closed
    assert health["transport_idle_read_count"] == 8
    assert health["transport_pong_count"] == 2
    assert health["valid_trade_tick_count"] == 0
    assert health["fresh"] is False
    assert health["history_ready"] is False
    assert health["subscription_state"] == "SENT_UNVERIFIED"
    output = capsys.readouterr().out
    assert "TRANSPORT_PONG_CONFIRMED" in output
    assert "FIRST_REAL_TICK" not in output
    assert "REAL_TICK_RESUMED" not in output
    assert "PRIVATE" not in output


def test_missing_pong_fails_at_bounded_deadline(tmp_path):
    feed, socket, elapsed = make_feed(tmp_path, idle(6))
    feed._stream_forever()
    health = feed.health()
    assert elapsed[0] == 30
    assert len(socket.pings) == 1
    assert health["transport_pong_count"] == 0
    assert health["stream_failure_count"] == 1
    assert health["stream_last_failure_class"] == "PING_RESPONSE_TIMEOUT"
    assert health["stream_state"] == "DISCONNECTED_RETRYING"
    assert socket.closed


@pytest.mark.parametrize("reply", [
    (0, (ABNF.OPCODE_PONG, b"not-the-current-ping")),
    (11, pong),
])
def test_wrong_or_late_pong_does_not_confirm_transport(tmp_path, reply):
    feed, _, _ = make_feed(tmp_path, idle() + [reply] + idle(2))
    feed._stream_forever()
    health = feed.health()
    assert health["transport_pong_count"] == 0
    assert health["stream_last_failure_class"] == "PING_RESPONSE_TIMEOUT"


@pytest.mark.parametrize("kind", ["quote", "peer_ping", "json_ping"])
def test_other_messages_do_not_replace_matching_pong(tmp_path, kind):
    def frame(socket):
        if kind == "quote":
            return ABNF.OPCODE_TEXT, trade(BASE + socket.elapsed[0])
        if kind == "peer_ping":
            return ABNF.OPCODE_PING, b"peer-ping"
        return ABNF.OPCODE_TEXT, b'{"type":"ping"}'

    feed, _, _ = make_feed(tmp_path, idle() + [(5, frame)] + idle(1))
    feed._stream_forever()
    health = feed.health()
    assert health["valid_trade_tick_count"] == (1 if kind == "quote" else 0)
    assert health["transport_pong_count"] == 0
    assert health["stream_last_failure_class"] == "PING_RESPONSE_TIMEOUT"


def test_ping_send_failure_reconnects_without_leaking_secret(tmp_path, capsys):
    feed, socket, _ = make_feed(tmp_path, idle())
    socket.ping_error = BrokenPipeError("PRIVATE key in a transport exception")
    feed._stream_forever()
    assert feed.health()["stream_last_failure_class"] == "BrokenPipeError"
    assert feed.health()["stream_failure_count"] == 1
    assert socket.closed
    assert "PRIVATE" not in capsys.readouterr().out


def test_new_quote_after_idle_stays_on_the_same_subscription(tmp_path):
    def quote(socket):
        return ABNF.OPCODE_TEXT, trade(BASE + socket.elapsed[0])

    feed, socket, _ = make_feed(tmp_path, idle() + [(0, pong), (1, quote)])
    feed._stream_forever()
    health = feed.health()
    assert health["stream_connection_attempts"] == 1
    assert health["stream_failure_count"] == 0
    assert health["subscription_state"] == "REAL_TICK_CONFIRMED"
    assert health["valid_trade_tick_count"] == 1
    assert health["fresh"] is True
    assert health["history_ready"] is False
    assert len(socket.sent) == 1


def test_protocol_close_reconnects(tmp_path):
    feed, socket, _ = make_feed(tmp_path, [(0, (ABNF.OPCODE_CLOSE, b"\x03\xe8"))])
    feed._stream_forever()
    assert feed.health()["stream_last_failure_class"] == "ConnectionError"
    assert feed.health()["stream_failure_count"] == 1
    assert socket.closed


def test_pong_does_not_refresh_an_old_quote_or_claim_recovery(tmp_path, capsys):
    feed, _, _ = make_feed(tmp_path, idle() + [(0, pong)] + idle() + [(0, pong)])
    feed.ingest_message(trade(BASE))
    capsys.readouterr()
    feed._stream_forever()
    health = feed.health()
    assert health["last_price_ts"] == BASE
    assert health["valid_trade_tick_count"] == 1
    assert health["price_age_seconds"] == 40
    assert health["fresh"] is False
    assert health["transport_pong_count"] == 2
    assert health["subscription_state"] == "SENT_UNVERIFIED"
    assert "REAL_TICK_RESUMED" not in capsys.readouterr().out


def test_ping_deadline_uses_monotonic_time_not_wall_clock(tmp_path):
    feed, _, elapsed = make_feed(tmp_path, idle() + [(5, pong)])
    wall_offset = [0]
    feed.clock = lambda: BASE + elapsed[0] + wall_offset[0]
    original_clock = feed._transport_clock

    def clock():
        if elapsed[0] >= 20:
            wall_offset[0] = 3600
        return original_clock()

    feed._transport_clock = clock
    feed._stream_forever()
    assert feed.health()["stream_failure_count"] == 0
    assert feed.health()["transport_pong_count"] == 1


def test_real_library_handles_peer_ping_and_fragmented_trade(tmp_path):
    """Exercise pinned websocket-client's control and reassembly path offline."""
    from websocket import WebSocket

    module = importlib.import_module("runtime.finnhub_market_data")
    message = trade(BASE).encode()
    frames = iter([
        ABNF(fin=0, opcode=ABNF.OPCODE_TEXT, data=message[:30]),
        ABNF(fin=1, opcode=ABNF.OPCODE_PING, data=b"peer-ping"),
        ABNF(fin=1, opcode=ABNF.OPCODE_CONT, data=message[30:]),
    ])
    socket = WebSocket()
    replies = []
    socket.pong = replies.append
    socket.send = lambda _message: None
    socket.close = lambda: None

    def recv_frame():
        try:
            return next(frames)
        except StopIteration:
            feed._stop_event.set()
            return ABNF(fin=1, opcode=ABNF.OPCODE_TEXT, data=b'{"type":"ping"}')

    socket.recv_frame = recv_frame
    feed = module.FinnhubForexFeed(
        token="PRIVATE", store_path=tmp_path / "market.json", clock=lambda: BASE,
        websocket_connector=lambda *args, **kwargs: socket,
    )
    feed._stop_event.wait = lambda _seconds: True
    feed._stream_forever()
    assert replies == [b"peer-ping"]
    assert feed.health()["stream_failure_count"] == 0
    assert feed.health()["valid_trade_tick_count"] == 1
    assert feed.health()["last_price_ts"] == BASE


def test_real_library_preserves_partial_frame_across_idle_timeout(tmp_path):
    """A receive timeout must not discard bytes already held by the parser."""
    from websocket import WebSocket

    module = importlib.import_module("runtime.finnhub_market_data")
    raw = ABNF(fin=1, opcode=ABNF.OPCODE_TEXT, mask_value=0,
               data=trade(BASE).encode()).format()
    offset = [0]
    timed_out = [False]
    elapsed = [0]
    socket = WebSocket()
    socket.send = lambda _message: None
    socket.close = lambda: None

    def receive(size):
        if offset[0] >= 12 and not timed_out[0]:
            timed_out[0] = True
            elapsed[0] += 5
            raise WebSocketTimeoutException("OFFLINE partial-frame idle read")
        chunk = raw[offset[0]:offset[0] + min(size, 10)]
        assert chunk, "test should stop after the completed frame"
        offset[0] += len(chunk)
        return chunk

    socket.frame_buffer.recv = receive
    feed = module.FinnhubForexFeed(
        token="PRIVATE", store_path=tmp_path / "market.json",
        clock=lambda: BASE + elapsed[0],
        websocket_connector=lambda *args, **kwargs: socket,
    )
    feed._transport_clock = lambda: elapsed[0]
    feed._stop_event.wait = lambda _seconds: True
    ingest = feed.ingest_message

    def ingest_and_stop(message):
        ingest(message)
        feed._stop_event.set()

    feed.ingest_message = ingest_and_stop
    feed._stream_forever()
    health = feed.health()
    assert timed_out[0]
    assert health["transport_idle_read_count"] == 1
    assert health["stream_failure_count"] == 0
    assert health["valid_trade_tick_count"] == 1
    assert health["last_price_ts"] == BASE

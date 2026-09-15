"""R-023: exercise installed library code while simulating transport I/O only.

Existing call-shape tests remain unchanged. These tests do not certify live
provider connectivity, real certificate handshakes, or production acceptance.
"""
from __future__ import annotations

import base64
import hashlib
import importlib
import json
import socket

import pytest
import requests
import websocket


@pytest.fixture
def _forbid_external_network(monkeypatch):
    """A missing transport stub must fail, never contact a real service."""
    def denied(*args, **kwargs):
        raise AssertionError("External network is forbidden in compatibility tests")

    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)


def test_telegram_real_requests_preparation(monkeypatch, _forbid_external_network):
    """Retain real post/Session/PreparedRequest/Response; stub adapter I/O only."""
    publisher = importlib.import_module("core.telegram_publisher")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:compatibility-test-token")
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    calls = []

    def fake_send(adapter, request, **kwargs):
        calls.append((request, kwargs))
        response = requests.Response()
        response.status_code = 200
        response.url = request.url
        response.request = request
        response._content = b'{"ok":true,"result":{"message_id":42}}'
        response.headers["Content-Type"] = "application/json"
        return response

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", fake_send)
    # The canonical autouse fixture blocks requests.post before the library runs.
    # Restore the actual library implementation only after adapter I/O is stubbed;
    # DNS and socket guards above remain active, even if the stub is bypassed.
    monkeypatch.setattr(requests, "post", requests.api.post)
    result = publisher.send_message(chat_id=77, text="compatibility")

    assert result == {"ok": True, "result": {"message_id": 42}}
    assert len(calls) == 1
    prepared, options = calls[0]
    assert isinstance(prepared, requests.PreparedRequest)
    assert prepared.method == "POST"
    assert prepared.url == "https://api.telegram.org/bot123456:compatibility-test-token/sendMessage"
    assert json.loads(prepared.body) == {"chat_id": 77, "text": "compatibility"}
    assert prepared.headers["Content-Type"] == "application/json"
    assert options["timeout"] == 10
    assert options["verify"] is True


@pytest.mark.parametrize("error_type", [requests.exceptions.Timeout, requests.exceptions.SSLError])
def test_telegram_real_requests_transport_error(
    monkeypatch, _forbid_external_network, error_type
):
    publisher = importlib.import_module("core.telegram_publisher")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:compatibility-test-token")
    calls = []

    def fail_send(adapter, request, **kwargs):
        calls.append(request)
        raise error_type("simulated transport failure")

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", fail_send)
    # Exercise real Requests dispatch under the same adapter/socket isolation.
    monkeypatch.setattr(requests, "post", requests.api.post)
    result = publisher.delete_message(chat_id=77, message_id=42)

    assert len(calls) == 1
    assert isinstance(calls[0], requests.PreparedRequest)
    assert result["outcome"] == publisher.DELETE_OUTCOME_TRANSPORT
    assert result["description"] == "simulated transport failure"


class _MemoryWebSocketTransport:
    """Preconnected test-only socket using the public websocket socket option.

    Real library code validates the HTTP upgrade and encodes/decodes frames.
    This is not a TLS handshake or live-provider connectivity test.
    """
    def __init__(self, *, invalid_accept=False):
        self.invalid_accept = invalid_accept
        self.incoming = bytearray()
        self.sent = bytearray()
        self.closed = False
        self.timeout = 30
        self.receive_error = None
        self._handshake_sent = False

    def send(self, data):
        data = bytes(data)
        self.sent.extend(data)
        if not self._handshake_sent and b"\r\n\r\n" in self.sent:
            headers = bytes(self.sent).decode("ascii").split("\r\n")
            key = next(line.split(":", 1)[1].strip() for line in headers
                       if line.lower().startswith("sec-websocket-key:"))
            # SHA-1 is required by the WebSocket handshake protocol here.
            accept = base64.b64encode(hashlib.sha1(
                (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")
            ).digest()).decode("ascii")
            if self.invalid_accept:
                accept = "invalid-test-accept"
            self.incoming.extend((
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii"))
            self._handshake_sent = True
        return len(data)

    def recv(self, size):
        if self.incoming:
            chunk = bytes(self.incoming[:size])
            del self.incoming[:size]
            return chunk
        if self.receive_error is not None:
            raise self.receive_error
        return b""

    def gettimeout(self):
        return self.timeout

    def settimeout(self, timeout):
        self.timeout = timeout

    def shutdown(self, how):
        self.closed = True

    def close(self):
        self.closed = True


def test_real_websocket_handshake_send_recv_close(_forbid_external_network):
    transport = _MemoryWebSocketTransport()
    client = websocket.create_connection(
        "wss://compatibility.invalid/feed", timeout=30, socket=transport
    )
    try:
        assert isinstance(client, websocket.WebSocket)
        assert client.connected is True
        assert client.getstatus() == 101
        assert client.gettimeout() == 30
        handshake_end = len(transport.sent)
        client.send("compatibility")
        frame = bytes(transport.sent[handshake_end:])
        payload = b"compatibility"
        assert frame[0] == 0x81  # FIN + text opcode.
        assert frame[1] == (0x80 | len(payload))  # Client masking is mandatory.
        assert len(frame) == 6 + len(payload)
        mask = frame[2:6]
        assert bytes(value ^ mask[index % 4]
                     for index, value in enumerate(frame[6:])) == payload
        transport.incoming.extend(b"\x81\x02ok")  # Unmasked server text frame.
        assert client.recv() == "ok"
    finally:
        client.close(timeout=0)
    assert transport.closed is True
    assert client.connected is False


def test_real_websocket_rejects_invalid_upgrade(_forbid_external_network):
    transport = _MemoryWebSocketTransport(invalid_accept=True)
    with pytest.raises(websocket.WebSocketException):
        websocket.create_connection(
            "wss://compatibility.invalid/feed", timeout=30, socket=transport
        )
    assert transport.closed is True


@pytest.mark.parametrize("timed_out", [False, True])
def test_real_websocket_receive_failure(_forbid_external_network, timed_out):
    transport = _MemoryWebSocketTransport()
    client = websocket.create_connection(
        "wss://compatibility.invalid/feed", timeout=30, socket=transport
    )
    if timed_out:
        transport.receive_error = socket.timeout("simulated receive timeout")
    expected = (websocket.WebSocketTimeoutException if timed_out
                else websocket.WebSocketConnectionClosedException)
    try:
        with pytest.raises(expected):
            client.recv()
    finally:
        client.close(timeout=0)
    assert transport.closed is True

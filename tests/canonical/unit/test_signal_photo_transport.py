"""Multipart photo publication preserves existing destination/reply behavior."""

import json

import pytest


def test_photo_keeps_topic_feedback_and_reply_context(monkeypatch):
    from core import telegram_publisher as publisher

    captured = {}
    markup = {"inline_keyboard": [[{"text": "WIN", "callback_data": "result:win"}]]}

    class Response:
        status_code = 200

        def json(self):
            return {"ok": True, "result": {"message_id": 123}}

    def post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "offline-token")
    monkeypatch.setattr(publisher.requests, "post", post)

    response = publisher.send_photo(
        chat_id=-100123, photo=b"png", caption="#2 · SELL · OPEN NOW",
        reply_to_message_id=97, reply_markup=markup, thread_id=7,
    )

    assert response["result"]["message_id"] == 123
    assert captured["url"].endswith("/sendPhoto")
    assert captured["data"]["chat_id"] == -100123
    assert captured["data"]["message_thread_id"] == 7
    assert json.loads(captured["data"]["reply_markup"]) == markup
    assert json.loads(captured["data"]["reply_parameters"])["message_id"] == 97
    assert captured["files"]["photo"][1:] == (b"png", "image/png")
    assert captured["timeout"] == 20


def test_failed_photo_request_never_falls_back_to_a_second_message(monkeypatch):
    from core import telegram_publisher as publisher

    calls = []

    def timeout(url, **kwargs):
        calls.append(url)
        raise TimeoutError("acceptance unavailable")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "offline-token")
    monkeypatch.setattr(publisher.requests, "post", timeout)
    with pytest.raises(TimeoutError):
        publisher.send_photo(chat_id=123, photo=b"png", caption="#2")
    assert len(calls) == 1 and calls[0].endswith("/sendPhoto")

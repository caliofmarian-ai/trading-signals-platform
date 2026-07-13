from __future__ import annotations


class FakePublisher:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.calls: list[dict] = []

    def send_message(self, chat_id: int, text: str, reply_markup=None, thread_id=None):
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
                "thread_id": thread_id,
            }
        )
        if self.fail:
            raise RuntimeError("simulated publisher failure")
        return {"ok": True, "result": {"message_id": 1000 + len(self.calls)}}

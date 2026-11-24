"""Web Push transport. Sends generic notices; the authenticated API owns signal access."""
from __future__ import annotations

import base64
import json
import time
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def valid_subscription(value: dict) -> dict:
    if not isinstance(value,dict) or not isinstance(value.get("endpoint"),str):
        raise ValueError("Invalid notification subscription.")
    url = urlsplit(value["endpoint"])
    allowed = ("fcm.googleapis.com","updates.push.services.mozilla.com","web.push.apple.com")
    if (url.scheme != "https" or url.port not in (None,443) or url.username or url.password
            or url.fragment or not any(url.hostname == host or
            url.hostname and url.hostname.endswith("."+host) for host in allowed)):
        raise ValueError("Unsupported notification provider.")
    keys = value.get("keys",{})
    for key, length in (("p256dh",65),("auth",16)):
        raw = keys.get(key,"")
        if not isinstance(raw,str) or len(raw)>200:
            raise ValueError("Invalid notification key.")
        try:
            decoded = base64.urlsafe_b64decode(raw + "="*(-len(raw)%4))
        except Exception as exc:
            raise ValueError("Invalid notification key.") from exc
        if len(decoded) != length:
            raise ValueError("Invalid notification key.")
    return {"endpoint":value["endpoint"],"keys":keys}


class PushDelivery:
    def __init__(self, service, subject: str):
        self.service = service
        self.store = service.store
        self.subject = subject
        path = self.store.directory / "push-private.pem"
        if not path.exists():
            key = ec.generate_private_key(ec.SECP256R1())
            # Exclusive creation keeps one persistent key across concurrent starts.
            try:
                with path.open("xb") as output:
                    path.chmod(0o600)
                    output.write(key.private_bytes(serialization.Encoding.PEM,
                        serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            except FileExistsError:
                pass
        self.path = path
        key = serialization.load_pem_private_key(path.read_bytes(),password=None)
        self.public_key = base64.urlsafe_b64encode(key.public_key().public_bytes(
            serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint)).decode().rstrip("=")

    def drain(self, send=None):
        from pywebpush import webpush
        sender = send or webpush
        now = int(time.time())
        with self.store.db() as db:
            jobs = db.execute("""SELECT p.*,s.channel,s.stage,s.payload,d.user_id,d.subscription,
                u.email,u.role,u.subscriber_ref FROM pushes p
                JOIN signals s ON s.event_id=p.event_id
                JOIN devices d ON d.endpoint=p.endpoint JOIN users u ON u.id=d.user_id
                WHERE p.next_attempt<=? ORDER BY p.id LIMIT 20""",(now,)).fetchall()
        for row in jobs:
            payload = json.loads(row["payload"])
            with self.store.db() as db:
                logged_in = db.execute("SELECT 1 FROM sessions WHERE user_id=? AND expires>?",
                                       (row["user_id"],now)).fetchone()
            user = {"id":row["user_id"],"role":row["role"],"subscriber_ref":row["subscriber_ref"]}
            expired = payload.get("expires_at") and payload["expires_at"]<=now
            deliver = logged_in and not expired and now-payload["created_ts"]<=120 and self.service.can_read(user,row["channel"])
            retry = False
            if deliver:
                try:
                    # The lock screen does not expose market, direction, entry or subscriber details.
                    sender(subscription_info=json.loads(row["subscription"]),
                        data=json.dumps({"title":"Trading Signals","body":"A new signal is available.",
                                         "event_id":row["event_id"],"url":"/#signals"}),
                        vapid_private_key=str(self.path),vapid_claims={"sub":self.subject},
                        ttl=60,timeout=5)
                except Exception as exc:
                    response = getattr(exc,"response",None)
                    status = getattr(response,"status_code",None)
                    if status in (404,410):
                        with self.store.db() as db:
                            db.execute("DELETE FROM devices WHERE endpoint=?",(row["endpoint"],))
                    else:
                        retry = row["attempts"]<2
                        self.store.audit("PUSH_ERROR","APP",type(exc).__name__)
            with self.store.db() as db:
                if retry:
                    db.execute("UPDATE pushes SET attempts=attempts+1,next_attempt=? WHERE id=?",
                               (now+2**(row["attempts"]+2),row["id"]))
                else:
                    db.execute("DELETE FROM pushes WHERE id=?",(row["id"],))
            if deliver and not retry:
                self.store.set_meta("last_push_attempt",now)

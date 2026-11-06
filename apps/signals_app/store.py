from __future__ import annotations

from contextlib import contextmanager
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import sqlite3
import time
import uuid


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password: str, salt: bytes | None = None) -> str:
    if not isinstance(password, str) or not 12 <= len(password) <= 256:
        raise ValueError("Use a password containing 12–256 characters.")
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return salt.hex() + ":" + derived.hex()


def password_matches(password: str, encoded: str) -> bool:
    try:
        salt, _ = encoded.split(":", 1)
        return hmac.compare_digest(password_hash(password, bytes.fromhex(salt)), encoded)
    except (ValueError, TypeError):
        return False


class Store:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.directory / "app.sqlite3"
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'MEMBER',
                    subscriber_ref TEXT UNIQUE, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
                    csrf TEXT NOT NULL, expires INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS invites (
                    hash TEXT PRIMARY KEY, email TEXT NOT NULL, subscriber_ref TEXT NOT NULL,
                    expires INTEGER NOT NULL, used_by TEXT);
                CREATE TABLE IF NOT EXISTS signals (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL,
                    channel TEXT NOT NULL, signal_id TEXT NOT NULL, stage TEXT NOT NULL,
                    payload TEXT NOT NULL, created INTEGER NOT NULL, published INTEGER NOT NULL,
                    quota_day TEXT NOT NULL,
                    UNIQUE(channel,signal_id,stage));
                CREATE INDEX IF NOT EXISTS signal_feed ON signals(channel,seq);
                CREATE TABLE IF NOT EXISTS feedback (
                    user_id TEXT NOT NULL, signal_id TEXT NOT NULL, result TEXT NOT NULL,
                    created INTEGER NOT NULL, PRIMARY KEY(user_id,signal_id));
                CREATE TABLE IF NOT EXISTS outcomes (
                    signal_id TEXT PRIMARY KEY, result TEXT NOT NULL, evidence_ref TEXT NOT NULL,
                    observed INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS rate_limits (key TEXT NOT NULL, ts INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS rates ON rate_limits(key,ts);
                CREATE TABLE IF NOT EXISTS devices (
                    endpoint TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                    subscription TEXT NOT NULL, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS pushes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt INTEGER NOT NULL, UNIQUE(event_id,endpoint));
                CREATE TABLE IF NOT EXISTS audit (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL,
                    actor TEXT NOT NULL, detail TEXT NOT NULL, created INTEGER NOT NULL);
            """)
        self.path.chmod(0o600)
        self.dummy_hash = password_hash(secrets.token_urlsafe(24))

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def meta(self, key: str, default=None):
        with self.db() as db:
            row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key: str, value):
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, json.dumps(value)))

    def audit(self, action: str, actor: str, detail: str):
        with self.db() as db:
            db.execute("INSERT INTO audit(action,actor,detail,created) VALUES (?,?,?,?)",
                       (action, actor, detail[:300], int(time.time())))

    def allow_attempt(self, key: str, limit: int, window: int = 60) -> bool:
        now = int(time.time())
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM rate_limits WHERE ts<?", (now-3600,))
            count = db.execute("SELECT COUNT(*) FROM rate_limits WHERE key=? AND ts>?",
                               (key, now-window)).fetchone()[0]
            if count >= limit:
                return False
            db.execute("INSERT INTO rate_limits VALUES (?,?)", (key, now))
        return True

    def register(self, email: str, password: str, role: str = "MEMBER") -> dict:
        uid = str(uuid.uuid4())
        encoded = password_hash(password)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if role == "OWNER" and db.execute("SELECT 1 FROM users WHERE role='OWNER'").fetchone():
                raise ValueError("The application owner is already configured.")
            db.execute("INSERT INTO users(id,email,password,role,created) VALUES (?,?,?,?,?)",
                       (uid, email, encoded, role, int(time.time())))
        self.audit("ACCOUNT_CREATED", uid, role)
        return {"id": uid, "email": email, "role": role, "subscriber_ref": None}

    def authenticate(self, email: str, password: str):
        with self.db() as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        valid = password_matches(password, row["password"] if row else self.dummy_hash)
        return dict(row) if row and valid else None

    def start_session(self, uid: str) -> tuple[str, str]:
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        now = int(time.time())
        with self.db() as db:
            db.execute("DELETE FROM sessions WHERE expires<?", (now,))
            db.execute("INSERT INTO sessions VALUES (?,?,?,?)",
                       (token_hash(token), uid, csrf, now+7*24*3600))
        return token, csrf

    def session(self, token: str | None):
        if not token:
            return None
        with self.db() as db:
            row = db.execute("""SELECT u.id,u.email,u.role,u.subscriber_ref,s.csrf,s.expires
                FROM sessions s JOIN users u ON u.id=s.user_id
                WHERE s.hash=? AND s.expires>?""", (token_hash(token), int(time.time()))).fetchone()
        return dict(row) if row else None

    def logout(self, token: str, uid: str):
        with self.db() as db:
            db.execute("DELETE FROM sessions WHERE hash=?", (token_hash(token),))
            # Generic lock-screen notifications also stop immediately on sign-out.
            db.execute("DELETE FROM pushes WHERE endpoint IN (SELECT endpoint FROM devices WHERE user_id=?)", (uid,))
            db.execute("DELETE FROM devices WHERE user_id=?", (uid,))

    def invite(self, email: str, subscriber_ref: str, ttl: int = 900) -> str:
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute("INSERT INTO invites VALUES (?,?,?,?,NULL)",
                       (token_hash(token), email, subscriber_ref, int(time.time())+ttl))
        return token

    def claim(self, uid: str, email: str, token: str, verify) -> None:
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM invites WHERE hash=?", (token_hash(token),)).fetchone()
            if not row or row["expires"] <= int(time.time()) or row["used_by"] or row["email"] != email:
                raise ValueError("This connection link is invalid, expired, or belongs to another account.")
            linked = db.execute("SELECT subscriber_ref FROM users WHERE id=?", (uid,)).fetchone()
            if linked[0] and linked[0] != row["subscriber_ref"]:
                raise ValueError("This account is already connected to another subscriber.")
            verify(row["subscriber_ref"])
            db.execute("UPDATE users SET subscriber_ref=? WHERE id=?", (row["subscriber_ref"], uid))
            db.execute("UPDATE invites SET used_by=? WHERE hash=?", (uid, token_hash(token)))
        self.audit("SUBSCRIBER_CONNECTED", uid, "Existing canonical subscription; no payment created")

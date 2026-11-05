from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from fastapi.testclient import TestClient
import pytest

from apps.signals_app.api import create_app
from apps.signals_app import canonical
from apps.signals_app.service import AppService
from apps.signals_app.store import Store

KEY = "test-ingest-secret-that-is-longer-than-thirty-two-characters"
SETUP = "test-owner-setup-secret-that-is-longer-than-thirty-two"


def candidate(stage="PRE", sid="test-signal", **changes):
    now = int(time.time())
    execution = stage in {"CONFIRM","OPEN_NOW"}
    return dict(event_type="SIGNAL_CANDIDATE",stage=stage,signal_id=sid,symbol="EUR/USD",
                timeframe="M1",direction="BUY",score_total=8.25,buffer_mode="SMALL",
                buffer_distance=.0002,model_expiry=2.5,execution_time_available=execution,
                confirm_expiry_min_minutes=1.5 if execution else None,
                confirm_expiry_max_minutes=2.5 if execution else None,
                open_now_expiry_minutes=2 if stage=="OPEN_NOW" else None,
                execution_calibration_source="TEST_FIXTURE" if execution else None,
                candle_ts=now-60,created_ts=now,entry_price=1.1,payload={},
                fsm_transition_id="test-fsm",execution_attempt_id="test-execution",
                decision_id="test-decision") | changes


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path,public_url="http://testserver",ingest_token=KEY,setup_token=SETUP)) as client:
        yield client


def register(client,email="member@example.com"):
    response = client.post("/api/register",json={"email":email,"password":"private-test-password"})
    assert response.status_code==200
    return {"X-CSRF-Token":response.json()["csrf"]}


def test_shared_canonical_channels_and_exclusive_access(client):
    assert [item["id"] for item in client.get("/api/config").json()["channels"]]==["FREE","BASIC","PRO","ELITE"]
    register(client)
    assert client.get("/api/session").json()["allowed_channels"]==["FREE"]
    assert client.get("/api/signals/FREE").status_code==200
    assert client.get("/api/signals/ELITE").status_code==403
    assert client.get("/api/admin").status_code==403


def test_role_and_subscriber_cannot_be_self_assigned(client):
    response=client.post("/api/register",json={"email":"member@example.com","password":"private-test-password",
        "role":"OWNER","subscriber_ref":"somebody-elses-paid-account"})
    assert response.status_code==200
    data=client.get("/api/session").json()
    assert data["role"]=="MEMBER" and not data["access"]["connected"]


def test_http_origin_csrf_and_session_revocation(client):
    assert client.post("/api/register",headers={"Origin":"https://evil.invalid"},json={}).status_code==403
    csrf=register(client)
    assert client.post("/api/logout",json={}).status_code==403
    assert client.post("/api/logout",headers=csrf,json={}).status_code==200
    assert client.get("/api/session").status_code==401


def test_source_auth_candidate_validation_and_dedup(client):
    data={"candidate":candidate(),"provider":"TWELVE_DATA"}
    assert client.post("/api/internal/signals",json=data).status_code==401
    headers={"Authorization":"Bearer "+KEY}
    for index in range(2):
        response=client.post("/api/internal/signals",json=data,headers=headers)
        assert response.status_code==200
        assert response.json()["published_count"]==(4 if index==0 else 0)
    register(client)
    rows=client.get("/api/signals/FREE").json()["signals"]
    assert len(rows)==1
    assert "payload" not in rows[0]
    bad=candidate("OPEN_NOW",open_now_expiry_minutes=None)
    assert client.post("/api/internal/signals",json={"candidate":bad,"provider":"TWELVE_DATA"},headers=headers).status_code==400


def test_lifecycle_exact_timing_and_no_fabricated_stages(tmp_path):
    service=AppService(Store(tmp_path))
    now=int(time.time())
    for stage in ["PRE","CONFIRM","OPEN_NOW"]:
        service.publish(candidate(stage,created_ts=now),provider="TWELVE_DATA",now=now)
    rows=service.feed("FREE")
    assert [row["stage"] for row in rows]==["OPEN_NOW","CONFIRM","PRE"]
    assert rows[0]["expires_at"]==now+120
    assert rows[1]["open_now_expiry_minutes"] is None
    assert rows[2]["expires_at"] is None
    assert service.publish(candidate("PRE",score_total=9,created_ts=now),provider="FINNHUB")["blocked"]
    with pytest.raises(ValueError,match="Conflicting"):
        service.publish(candidate("PRE",score_total=9,created_ts=now),provider="TWELVE_DATA",now=now)


def test_quotas_count_unique_entries_not_stages(tmp_path):
    service=AppService(Store(tmp_path))
    now=int(time.time())
    for index in range(7):
        service.publish(candidate("OPEN_NOW",sid=f"test-{index}",created_ts=now),provider="TWELVE_DATA",now=now)
    assert len(service.feed("FREE"))==6
    assert len(service.feed("BASIC"))==7
    service.publish(candidate("CONFIRM",sid="next",created_ts=now),provider="TWELVE_DATA",now=now)
    assert len(service.feed("FREE"))==6


def test_missing_fsm_cannot_publish(tmp_path):
    service=AppService(Store(tmp_path))
    with pytest.raises(ValueError):
        service.publish(candidate(fsm_transition_id=None),provider="TWELVE_DATA")
    assert not service.feed("FREE")


def test_owner_setup_is_secret_and_single_use(client):
    data={"email":"owner@example.com","password":"owner-test-password","token":SETUP}
    assert client.post("/api/setup",json=data|{"token":"wrong"}).status_code==403
    assert client.post("/api/setup",json=data).status_code==200
    assert client.get("/api/admin").status_code==200
    assert client.post("/api/setup",json=data|{"email":"second@example.com"}).status_code==400


def test_snapshot_staleness_revokes_connected_paid_access(tmp_path,monkeypatch):
    service=AppService(Store(tmp_path))
    now=int(time.time())
    service.store.set_meta("subscription_snapshot_at",now)
    monkeypatch.setattr(canonical,"resolve_entitlement",lambda **_:dict(tier="PRO",access_state="ACTIVE"))
    account={"role":"MEMBER","subscriber_ref":"verified-subscriber"}
    assert service.can_read(account,"PRO")
    assert not service.can_read(account,"FREE")
    assert service.entitlement(account,now=now+301)["access_state"]=="UNAVAILABLE"


def test_claim_bound_to_account_atomic_single_use(tmp_path):
    store=Store(tmp_path)
    first=store.register("first@example.com","private-test-password")
    second=store.register("second@example.com","private-test-password")
    token=store.invite("first@example.com","verified-subscriber")
    with pytest.raises(ValueError):store.claim(second["id"],second["email"],token,lambda _:None)
    store.claim(first["id"],first["email"],token,lambda _:None)
    with pytest.raises(ValueError):store.claim(first["id"],first["email"],token,lambda _:None)
    with store.db() as db:
        assert db.execute("SELECT COUNT(*) FROM invites WHERE used_by IS NOT NULL").fetchone()[0]==1


def test_passwords_tokens_and_private_responses_are_not_cached(client):
    register(client)
    with client.app.state.store.db() as db:
        row=db.execute("SELECT password FROM users").fetchone()
        assert "private-test-password" not in row[0]
        session=db.execute("SELECT hash FROM sessions").fetchone()
        assert session[0]!=client.cookies["signals_session"]
    response=client.get("/api/session")
    assert response.headers["cache-control"]=="no-store"
    assert "HttpOnly" in client.post("/api/login",json={"email":"member@example.com","password":"private-test-password"}).headers["set-cookie"]
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_metrics_do_not_invent_performance_or_promote_self_reports(tmp_path):
    service=AppService(Store(tmp_path))
    assert service.metrics()["market_win_rate"] is None
    with service.store.db() as db:
        db.execute("INSERT INTO feedback VALUES ('member','signal','WIN',?)",(int(time.time()),))
    assert service.metrics()["community_reports"]["WIN"]==1
    assert service.metrics()["market_win_rate"] is None


def test_untrusted_push_endpoint_is_rejected(client):
    csrf=register(client)
    response=client.post("/api/push",headers=csrf,json={"endpoint":"https://127.0.0.1/private","keys":{}})
    assert response.status_code==400


def test_existing_telegram_entrypoint_has_no_app_imports():
    repo=Path(__file__).resolve().parents[3]
    for path in [repo/"send/runtime/system_boot.py",repo/"send/runtime/engine_loop.py",repo/"scripts/railway_start.py"]:
        assert "apps.signals_app" not in path.read_text()
    root_config=json.loads((repo/"railway.json").read_text())
    assert "scripts.railway_start" in root_config["deploy"]["startCommand"]


def test_manifest_icons_and_service_worker_shell_only(client):
    manifest=client.get("/assets/manifest.webmanifest").json()
    assert manifest["display"]=="standalone"
    for icon in manifest["icons"]:
        assert client.get(icon["src"]).status_code==200
    sw=client.get("/sw.js").text
    assert "url.pathname.startsWith('/api/')" in sw


def test_android_package_association_and_authenticated_upload(client,monkeypatch):
    assert client.get('/.well-known/assetlinks.json').json()==[]
    fingerprint=':'.join(['A1']*32)
    monkeypatch.setenv('SIGNALS_APP_ANDROID_SHA256',fingerprint)
    assert client.get('/.well-known/assetlinks.json').json()[0]['target']['sha256_cert_fingerprints']==[fingerprint]
    assert client.get('/download/android').status_code==404
    assert client.post('/api/internal/android-apk',content=b'not-an-apk').status_code==401
    assert client.post('/api/internal/android-apk',content=b'not-an-apk',headers={'Authorization':'Bearer '+KEY}).status_code==400

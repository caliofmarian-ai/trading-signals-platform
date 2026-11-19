from __future__ import annotations

import base64
import time

from fastapi.testclient import TestClient

from apps.signals_app.api import create_app
from apps.signals_app.store import Store

KEY = "test-ingest-secret-that-is-longer-than-thirty-two-characters"
SETUP = "test-owner-setup-secret-that-is-longer-than-thirty-two"


def receipt(phase="entry", *, study_id="prospective-study-001", now=None, image=False):
    now = int(time.time()) if now is None else now
    return {
        "protocol": "PRIVATE_V3_STUDY_RECEIPT_V1",
        "study_id": study_id,
        "phase": phase,
        "created_ts": now,
        "signal_label": "19.11.2026 · 20:00:00 · nr. 1",
        "text": "OPEN_NOW · STUDIU V3\nProvider: FINNHUB\nSymbol: EUR/USD",
        "provider": "FINNHUB",
        "symbol": "EUR/USD",
        "strategy_version": "3.0.0",
        "decision_policy": "PHYSICAL_ONLY_V3",
        "format": "PHOTO" if image else "TEXT",
        "image_base64": base64.b64encode(b"\x89PNG\r\n\x1a\nfixture").decode("ascii") if image else None,
    }


def owner_client(tmp_path):
    client = TestClient(create_app(tmp_path, public_url="http://testserver",
                                   ingest_token=KEY, setup_token=SETUP))
    response = client.post("/api/setup", json={
        "email": "owner@example.com", "password": "owner-private-test-password", "token": SETUP,
    })
    assert response.status_code == 200
    return client


def test_private_studies_are_owner_only_separate_and_idempotent(tmp_path):
    with owner_client(tmp_path) as client:
        headers = {"Authorization": "Bearer " + KEY}
        entry = receipt(image=True)
        first = client.post("/api/internal/signals", json={"private_study": entry}, headers=headers)
        assert first.status_code == 200
        accepted = first.json()
        assert accepted["status"] == "API_ACCEPTED"
        assert accepted["transport"] == "APP"
        assert accepted["phone_receipt_proven"] is False

        duplicate = client.post("/api/internal/signals", json={"private_study": entry}, headers=headers)
        assert duplicate.status_code == 200
        assert duplicate.json()["receipt_id"] == accepted["receipt_id"]
        assert duplicate.json()["duplicate"] is True

        result = receipt("result", image=False)
        result["text"] = "REZULTAT STUDIU V3\nRezultat direcțional măsurat separat."
        result_response = client.post("/api/internal/signals", json={"private_study": result}, headers=headers)
        assert result_response.status_code == 200

        dashboard = client.get("/api/admin")
        assert dashboard.status_code == 200
        rows = dashboard.json()["private_studies"]
        assert [row["phase"] for row in rows] == ["result", "entry"]
        assert rows[1]["image_base64"] == entry["image_base64"]
        assert all(row["phone_receipt_proven"] is False for row in rows)

        with Store(tmp_path).db() as db:
            assert db.execute("SELECT COUNT(*) FROM signals").fetchone()[0] == 0
            assert db.execute("SELECT COUNT(*) FROM private_studies").fetchone()[0] == 2


def test_private_study_result_requires_entry_and_member_cannot_read_inbox(tmp_path):
    with owner_client(tmp_path) as owner:
        headers = {"Authorization": "Bearer " + KEY}
        result_first = owner.post("/api/internal/signals", json={
            "private_study": receipt("result", study_id="missing-entry")
        }, headers=headers)
        assert result_first.status_code == 400

        entry = owner.post("/api/internal/signals", json={
            "private_study": receipt(study_id="owner-only-study")
        }, headers=headers)
        assert entry.status_code == 200

        member = owner.post("/api/register", json={
            "email": "member@example.com", "password": "private-member-password",
        })
        assert member.status_code == 200
        assert owner.get("/api/admin").status_code == 403


def test_private_study_rejects_policy_or_provider_drift(tmp_path):
    with owner_client(tmp_path) as client:
        headers = {"Authorization": "Bearer " + KEY}
        invalid = receipt()
        invalid["provider"] = "TWELVE_DATA"
        assert client.post("/api/internal/signals", json={"private_study": invalid},
                           headers=headers).status_code == 400
        invalid = receipt()
        invalid["decision_policy"] = "SCORED_V2"
        assert client.post("/api/internal/signals", json={"private_study": invalid},
                           headers=headers).status_code == 400
        assert client.post("/api/internal/signals", json={"private_study": receipt()},
                           headers={}).status_code == 401

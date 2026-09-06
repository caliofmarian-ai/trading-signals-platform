from __future__ import annotations

from copy import deepcopy

import pytest

from core import event_schema_migration as migration


def test_legacy_compat_inventory_is_explicit_and_bounded() -> None:
    assert migration.legacy_compat_event_types() == (
        "decision",
        "signal_event",
        "tier_publish",
        "tier_reset",
    )


def test_legacy_name_never_becomes_primary_merely_from_v3_stamp() -> None:
    record = {
        "event_type": "tier_publish",
        "schema_version": "3.0.0",
        "data": {"publish_result": "PUBLISHED"},
    }
    snapshot = deepcopy(record)

    assert migration.classify_event_identity(record) == migration.LEGACY_COMPAT
    assert record == snapshot


def test_non_v3_record_keeps_historical_schema_identity() -> None:
    record = {
        "event_type": "route_publish_result",
        "schema_version": "2.0.0",
        "data": {},
    }
    snapshot = deepcopy(record)

    assert migration.classify_event_identity(record) == migration.HISTORICAL_SCHEMA
    assert record == snapshot


def test_current_v3_primary_identity_is_distinct() -> None:
    record = {
        "event_type": "route_publish_result",
        "schema_version": "3.0.0",
        "data": {},
    }

    assert migration.classify_event_identity(record) == migration.PRIMARY_V3


def test_missing_identity_is_invalid_without_inference() -> None:
    assert migration.classify_event_identity({"event_type": "route_publish_result"}) == migration.INVALID_EVENT_IDENTITY
    assert migration.classify_event_identity({"schema_version": "3.0.0"}) == migration.INVALID_EVENT_IDENTITY
    assert migration.classify_event_identity({}) == migration.INVALID_EVENT_IDENTITY


def test_primary_v3_guard_rejects_legacy_and_unknown_types() -> None:
    with pytest.raises(migration.EventSchemaMigrationError, match="legacy compatibility"):
        migration.require_primary_v3_event_type("tier_publish")

    with pytest.raises(migration.EventSchemaMigrationError, match="unsupported primary v3"):
        migration.require_primary_v3_event_type("not_a_real_event")

    assert migration.require_primary_v3_event_type("route_publish_result") == "route_publish_result"

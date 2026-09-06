"""Bounded Event Schema v3 migration helpers.

R-021 separates current write authority from historical compatibility.  This
module does not rewrite event records and does not infer newer truth from older
evidence.  It only classifies event identity and exposes a guard that current
runtime producers can adopt when they are migrated to v3-only writes.
"""

from __future__ import annotations

from typing import Any, Mapping

from . import observability_logger


PRIMARY_SCHEMA_VERSION = "3.0.0"

# Active Event Schema v3 names these as migration-adapter-only.  They remain in
# the runtime schema for bounded historical compatibility while R-021 migrates
# readers, but they are not valid primary names for newly migrated v3 writers.
LEGACY_COMPAT_EVENT_TYPES = frozenset(
    {
        "decision",
        "signal_event",
        "tier_publish",
        "tier_reset",
    }
)

PRIMARY_V3 = "PRIMARY_V3"
LEGACY_COMPAT = "LEGACY_COMPAT"
HISTORICAL_SCHEMA = "HISTORICAL_SCHEMA"
INVALID_EVENT_IDENTITY = "INVALID_EVENT_IDENTITY"


class EventSchemaMigrationError(ValueError):
    """Raised when a current v3 write path attempts to use migration-only identity."""


def classify_event_identity(event: Mapping[str, Any]) -> str:
    """Classify an event without mutating or upgrading its historical identity.

    Precedence is intentional:
    - explicit legacy event families remain LEGACY_COMPAT even when a historical
      producer happened to stamp schema_version 3.0.0;
    - non-v3 schema versions remain HISTORICAL_SCHEMA and are never silently
      promoted merely because their event_type also exists in v3;
    - only schema_version 3.0.0 + a non-legacy event family is PRIMARY_V3.
    """

    if not isinstance(event, Mapping):
        return INVALID_EVENT_IDENTITY

    event_type = event.get("event_type")
    schema_version = event.get("schema_version")
    if not isinstance(event_type, str) or not event_type.strip():
        return INVALID_EVENT_IDENTITY
    if not isinstance(schema_version, str) or not schema_version.strip():
        return INVALID_EVENT_IDENTITY

    normalized_type = event_type.strip()
    normalized_version = schema_version.strip()

    if normalized_type in LEGACY_COMPAT_EVENT_TYPES:
        return LEGACY_COMPAT
    if normalized_version != PRIMARY_SCHEMA_VERSION:
        return HISTORICAL_SCHEMA
    return PRIMARY_V3


def require_primary_v3_event_type(event_type: str) -> str:
    """Validate one event_type for a current primary-v3 producer.

    This guard intentionally does not alter observability_logger yet.  During
    R-021 it can be adopted producer-by-producer, allowing historical readers to
    remain intact until their migration is separately proven.
    """

    normalized = str(event_type or "").strip()
    if not normalized:
        raise EventSchemaMigrationError("primary v3 event_type is required")
    if normalized in LEGACY_COMPAT_EVENT_TYPES:
        raise EventSchemaMigrationError(
            f"legacy compatibility event_type cannot be used by a primary v3 writer: {normalized}"
        )
    if normalized not in observability_logger.supported_event_types():
        raise EventSchemaMigrationError(f"unsupported primary v3 event_type: {normalized}")
    return normalized


def is_legacy_compat_event_type(event_type: Any) -> bool:
    return isinstance(event_type, str) and event_type.strip() in LEGACY_COMPAT_EVENT_TYPES


def legacy_compat_event_types() -> tuple[str, ...]:
    """Return the bounded compatibility inventory in deterministic order."""

    return tuple(sorted(LEGACY_COMPAT_EVENT_TYPES))

"""Bounded Event Schema v3 migration helpers.

R-021 separates current write authority from historical compatibility. This
module does not rewrite event records and does not infer newer truth from older
evidence. It classifies event identity, exposes a v3-only construction surface,
and retains an explicit validation surface for canonical historical records.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from . import observability_logger


PRIMARY_SCHEMA_VERSION = "3.0.0"

# Active Event Schema v3 names these as migration-adapter-only. They remain in
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
    """Raised when event identity violates the bounded migration contract."""


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
    """Validate one event_type for a current primary-v3 producer."""

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


def build_primary_v3_event(
    event_type: str,
    data: Dict[str, Any],
    *,
    source: Optional[Dict[str, Any]] = None,
    correlation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one new-runtime event through the primary-v3 write authority.

    The v3 identity is set explicitly instead of inheriting an environment
    override.  Legacy-only event families are rejected before construction.
    This function does not change the lower-level historical validator because
    canonical v2 records must remain readable under their original identity.
    """

    normalized_type = require_primary_v3_event_type(event_type)
    event = observability_logger.build_event(
        normalized_type,
        data,
        source=source,
        correlation=correlation,
    )
    event["schema_version"] = PRIMARY_SCHEMA_VERSION
    validated = observability_logger.validate_event(event)
    if classify_event_identity(validated) != PRIMARY_V3:
        raise EventSchemaMigrationError(
            f"primary v3 builder produced non-primary identity: {normalized_type}"
        )
    return validated


def validate_historical_event(event: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a canonical stored event without rewriting its original identity.

    This is a read/compatibility surface, not a migration writer.  The returned
    dictionary is a copy; ``event_type`` and ``schema_version`` are preserved
    exactly.  Invalid/missing identity remains invalid rather than being inferred.
    """

    if not isinstance(event, Mapping):
        raise EventSchemaMigrationError("historical event must be a mapping")
    candidate = dict(event)
    classification = classify_event_identity(candidate)
    if classification == INVALID_EVENT_IDENTITY:
        raise EventSchemaMigrationError("historical event has invalid identity")
    validated = observability_logger.validate_event(candidate)
    if validated.get("event_type") != event.get("event_type"):
        raise EventSchemaMigrationError("historical validation changed event_type")
    if validated.get("schema_version") != event.get("schema_version"):
        raise EventSchemaMigrationError("historical validation changed schema_version")
    return validated


def is_legacy_compat_event_type(event_type: Any) -> bool:
    return isinstance(event_type, str) and event_type.strip() in LEGACY_COMPAT_EVENT_TYPES


def legacy_compat_event_types() -> tuple[str, ...]:
    """Return the bounded compatibility inventory in deterministic order."""

    return tuple(sorted(LEGACY_COMPAT_EVENT_TYPES))

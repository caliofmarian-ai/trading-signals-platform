"""Data-driven operational memory for Telegram control surfaces.

Explanatory content lives in a versioned JSON registry. This module owns only
schema validation, immutable access, routing aliases, and presentation. It
never owns or invents runtime, strategy, execution, distribution, analytics,
permission, or governance truth.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence


REGISTRY_SCHEMA_VERSION = "1.0.0"
REGISTRY_PATH_ENV = "OWNER_KNOWLEDGE_REGISTRY_PATH"
_SEND_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_REGISTRY_PATH = _SEND_DIR / "config" / "owner_knowledge_registry.json"


class KnowledgeRegistryError(ValueError):
    """Raised when the declarative knowledge registry is missing or invalid."""


@dataclass(frozen=True)
class KnowledgeEntry:
    """Validated, presentation-safe knowledge for one stable human surface."""

    key: str
    title: str
    identity: str
    purpose: str
    pipeline_position: str
    controls: tuple[str, ...]
    consequences: tuple[str, ...]
    limitations: tuple[str, ...]
    canonical_sources: tuple[str, ...]
    glossary: tuple[tuple[str, str], ...] = ()
    public: bool = False
    panel_actions: tuple[str, ...] = ()


def _registry_path() -> Path:
    configured = str(os.getenv(REGISTRY_PATH_ENV) or "").strip()
    if not configured:
        return _DEFAULT_REGISTRY_PATH
    candidate = Path(configured)
    return candidate if candidate.is_absolute() else _SEND_DIR / candidate


def _read_payload(path: Path) -> Mapping[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise KnowledgeRegistryError(f"knowledge registry unavailable: {path}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KnowledgeRegistryError(f"knowledge registry is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise KnowledgeRegistryError("knowledge registry root must be an object")
    return payload


def _required_text(value: Any, *, field: str, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeRegistryError(f"{context}.{field} must be non-empty text")
    return value.strip()


def _text_tuple(
    value: Any,
    *,
    field: str,
    context: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise KnowledgeRegistryError(f"{context}.{field} must be a list")
    items = tuple(
        _required_text(item, field=field, context=f"{context}[{index}]")
        for index, item in enumerate(value)
    )
    if not items and not allow_empty:
        raise KnowledgeRegistryError(f"{context}.{field} must not be empty")
    return items


def _glossary(value: Any, *, context: str) -> tuple[tuple[str, str], ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise KnowledgeRegistryError(f"{context}.glossary must be a list")
    parsed: list[tuple[str, str]] = []
    for index, pair in enumerate(value):
        if not isinstance(pair, list) or len(pair) != 2:
            raise KnowledgeRegistryError(
                f"{context}.glossary[{index}] must contain term and meaning"
            )
        term = _required_text(
            pair[0], field="term", context=f"{context}.glossary[{index}]"
        )
        meaning = _required_text(
            pair[1], field="meaning", context=f"{context}.glossary[{index}]"
        )
        parsed.append((term, meaning))
    return tuple(parsed)


def _entry(raw: Any, *, human_canon: str, index: int) -> KnowledgeEntry:
    context = f"entries[{index}]"
    if not isinstance(raw, dict):
        raise KnowledgeRegistryError(f"{context} must be an object")
    key = _required_text(raw.get("key"), field="key", context=context)
    sources = _text_tuple(
        raw.get("canonical_sources"), field="canonical_sources", context=context
    )
    canonical_sources = tuple(dict.fromkeys((human_canon, *sources)))
    public = raw.get("public", False)
    if not isinstance(public, bool):
        raise KnowledgeRegistryError(f"{context}.public must be boolean")
    return KnowledgeEntry(
        key=key,
        title=_required_text(raw.get("title"), field="title", context=context),
        identity=_required_text(raw.get("identity"), field="identity", context=context),
        purpose=_required_text(raw.get("purpose"), field="purpose", context=context),
        pipeline_position=_required_text(
            raw.get("pipeline_position"), field="pipeline_position", context=context
        ),
        controls=_text_tuple(raw.get("controls"), field="controls", context=context),
        consequences=_text_tuple(
            raw.get("consequences"), field="consequences", context=context
        ),
        limitations=_text_tuple(
            raw.get("limitations"), field="limitations", context=context
        ),
        canonical_sources=canonical_sources,
        glossary=_glossary(raw.get("glossary"), context=context),
        public=public,
        panel_actions=_text_tuple(
            raw.get("panel_actions", []),
            field="panel_actions",
            context=context,
            allow_empty=True,
        ),
    )


def _build_registry(
    payload: Mapping[str, Any],
) -> tuple[str, str, Mapping[str, KnowledgeEntry], Mapping[str, str]]:
    schema_version = _required_text(
        payload.get("schema_version"), field="schema_version", context="registry"
    )
    if schema_version != REGISTRY_SCHEMA_VERSION:
        raise KnowledgeRegistryError(
            f"unsupported knowledge registry schema {schema_version!r}; "
            f"expected {REGISTRY_SCHEMA_VERSION!r}"
        )
    registry_id = _required_text(
        payload.get("registry_id"), field="registry_id", context="registry"
    )
    human_canon = _required_text(
        payload.get("human_comprehension_canon"),
        field="human_comprehension_canon",
        context="registry",
    )
    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise KnowledgeRegistryError("registry.entries must be a non-empty list")

    entries: dict[str, KnowledgeEntry] = {}
    for index, raw in enumerate(raw_entries):
        item = _entry(raw, human_canon=human_canon, index=index)
        if item.key in entries:
            raise KnowledgeRegistryError(f"duplicate knowledge key: {item.key}")
        entries[item.key] = item

    raw_aliases = payload.get("aliases", {})
    if not isinstance(raw_aliases, dict):
        raise KnowledgeRegistryError("registry.aliases must be an object")
    aliases: dict[str, str] = {}
    for raw_alias, raw_target in raw_aliases.items():
        alias = _required_text(
            raw_alias, field="alias", context="registry.aliases"
        )
        target = _required_text(
            raw_target, field="target", context=f"registry.aliases.{alias}"
        )
        if target not in entries:
            raise KnowledgeRegistryError(
                f"alias {alias!r} targets unknown key {target!r}"
            )
        if alias in entries:
            raise KnowledgeRegistryError(f"alias duplicates canonical key: {alias}")
        aliases[alias] = target

    return (
        registry_id,
        human_canon,
        MappingProxyType(entries),
        MappingProxyType(aliases),
    )


KNOWLEDGE_REGISTRY_PATH = _registry_path()
(
    KNOWLEDGE_REGISTRY_ID,
    HUMAN_COMPREHENSION_CANON,
    KNOWLEDGE_REGISTRY,
    _ALIASES,
) = _build_registry(_read_payload(KNOWLEDGE_REGISTRY_PATH))


def normalize_key(key: object) -> str:
    normalized = str(key or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _ALIASES.get(normalized, normalized)


def get_knowledge(key: object) -> Optional[KnowledgeEntry]:
    return KNOWLEDGE_REGISTRY.get(normalize_key(key))


def knowledge_keys() -> tuple[str, ...]:
    return tuple(KNOWLEDGE_REGISTRY)


def render_operational_summary(key: object) -> str:
    entry = get_knowledge(key)
    if entry is None:
        return ""
    return "\n".join(
        [
            f"What this is: {entry.identity}",
            f"Why it exists: {entry.purpose}",
            f"Important: {entry.limitations[0]}",
        ]
    )


def render_operational_page(
    key: object,
    current_state: object,
    *,
    title: Optional[str] = None,
) -> str:
    entry = get_knowledge(key)
    body = (
        str(current_state or "").strip()
        or "No current evidence is available on this surface."
    )
    if entry is None:
        clean_title = str(title or "Information").strip()
        return f"{clean_title}\n\n{body}"
    return "\n".join(
        [
            str(title or entry.title).strip(),
            "",
            render_operational_summary(entry.key),
            "",
            "Current state",
            body,
        ]
    )


def _section(title: str, items: Sequence[str]) -> list[str]:
    return [title, *(f"- {item}" for item in items)]


def render_contextual_knowledge(key: object) -> str:
    entry = get_knowledge(key)
    if entry is None:
        return (
            "Knowledge unavailable\n\n"
            "No canonical explanation is registered for this surface."
        )

    lines = [
        f"About: {entry.title}",
        "",
        "What this is",
        entry.identity,
        "",
        "Why it exists",
        entry.purpose,
        "",
        "Where it sits",
        entry.pipeline_position,
        "",
    ]
    lines.extend(_section("Available controls", entry.controls))
    lines.append("")
    lines.extend(_section("Consequences", entry.consequences))
    lines.append("")
    lines.extend(_section("What this does NOT prove", entry.limitations))

    if entry.glossary:
        lines.extend(["", "Key terms"])
        lines.extend(f"- {term}: {meaning}" for term, meaning in entry.glossary)

    lines.extend(["", "Canonical sources"])
    lines.extend(f"- {source}" for source in entry.canonical_sources)
    return "\n".join(lines)


def public_knowledge_key(key: object) -> bool:
    entry = get_knowledge(key)
    return bool(entry and entry.public)

"""Validated catalog of selectable trading-strategy families."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "1.0.0"
CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "strategy_catalog.json"
_ROOT_FIELDS = frozenset({"schema_version", "catalog_id", "selected_strategy_id", "strategies"})
_ENTRY_FIELDS = frozenset({"id", "name", "trade_type", "implementation", "availability", "description"})
_VERSIONED_CANONICAL_SPEC_RE = re.compile(
    r"^[A-Z0-9_]+_v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)(?:\.md)?$"
)


class StrategyCatalogError(ValueError):
    pass


@dataclass(frozen=True)
class StrategyDefinition:
    id: str
    name: str
    trade_type: str
    implementation: str
    availability: str
    description: str

    @property
    def canonical_spec_version(self) -> str | None:
        match = _VERSIONED_CANONICAL_SPEC_RE.fullmatch(self.implementation)
        if match is None:
            return None
        return match.group("version")


@dataclass(frozen=True)
class StrategyCatalog:
    selected_strategy_id: str
    strategies: tuple[StrategyDefinition, ...]

    @property
    def selected(self) -> StrategyDefinition:
        for strategy in self.strategies:
            if strategy.id == self.selected_strategy_id:
                return strategy
        raise StrategyCatalogError("selected strategy is absent from catalog")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StrategyCatalogError(f"{field} must be non-empty text")
    return value.strip()


def load_strategy_catalog(path: Path = CATALOG_PATH) -> StrategyCatalog:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StrategyCatalogError("strategy catalog is unavailable or invalid") from exc
    if not isinstance(payload, dict) or set(payload) != _ROOT_FIELDS:
        raise StrategyCatalogError("strategy catalog root fields are invalid")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise StrategyCatalogError("strategy catalog schema version is unsupported")
    raw_entries = payload.get("strategies")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise StrategyCatalogError("strategy catalog must contain at least one strategy")

    entries = []
    ids = set()
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict) or set(raw) != _ENTRY_FIELDS:
            raise StrategyCatalogError(f"strategy entry {index} fields are invalid")
        entry = StrategyDefinition(
            id=_text(raw.get("id"), f"strategies[{index}].id"),
            name=_text(raw.get("name"), f"strategies[{index}].name"),
            trade_type=_text(raw.get("trade_type"), f"strategies[{index}].trade_type").upper(),
            implementation=_text(raw.get("implementation"), f"strategies[{index}].implementation"),
            availability=_text(raw.get("availability"), f"strategies[{index}].availability").upper(),
            description=_text(raw.get("description"), f"strategies[{index}].description"),
        )
        if entry.id in ids:
            raise StrategyCatalogError("strategy ids must be unique")
        if entry.availability not in {"AVAILABLE", "UNAVAILABLE"}:
            raise StrategyCatalogError("strategy availability is invalid")
        if entry.availability == "AVAILABLE" and entry.canonical_spec_version is None:
            raise StrategyCatalogError(
                f"available strategy {entry.id} must reference a versioned canonical specification"
            )
        if (
            entry.availability == "UNAVAILABLE"
            and entry.implementation != "NOT_IMPLEMENTED"
            and entry.canonical_spec_version is None
        ):
            raise StrategyCatalogError(
                f"unavailable strategy {entry.id} implementation metadata is invalid"
            )
        ids.add(entry.id)
        entries.append(entry)

    catalog = StrategyCatalog(
        selected_strategy_id=_text(payload.get("selected_strategy_id"), "selected_strategy_id"),
        strategies=tuple(entries),
    )
    if catalog.selected.availability != "AVAILABLE":
        raise StrategyCatalogError("selected strategy must be available")
    return catalog


def render_strategy_choice(catalog: StrategyCatalog) -> str:
    selected = catalog.selected
    spec_version = selected.canonical_spec_version
    if spec_version is None:
        raise StrategyCatalogError("selected strategy canonical specification is not versioned")
    planned = [strategy for strategy in catalog.strategies if strategy.availability != "AVAILABLE"]
    lines = [
        "Choose Strategy",
        "",
        "Current selection",
        f"Selected: {selected.name}",
        f"Trading type: {selected.trade_type}",
        f"Canonical specification: {selected.implementation}",
        f"Canonical specification version: {spec_version}",
        "Status: AVAILABLE",
        "",
        "Plain-language meaning",
        "Binary Trading is currently the only installed trading-strategy family.",
        "Only strategies marked AVAILABLE can be selected.",
        "Choosing a strategy does not enable broker execution or guarantee a winning trade.",
    ]
    if planned:
        lines.extend(["", "Future objectives"])
        lines.extend(
            f"{strategy.name}: NOT AVAILABLE YET — {strategy.description}"
            for strategy in planned
        )
    return "\n".join(lines)


def render_future_forex(catalog: StrategyCatalog) -> str:
    forex = next((item for item in catalog.strategies if item.id == "forex_future"), None)
    if forex is None:
        raise StrategyCatalogError("future Forex strategy is absent from catalog")
    return "\n".join([
        "Forex Strategy",
        "",
        "Current state",
        "Availability: NOT AVAILABLE YET",
        "Selection: BLOCKED",
        "",
        "Plain-language meaning",
        "Forex Strategy is the next planned strategy family after Binary Trading is completed.",
        "It will be researched for Forex positions and separately governed copy-trading use cases.",
        "No Forex decision logic, broker connection, account action, or copy-trading action is enabled here.",
        "It can become selectable only after research, implementation, testing, and Owner approval.",
    ])

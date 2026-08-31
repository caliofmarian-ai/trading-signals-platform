from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SEND_DIR = ROOT / "send"
if str(SEND_DIR) not in sys.path:
    sys.path.insert(0, str(SEND_DIR))

from core import telegram_admin_ui, telegram_app_nav
from core.owner_knowledge import (
    HUMAN_COMPREHENSION_CANON,
    KNOWLEDGE_REGISTRY,
    KNOWLEDGE_REGISTRY_PATH,
    REGISTRY_SCHEMA_VERSION,
    get_knowledge,
    public_knowledge_key,
    render_contextual_knowledge,
    render_operational_page,
)
from core.role_constants import (
    ROLE_AFFILIATE_ADMIN,
    ROLE_ANALYST,
    ROLE_OWNER,
    ROLE_STRATEGY_ADMIN,
    ROLE_USER,
)


EXPECTED_KNOWLEDGE_KEYS = {
    "home",
    "status",
    "help",
    "admin_home",
    "operations",
    "engine",
    "strategy",
    "strategy_selection",
    "thresholds",
    "sr_corridor",
    "spike_filter",
    "symbols_coverage",
    "decision_visibility",
    "distribution",
    "research_analytics",
    "intelligence",
    "affiliate",
    "roles_identity",
    "files_reports",
    "governance_docs",
    "diagnostics",
    "system_health",
    "security_audit",
}


def _callbacks(markup: dict) -> list[str]:
    return [
        button.get("callback_data", "")
        for row in markup.get("inline_keyboard", [])
        for button in row
    ]


def test_registry_covers_every_stable_owner_surface():
    assert EXPECTED_KNOWLEDGE_KEYS == set(KNOWLEDGE_REGISTRY)


def test_explanatory_content_is_declarative_not_embedded_in_python():
    payload = json.loads(KNOWLEDGE_REGISTRY_PATH.read_text(encoding="utf-8"))
    module_source = (SEND_DIR / "core" / "owner_knowledge.py").read_text(encoding="utf-8")

    assert payload["schema_version"] == REGISTRY_SCHEMA_VERSION
    assert {entry["key"] for entry in payload["entries"]} == EXPECTED_KNOWLEDGE_KEYS
    for entry in payload["entries"]:
        for field in ("identity", "purpose", "pipeline_position"):
            assert entry[field] not in module_source


def test_registry_schema_rejects_unversioned_operational_fields():
    from core.owner_knowledge import KnowledgeRegistryError, _build_registry

    root_payload = json.loads(KNOWLEDGE_REGISTRY_PATH.read_text(encoding="utf-8"))
    root_payload["live_runtime_state"] = "READY"
    with pytest.raises(KnowledgeRegistryError, match="unsupported fields"):
        _build_registry(root_payload)

    entry_payload = json.loads(KNOWLEDGE_REGISTRY_PATH.read_text(encoding="utf-8"))
    entry_payload["entries"][0]["current_value"] = "HEALTHY"
    with pytest.raises(KnowledgeRegistryError, match="unsupported fields"):
        _build_registry(entry_payload)


def test_every_entry_fulfils_the_common_comprehension_contract():
    for key, entry in KNOWLEDGE_REGISTRY.items():
        assert entry.key == key
        assert entry.title.strip()
        assert entry.identity.strip()
        assert entry.purpose.strip()
        assert entry.pipeline_position.strip()
        assert entry.controls
        assert entry.consequences
        assert entry.limitations
        assert HUMAN_COMPREHENSION_CANON in entry.canonical_sources


def test_every_canonical_source_is_active_and_materialized():
    active = Path("send/docs/canonical/active")
    for entry in KNOWLEDGE_REGISTRY.values():
        for source in entry.canonical_sources:
            assert "/" not in source, source
            assert "deprecated" not in source.lower(), source
            assert "proposed" not in source.lower(), source
            assert (active / source).is_file(), (entry.key, source)


def test_contextual_pages_expose_required_sections_and_fit_telegram_limit():
    required_sections = (
        "What this is",
        "Why it exists",
        "Where it sits",
        "Available controls",
        "Consequences",
        "What this does NOT prove",
        "Canonical sources",
    )
    for key in KNOWLEDGE_REGISTRY:
        text = render_contextual_knowledge(key)
        assert len(text) < 4096, key
        for section in required_sections:
            assert section in text, (key, section)


def test_operational_page_separates_definition_from_current_state():
    text = render_operational_page("engine", "Running: True", title="Engine Panel")
    assert text.startswith("Engine Panel")
    assert "What this is:" in text
    assert "Why it exists:" in text
    assert "Important:" in text
    assert "Current state\nRunning: True" in text


def test_missing_runtime_evidence_is_never_presented_as_healthy_or_ready(
    monkeypatch: pytest.MonkeyPatch,
):
    from core import bot_service, operational_snapshot

    monkeypatch.setattr(operational_snapshot.runtime_status, "read_status", lambda: {})

    def unreadable_state():
        raise OSError("state unavailable")

    monkeypatch.setattr(operational_snapshot.fsm_runtime, "load_state", unreadable_state)
    for name in ("ENABLE_TELEGRAM", "SHADOW_MODE", "ENABLE_BROKER_EXECUTION"):
        monkeypatch.delenv(name, raising=False)

    snapshot = bot_service._build_status_snapshot()

    assert snapshot["overall_state"].startswith("UNKNOWN")
    assert snapshot["runtime_phase"].startswith("UNKNOWN")
    assert snapshot["recovery_state"].startswith("UNKNOWN")
    assert snapshot["market_data_state"].startswith("UNKNOWN")
    assert snapshot["telegram_state"].startswith("UNKNOWN")
    assert snapshot["fsm_state"].startswith("UNAVAILABLE")
    assert snapshot["shadow_mode"].startswith("UNKNOWN")
    assert snapshot["broker_state"].startswith("DISABLED")
    assert snapshot["broker_state"].endswith("configuration absent)")
    assert "HEALTHY" not in snapshot.values()
    assert "READY" not in snapshot.values()


def test_partial_runtime_evidence_cannot_claim_overall_ready(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import operational_snapshot

    monkeypatch.setattr(
        operational_snapshot.fsm_runtime,
        "STATE_PATH",
        str(tmp_path / "missing_fsm_state.json"),
    )
    for name in ("ENABLE_TELEGRAM", "SHADOW_MODE", "ENABLE_BROKER_EXECUTION"):
        monkeypatch.delenv(name, raising=False)

    partial = operational_snapshot.build_status_snapshot(
        {"phase": "RUNNING", "recovery_required": False}
    )
    complete = operational_snapshot.build_status_snapshot(
        {
            "phase": "RUNNING",
            "recovery_required": False,
            "market_data_state": "READY",
        }
    )

    assert partial["market_data_state"].startswith("UNKNOWN")
    assert partial["overall_state"].startswith("UNKNOWN")
    assert complete["overall_state"].startswith("READY")


def test_missing_fsm_artifact_is_not_presented_as_default_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import operational_snapshot

    state_path = tmp_path / "missing_focus_state.json"
    monkeypatch.setattr(
        operational_snapshot.fsm_runtime,
        "STATE_PATH",
        str(state_path),
    )

    projected = operational_snapshot._fsm_projection()

    assert projected.startswith("UNAVAILABLE")
    assert "WIDE_SCAN" not in projected
    assert "watchlist=0" not in projected


def test_incomplete_fsm_artifact_is_not_normalized_into_observed_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import operational_snapshot

    state_path = tmp_path / "focus_state.json"
    state_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        operational_snapshot.fsm_runtime,
        "STATE_PATH",
        str(state_path),
    )

    projected = operational_snapshot._fsm_projection()

    assert projected.startswith("UNAVAILABLE")
    assert "WIDE_SCAN" not in projected
    assert "watchlist=0" not in projected


def test_engine_tick_interval_requires_reported_runtime_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import operational_snapshot

    monkeypatch.setattr(
        operational_snapshot.fsm_runtime,
        "STATE_PATH",
        str(tmp_path / "missing_focus_state.json"),
    )

    missing = operational_snapshot.build_status_snapshot({})
    reported = operational_snapshot.build_status_snapshot(
        {"engine_tick_seconds": 2}
    )
    invalid = operational_snapshot.build_status_snapshot(
        {"engine_tick_seconds": float("nan")}
    )

    assert missing["engine_tick_seconds"].startswith("UNKNOWN")
    assert reported["engine_tick_seconds"] == (
        "2 seconds (reported runtime evidence)"
    )
    assert invalid["engine_tick_seconds"].startswith("UNAVAILABLE")


def test_invalid_runtime_scalar_types_remain_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import operational_snapshot

    monkeypatch.setattr(
        operational_snapshot.fsm_runtime,
        "STATE_PATH",
        str(tmp_path / "missing_focus_state.json"),
    )
    snapshot = operational_snapshot.build_status_snapshot(
        {
            "phase": [],
            "market_data_state": {},
            "overall_state": ["READY"],
            "recovery_state": 123,
            "broker_state": True,
            "engine_tick_seconds": "not-a-number",
        }
    )

    for key in (
        "overall_state",
        "runtime_phase",
        "market_data_state",
        "recovery_state",
        "broker_state",
        "engine_tick_seconds",
    ):
        assert snapshot[key].startswith("UNAVAILABLE"), (key, snapshot[key])
    assert "READY" not in snapshot["overall_state"]


def test_missing_operational_artifacts_do_not_become_zero_or_empty_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import admin_commands, admin_views

    missing_root = tmp_path / "missing"
    monkeypatch.setattr(
        admin_commands,
        "ENGINE_EVENTS_PATH",
        str(missing_root / "engine_events.jsonl"),
    )
    monkeypatch.setattr(
        admin_commands,
        "ACTIVE_SYMBOLS_PATH",
        str(missing_root / "active_symbols.json"),
    )
    monkeypatch.setattr(admin_commands, "REPORTS_DIR", str(missing_root / "reports"))
    monkeypatch.setattr(
        admin_commands,
        "build_status_snapshot",
        lambda: {
            "runtime_phase": "UNKNOWN (not reported)",
            "engine_tick_seconds": "UNKNOWN (not reported)",
        },
    )

    engine = admin_commands._engine_status()
    symbols = admin_commands._load_active_symbols_observation()
    report = admin_commands._report_summary()

    assert engine["tick_interval"].startswith("UNKNOWN")
    assert engine["decision_count"].startswith("UNAVAILABLE")
    assert engine["decision_count"] != 0
    assert symbols is None
    assert report["availability"].startswith("UNAVAILABLE")
    assert "UNAVAILABLE" in admin_views.render_symbols(symbols)
    assert "UNAVAILABLE" in admin_views.render_report_summary(report)


def test_explicit_empty_artifacts_remain_distinct_from_missing_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import admin_commands

    engine_events = tmp_path / "engine_events.jsonl"
    active_symbols = tmp_path / "active_symbols.json"
    reports_dir = tmp_path / "reports"
    report_path = reports_dir / "daily_strategy_audit_20260830.json"
    engine_events.write_text("", encoding="utf-8")
    active_symbols.write_text("[]", encoding="utf-8")
    reports_dir.mkdir()
    report_path.write_text(
        json.dumps(
            {
                "date": "2026-08-30",
                "decisions": 0,
                "rejects": 0,
                "pre": 0,
                "confirm": 0,
                "open_now": 0,
                "avg_score": 0,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(admin_commands, "ENGINE_EVENTS_PATH", str(engine_events))
    monkeypatch.setattr(admin_commands, "ACTIVE_SYMBOLS_PATH", str(active_symbols))
    monkeypatch.setattr(admin_commands, "REPORTS_DIR", str(reports_dir))
    monkeypatch.setattr(
        admin_commands,
        "build_status_snapshot",
        lambda: {
            "runtime_phase": "RUNNING",
            "engine_tick_seconds": "2 seconds (reported runtime evidence)",
        },
    )

    engine = admin_commands._engine_status()
    report = admin_commands._report_summary()

    assert engine["decision_count"] == 0
    assert admin_commands._load_active_symbols_observation() == []
    assert report["availability"].startswith("AVAILABLE")
    assert report["decisions"] == 0


def test_invalid_symbol_members_do_not_become_fabricated_symbols(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import admin_commands

    path = tmp_path / "active_symbols.json"
    monkeypatch.setattr(admin_commands, "ACTIVE_SYMBOLS_PATH", str(path))

    path.write_text(json.dumps([None, 42, {"bad": True}]), encoding="utf-8")
    assert admin_commands._load_active_symbols_observation() is None

    path.write_text(json.dumps({"forex": ["EUR/USD"], "crypto": [7]}), encoding="utf-8")
    assert admin_commands._load_active_symbols_observation() is None

    path.write_text(json.dumps({"forex": ["EUR/USD"], "crypto": []}), encoding="utf-8")
    assert admin_commands._load_active_symbols_observation() == ["EUR/USD"]


def test_decision_and_intelligence_views_distinguish_missing_from_empty_logs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import admin_commands, admin_views, bot_service

    path = tmp_path / "engine_events.jsonl"
    monkeypatch.setattr(admin_commands, "ENGINE_EVENTS_PATH", str(path))

    missing = admin_commands._decision_debug_observation()
    assert missing["availability"].startswith("UNAVAILABLE")
    assert "UNAVAILABLE" in admin_views.render_debug_last(
        missing["event"], availability=missing["availability"]
    )
    assert bot_service._iter_recent_engine_events() is None
    assert "UNAVAILABLE" in admin_views.render_intelligence_panel(None)

    path.write_text("", encoding="utf-8")
    empty = admin_commands._decision_debug_observation()
    assert empty["availability"].startswith("AVAILABLE")
    assert "available event log" in admin_views.render_debug_last(
        empty["event"], availability=empty["availability"]
    )
    assert bot_service._iter_recent_engine_events() == []
    assert "available event log" in admin_views.render_intelligence_panel([])


def test_strategy_profile_does_not_call_missing_configuration_custom(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    from core import admin_commands

    monkeypatch.setattr(
        admin_commands,
        "_algo_params_path",
        lambda: str(tmp_path / "missing_algo_params.json"),
    )
    assert admin_commands.get_current_strategy_profile_observation().startswith(
        "UNAVAILABLE"
    )

    monkeypatch.setattr(
        admin_commands,
        "_algo_params_path",
        lambda: str(SEND_DIR / "config" / "algo_params.json"),
    )
    assert admin_commands.get_current_strategy_profile_observation().startswith(
        "CUSTOM"
    )


def test_welcome_page_does_not_invent_a_shadow_mode_default():
    text, _ = telegram_app_nav.render_welcome_page(1, ROLE_USER)
    assert "Mode: UNKNOWN" in text
    assert "Shadow mode is disabled" not in text


def test_only_public_knowledge_is_available_through_app_navigation():
    assert public_knowledge_key("home")
    assert public_knowledge_key("status")
    assert public_knowledge_key("help")
    assert not public_knowledge_key("strategy")
    assert not public_knowledge_key("security_audit")


@pytest.mark.parametrize(
    ("renderer", "expected_key"),
    [
        (lambda: telegram_admin_ui.admin_home_markup(role=ROLE_OWNER), "admin_home"),
        (telegram_admin_ui.operations_markup, "operations"),
        (telegram_admin_ui.decision_visibility_markup, "decision_visibility"),
        (telegram_admin_ui.strategy_choice_markup, "strategy_selection"),
        (telegram_admin_ui.distribution_markup, "distribution"),
        (telegram_admin_ui.research_markup, "research_analytics"),
        (telegram_admin_ui.intelligence_markup, "intelligence"),
        (telegram_admin_ui.affiliate_markup, "affiliate"),
        (telegram_admin_ui.roles_identity_markup, "roles_identity"),
        (telegram_admin_ui.system_health_markup, "system_health"),
        (lambda: telegram_admin_ui.governance_docs_markup([]), "governance_docs"),
        (telegram_admin_ui.security_audit_markup, "security_audit"),
    ],
)
def test_every_admin_root_panel_exposes_contextual_knowledge(renderer, expected_key):
    callbacks = _callbacks(renderer())
    assert any(cb.startswith(f"ADMIN_NAV:INFO:{expected_key}:") for cb in callbacks)


@pytest.mark.parametrize(
    ("key", "action"),
    [
        ("thresholds", "THRESHOLDS"),
        ("sr_corridor", "SR"),
        ("spike_filter", "SPIKE"),
    ],
)
def test_parameter_pages_link_to_their_own_semantic_explanation(key, action):
    callbacks = _callbacks(telegram_admin_ui.strategy_parameter_markup(key, action))
    assert f"ADMIN_NAV:INFO:{key}:{action}" in callbacks


def test_knowledge_return_action_cannot_be_turned_into_a_mutation():
    markup = telegram_admin_ui.knowledge_detail_markup("PROFILE_EXEC:AGGRESSIVE")
    assert _callbacks(markup) == ["ADMIN_NAV:HOME"]


def test_file_knowledge_return_keeps_only_allowlisted_read_navigation():
    safe = telegram_admin_ui.knowledge_detail_markup("FILES:obs:2")
    unsafe = telegram_admin_ui.knowledge_detail_markup("FILES:../../secret:2")
    assert _callbacks(safe) == ["ADMIN_NAV:FILES:obs:2"]
    assert _callbacks(unsafe) == ["ADMIN_NAV:HOME"]


def test_role_aware_knowledge_does_not_expand_panel_visibility():
    assert telegram_admin_ui.knowledge_visible_for_role(ROLE_OWNER, "security_audit")
    assert telegram_admin_ui.knowledge_visible_for_role(ROLE_AFFILIATE_ADMIN, "affiliate")
    assert not telegram_admin_ui.knowledge_visible_for_role(ROLE_AFFILIATE_ADMIN, "strategy")
    assert not telegram_admin_ui.knowledge_visible_for_role(
        ROLE_AFFILIATE_ADMIN, "strategy_selection"
    )
    assert telegram_admin_ui.knowledge_visible_for_role(ROLE_ANALYST, "research_analytics")
    assert not telegram_admin_ui.knowledge_visible_for_role(ROLE_ANALYST, "symbols_coverage")
    assert telegram_admin_ui.knowledge_visible_for_role(ROLE_STRATEGY_ADMIN, "thresholds")
    assert not telegram_admin_ui.knowledge_visible_for_role(ROLE_USER, "admin_home")


def test_public_pages_expose_discoverable_information_buttons():
    home_text, home_markup = telegram_app_nav.render_welcome_page(1, ROLE_USER)
    status_text, status_markup = telegram_app_nav.render_status_page({})
    help_text, help_markup = telegram_app_nav.render_help_page(ROLE_USER)

    assert "What this is:" in home_text
    assert "What this is:" in status_text
    assert "What this is:" in help_text
    assert any("INFO:home" in cb for cb in _callbacks(home_markup))
    assert any("INFO:status" in cb for cb in _callbacks(status_markup))
    assert any("INFO:help" in cb for cb in _callbacks(help_markup))


def test_app_information_page_is_navigable_and_rejects_admin_key():
    text, markup = telegram_app_nav.handle_app_action(
        telegram_app_nav.make_info_action("status"),
        user_id=101,
        primary_role=ROLE_USER,
        chat_id=101,
    )
    assert text.startswith("About: System Status")
    assert "APP:HOME" in _callbacks(markup)

    rejected_text, _ = telegram_app_nav.handle_app_action(
        telegram_app_nav.make_info_action("security_audit"),
        user_id=101,
        primary_role=ROLE_USER,
        chat_id=101,
    )
    assert "About: Security and Audit" not in rejected_text
    assert "BinaryBot" in rejected_text


def test_admin_information_handler_is_role_scoped(monkeypatch: pytest.MonkeyPatch):
    from core import bot_service

    message = {"chat": {"id": 1, "type": "private"}}
    monkeypatch.setattr(bot_service, "is_owner", lambda _user_id: False)

    monkeypatch.setattr(bot_service, "get_primary_role", lambda _user_id: ROLE_OWNER)
    allowed = bot_service._handle_admin_navigation_action(
        "INFO:strategy:STRATEGY",
        1,
        message,
    )
    assert allowed["text"].startswith("About: Strategy Parameters")
    assert _callbacks(allowed["reply_markup"]) == ["ADMIN_NAV:STRATEGY"]

    monkeypatch.setattr(bot_service, "get_primary_role", lambda _user_id: ROLE_AFFILIATE_ADMIN)
    denied = bot_service._handle_admin_navigation_action(
        "INFO:strategy:STRATEGY",
        1,
        message,
    )
    assert "unavailable" in denied["text"].lower()


def test_admin_home_replaces_flat_command_dump_with_role_scoped_navigation(
    monkeypatch: pytest.MonkeyPatch,
):
    from core import bot_service

    monkeypatch.setattr(bot_service, "get_primary_role", lambda _user_id: ROLE_OWNER)
    monkeypatch.setattr(
        bot_service,
        "handle_admin_command_v2",
        lambda _command, _user_id: (
            "BinaryBot Admin Panel\n\n"
            "Primary role: OWNER\n"
            "All roles: OWNER\n\n"
            "Available commands:\n"
            "/strategy\n/roles_reload"
        ),
    )

    text, markup = bot_service._build_canonical_admin_root_page(
        1,
        owner_private=True,
    )

    assert "Available commands:" not in text
    assert "/roles_reload" not in text
    assert "buttons below are filtered to the current role" in text
    assert "ADMIN_NAV:OPERATIONS" in _callbacks(markup)
    assert "ADMIN_NAV:INFO:admin_home:HOME" in _callbacks(markup)


def test_contextual_callback_payloads_fit_telegram_limit():
    renderers = [
        telegram_admin_ui.admin_home_markup(role=ROLE_OWNER),
        telegram_admin_ui.operations_markup(),
        telegram_admin_ui.strategy_parameter_markup("thresholds", "THRESHOLDS"),
        telegram_admin_ui.symbols_toggle_markup(["EURUSD"], ["EURUSD"]),
        telegram_admin_ui.decision_visibility_markup(),
        telegram_admin_ui.distribution_markup(),
        telegram_admin_ui.research_markup(),
        telegram_admin_ui.intelligence_markup(),
        telegram_admin_ui.affiliate_markup(),
        telegram_admin_ui.roles_identity_markup(),
        telegram_admin_ui.system_health_markup(),
        telegram_admin_ui.governance_docs_markup([]),
        telegram_admin_ui.security_audit_markup(),
    ]
    info_callbacks = [
        callback
        for markup in renderers
        for callback in _callbacks(markup)
        if callback.startswith("ADMIN_NAV:INFO:")
    ]
    assert info_callbacks
    assert all(len(callback.encode("utf-8")) <= 64 for callback in info_callbacks)


def test_public_information_callback_preserves_single_message_navigation(monkeypatch: pytest.MonkeyPatch):
    from core import bot_service

    nav = bot_service.telegram_app_nav
    chat_id = 5511
    user_id = 5511
    message_id = 9911
    generation = nav.begin_navigation_generation(chat_id, user_id)
    nav.set_active_message(user_id, chat_id, message_id)

    sends: list[dict] = []
    edits: list[dict] = []

    monkeypatch.setattr(bot_service, "get_primary_role", lambda _user_id: ROLE_USER)
    monkeypatch.setattr(
        bot_service.telegram_publisher,
        "send_message",
        lambda *args, **kwargs: sends.append({"args": args, "kwargs": kwargs}),
    )
    monkeypatch.setattr(
        bot_service.telegram_publisher,
        "edit_message",
        lambda chat_id, message_id, text, reply_markup=None: edits.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            }
        ),
    )

    bot_service.process_update(
        {
            "callback_query": {
                "from": {"id": user_id},
                    "data": nav.make_callback(
                        nav.make_info_action("status"),
                    generation=generation,
                ),
                "message": {
                    "chat": {"id": chat_id, "type": "private"},
                    "message_id": message_id,
                    "text": "previous page",
                },
            }
        }
    )

    assert sends == []
    assert len(edits) == 1
    assert edits[0]["message_id"] == message_id
    assert edits[0]["text"].startswith("About: System Status")


def test_aliases_do_not_duplicate_canonical_entries():
    assert get_knowledge("symbols") is KNOWLEDGE_REGISTRY["symbols_coverage"]
    assert get_knowledge("sr") is KNOWLEDGE_REGISTRY["sr_corridor"]
    assert get_knowledge("audit") is KNOWLEDGE_REGISTRY["security_audit"]

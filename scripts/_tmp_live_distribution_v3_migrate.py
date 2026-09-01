from pathlib import Path
import json

BRANCH_WORKFLOW = Path('.github/workflows/live-distribution-v3-migrate.yml')
SELF = Path('scripts/_tmp_live_distribution_v3_migrate.py')


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one match, found {count}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


replace_once(
    'send/core/observability_logger.py',
    'SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "2.0.0")',
    'SCHEMA_VERSION = os.getenv("EVENT_SCHEMA_VERSION", "3.0.0")',
)
replace_once(
    'send/state_store/state_store.py',
    'if state not in {"ACTIVE", "SILENT"}:',
    'if state not in {"ACTIVE", "SILENT", "DISABLED"}:',
)
replace_once(
    'send/core/distribution_router.py',
    '"FREE": 5,',
    '"FREE": 6,',
)
replace_once(
    'send/core/outcome_service.py',
    'VOTE_WINDOW_GRACE_SECONDS = 5 * 60',
    'VOTE_WINDOW_GRACE_SECONDS = 10 * 60',
)
replace_once(
    'send/core/outcome_service.py',
    '        "event_type": "user_outcome_record",\n        "signal_id": signal_id,',
    '        "event_type": "user_outcome_record",\n        "record_schema_version": "3.0.0",\n        "truth_source": "COMMUNITY_SELF_REPORT",\n        "signal_id": signal_id,',
)
replace_once(
    'send/core/outcome_service.py',
    '                "outcome": outcome,\n                "policy": "LOCK_FIRST_WRITE_WINS",',
    '                "outcome": outcome,\n                "truth_source": "COMMUNITY_SELF_REPORT",\n                "policy": "LOCK_FIRST_WRITE_WINS",',
)

schema_path = Path('send/schema/event_schema.json')
schema = json.loads(schema_path.read_text(encoding='utf-8'))
schema['event_types']['user_outcome']['data'].setdefault('optional', {})['truth_source'] = {
    'type': 'string',
    'enum': ['COMMUNITY_SELF_REPORT'],
}
schema_path.write_text(
    json.dumps(schema, ensure_ascii=False, separators=(',', ':')) + '\n',
    encoding='utf-8',
)

replace_once(
    'send/core/signal_execution_gate.py',
    'Distribution remains deliberately disabled; therefore a valid candidate is\nclassified as PRE_DISTRIBUTION / DEFERRED, never EMITTED.',
    'A valid exact-stage candidate may authorize Distribution Router invocation.\nThe pre-distribution checkpoint remains DEFERRED and can never claim EMITTED.',
)
replace_once(
    'send/core/signal_execution_gate.py',
    '        if self.distribution_allowed:\n            raise ValueError("distribution cannot be enabled by the pre-distribution execution gate")',
    '        if self.distribution_allowed:\n            if self.candidate is None or not self.stage_handoff_ready:\n                raise ValueError("distribution requires an available handoff-ready candidate")\n            if self.outcome != "DEFERRED":\n                raise ValueError("distribution authorization requires a DEFERRED pre-distribution checkpoint")',
)
replace_once(
    'send/core/signal_execution_gate.py',
    '    candidate: Optional[SignalEvent] = None,\n) -> SignalExecutionGateResult:',
    '    candidate: Optional[SignalEvent] = None,\n    distribution_allowed: bool = False,\n) -> SignalExecutionGateResult:',
)
replace_once(
    'send/core/signal_execution_gate.py',
    '        candidate=candidate,\n        distribution_allowed=False,',
    '        candidate=candidate,\n        distribution_allowed=distribution_allowed,',
)
replace_once(
    'send/core/signal_execution_gate.py',
    '        reason="DISTRIBUTION_NOT_INVOKED",\n        candidate=candidate,\n    )',
    '        reason="DISTRIBUTION_ROUTER_READY",\n        candidate=candidate,\n        distribution_allowed=True,\n    )',
)
replace_once(
    'send/core/signal_execution_gate.py',
    '    """Prepare a traceable exact-stage execution verdict without distribution."""',
    '    """Prepare a traceable exact-stage pre-distribution verdict."""',
)

replace_once(
    'send/core/signal_engine.py',
    'from core import distribution_router  # compatibility surface only; run_once does not invoke routing',
    'from core import distribution_router_v3 as distribution_router',
)
replace_once(
    'send/core/signal_engine.py',
    '    """Run one real-market strategy/FSM/execution-candidate cycle.\n\n    Distribution, Telegram publication, outcome registration and broker execution\n    are intentionally not invoked by this function in the current activation.\n    """',
    '    """Run one real-market strategy/FSM/candidate/distribution cycle.\n\n    Governed SignalEvent candidates may be routed to Telegram. Broker execution\n    remains disabled and is never invoked by this function.\n    """',
)

signal_engine = Path('send/core/signal_engine.py')
text = signal_engine.read_text(encoding='utf-8')
marker = '\n\ndef run_once(now_ts=None, forced_symbols=None, forced_focus_context=None, scheduler_stage=None) -> None:\n'
if text.count(marker) != 1:
    raise SystemExit('signal_engine: run_once marker mismatch')
helper = '''


def _log_post_distribution(decision, persistent_fsm, execution, summary: Dict[str, Any]) -> None:
    published_count = int(summary.get("published_count", 0))
    failed_count = int(summary.get("failed_count", 0))
    blocked = bool(summary.get("blocked"))

    if blocked:
        outcome = "BLOCKED"
        reason = str(summary.get("block_reason") or "DISTRIBUTION_BLOCKED")
        destination_state = "DISTRIBUTION_BLOCKED"
    elif published_count > 0:
        outcome = "EMITTED"
        reason = "AUTHORIZED_PUBLICATION_SUCCEEDED"
        destination_state = "PUBLISHED"
    elif failed_count > 0:
        outcome = "FAILED"
        reason = "ROUTE_PUBLICATION_FAILED"
        destination_state = "ROUTES_EVALUATED_NO_PUBLICATION"
    else:
        outcome = "SKIPPED"
        reason = "NO_AUTHORIZED_ROUTE_PUBLISHED"
        destination_state = "ROUTES_EVALUATED_NO_PUBLICATION"

    decision_dict = decision.to_dict()
    data = {
        "execution_phase": "POST_DISTRIBUTION",
        "execution_outcome": outcome,
        "execution_reason": reason,
        "stage_handoff_ready": execution.stage_handoff_ready,
        "trade_execution_ready": execution.trade_execution_ready,
        "signal_event_available": execution.candidate is not None,
        "destination_state": destination_state,
        "candidate_schema_version": execution.candidate.schema_version if execution.candidate is not None else None,
        "fsm_handoff": {
            "requested_stage": persistent_fsm.requested_stage,
            "accepted_stage": persistent_fsm.accepted_stage,
            "signal_id": persistent_fsm.signal_id,
            "prior_state": persistent_fsm.prior_state,
            "resulting_state": persistent_fsm.resulting_state,
            "state_changed": persistent_fsm.state_changed,
            "reason": persistent_fsm.reason,
            "reason_family": persistent_fsm.reason_family,
            "stage_handoff_ready": persistent_fsm.stage_handoff_ready,
            "trade_execution_ready": persistent_fsm.trade_execution_ready,
        },
        "trade_physics": _trade_physics_dict(decision_dict) or None,
        "publication_evidence": {
            "published": list(summary.get("publication_evidence") or []),
            "route_results": list(summary.get("route_results") or []),
        },
    }
    event = _build_v3_event(
        "signal_execution_result",
        data,
        correlation={
            "execution_attempt_id": execution.execution_attempt_id,
            "setup_correlation_id": execution.setup_correlation_id,
            "signal_id": decision.signal_id,
            "symbol": decision.setup.symbol,
            "timeframe": decision.setup.timeframe,
            "stage": decision.kind,
        },
    )
    observability_logger.log_event(event)
'''
text = text.replace(marker, helper + marker, 1)
signal_engine.write_text(text, encoding='utf-8')

replace_once(
    'send/core/signal_engine.py',
    '                _log_signal_execution(decision, persistent_fsm, execution)\n',
    '''                _log_signal_execution(decision, persistent_fsm, execution)\n                if execution.distribution_allowed and execution.candidate is not None:\n                    try:\n                        distribution_summary = distribution_router.route(\n                            execution.candidate, now_ts=now_ts\n                        )\n                    except Exception as distribution_exc:\n                        observability_logger.log_error(\n                            {\n                                "event_type": "error",\n                                "module": "signal_engine",\n                                "symbol": symbol,\n                                "error": str(distribution_exc),\n                                "trace": "",\n                            }\n                        )\n                        distribution_summary = {\n                            "published_count": 0,\n                            "failed_count": 1,\n                            "skipped_count": 0,\n                            "blocked": False,\n                            "block_reason": None,\n                            "route_results": [],\n                            "publication_evidence": [],\n                        }\n                    _log_post_distribution(\n                        decision, persistent_fsm, execution, distribution_summary\n                    )\n''',
)
replace_once(
    'tests/batch_03/test_distribution_observability_interface_repair.py',
    '        "FREE_LIMIT": 5,',
    '        "FREE_LIMIT": 6,',
)

# Remove the temporary helper artifacts from the final branch commit.
if BRANCH_WORKFLOW.exists():
    BRANCH_WORKFLOW.unlink()
if SELF.exists():
    SELF.unlink()

# MODULE_INTERFACE_SPEC_v3.0.0.md

BinaryBot — Canonical Module Interface and Boundary Specification  
Version: 3.0.0  
Status: PROPOSED CANONICAL REPLACEMENT — OWNER REVIEW REQUIRED  
Proposed Path: `send/docs/canonical/proposed/MODULE_INTERFACE_SPEC_v3.0.0.md`  
Intended Active Path After Promotion: `send/docs/canonical/active/MODULE_INTERFACE_SPEC_v3.0.0.md`  
Owner: BinaryBot / DROPi Signals  
Governance Change: `CHANGE_ID 20260831-01`  
Supersedes upon promotion: `MODULE_INTERFACE_SPEC_v2.0.0.md`

---

## 0. PROPOSAL STATUS AND PRESERVATION RULE

This is a proposed replacement, not active canonical truth.

It preserves all valid v2.0.0 module ownership boundaries, shared data contracts, persistence ownership, Telegram separation, distribution separation, outcome separation, observability ownership and analytics non-mutation rules unless explicitly changed below.

v3.0.0 closes one structural gap: the FSM-to-signal-engine boundary must explicitly tell the signal engine whether PRE, CONFIRM or OPEN_NOW was operationally accepted for canonical SignalEvent construction.

It also aligns the engine-to-distribution SignalEvent contract with the active strategy vocabulary and adds a structured execution-result interface consistent with the proposed event schema.

No code change is authorized until this proposed contract is promoted and re-audited.

---

## 1. GLOBAL BOUNDARY PRINCIPLE

No module may bypass its canonical boundary to:
- read hidden state owned elsewhere;
- inject side effects into another layer;
- duplicate another module's ownership;
- redefine upstream truth;
- infer delivery success from object construction;
- mix strategy, FSM, execution and distribution authority.

The canonical runtime chain remains:

`Market/Strategy -> DecisionObject -> FSM -> FSMExecutionHandoff -> Signal Engine -> SignalEvent / SignalExecutionResult -> Distribution Router -> Publisher -> External Surface`

Observability reads evidence across this chain but does not mutate trading behavior.

---

## 2. PRESERVED SHARED CONTRACTS

The substantive v2.0.0 contracts remain preserved for:
- Candle;
- DecisionObject;
- FSM persistent state;
- DistributionState;
- OutcomeVote;
- EventRecord;
- storage ownership;
- candle normalization;
- parameter loading;
- strategy purity;
- Telegram transport separation;
- outcome service ownership;
- observability logger ownership;
- analytics non-mutation.

The v3 changes below supersede only the interface details that were ambiguous or stale.

---

## 3. `DecisionObject`

The DecisionObject remains the canonical strategy output produced before FSM.

Required semantic families remain:
- decision kind: `NO_SIGNAL | PRE | CONFIRM | OPEN_NOW | REJECT`;
- stable signal identity for actionable stages;
- symbol/timeframe/direction;
- score semantics;
- canonical `buffer_distance` strategic truth;
- timing/expiry semantics;
- gates and explanations;
- candle/evaluation timestamp;
- structured context needed by FSM and audit.

Rules:
1. DecisionObject is produced before FSM.
2. PRE/CONFIRM/OPEN_NOW require a stable `signal_id` for the same trade idea.
3. DecisionObject does not authorize distribution by itself.
4. DecisionObject does not prove FSM acceptance.
5. DecisionObject does not prove external visibility.

---

## 4. `FSMExecutionHandoff` — NEW EXPLICIT CONTRACT

### 4.1 Purpose

`FSMExecutionHandoff` is the canonical post-FSM interface consumed by the signal engine for stage-level execution gating.

It exists because a raw transition event or a boolean such as `accepted` without stage semantics is insufficient to distinguish:
- a real accepted stage;
- a duplicate/suppressed stage;
- cooldown/focus/watchlist blocking;
- identity/lifecycle rejection;
- a non-actionable decision.

### 4.2 Minimum fields

Conceptual contract:

```text
FSMExecutionHandoff
- requested_stage: str | None
- signal_id: str | None
- disposition: str
- accepted_for_signal_event: bool
- reason: str
- state_changed: bool
- transition_event: object | None
- next_state: FSMState or canonical state reference
- created_ts: int
```

Canonical `disposition` values:
- `ACCEPTED`
- `DUPLICATE_SUPPRESSED`
- `BLOCKED`
- `REJECTED`
- `NOT_ACTIONABLE`

### 4.3 Acceptance invariant

`accepted_for_signal_event` may be true only when all of the following hold:
- requested stage is PRE, CONFIRM or OPEN_NOW;
- FSM/lifecycle rules accept that exact stage now;
- signal identity is valid for the lifecycle;
- no cooldown/invariant/policy/focus/watchlist blocker prevents stage release;
- the stage is not a duplicate/suppressed replay;
- any required canonical predecessor/focus condition is satisfied.

If any requirement fails, `accepted_for_signal_event` must be false.

### 4.4 Transition event is not acceptance proof

A transition/suppression event may be produced for reasons such as:
- cooldown active;
- watchlist full;
- duplicate stage/candle;
- focus eviction/replacement;
- invalid lifecycle path;
- invalid signal identity continuity.

Therefore:

`transition_event != None` MUST NOT be interpreted as equivalent to `accepted_for_signal_event=True`.

### 4.5 Required disposition examples

- Valid PRE admitted to watchlist/focus -> `ACCEPTED`, true.
- Valid PRE refresh that canonically represents the same accepted stage but is not a duplicate stage/candle -> `ACCEPTED`, true if stage-release rules permit.
- Same PRE/CONFIRM stage and same governed candle already materialized -> `DUPLICATE_SUPPRESSED`, false.
- PRE blocked because watchlist is full and no valid replacement is allowed -> `BLOCKED`, false.
- PRE/CONFIRM/OPEN_NOW during active cooldown -> `BLOCKED`, false.
- CONFIRM without stable lifecycle identity -> `REJECTED`, false.
- OPEN_NOW without canonical PRE/focus path -> `REJECTED`, false.
- NO_SIGNAL -> `NOT_ACTIONABLE`, false.
- strategic REJECT -> `NOT_ACTIONABLE` or `REJECTED` according to the FSM authority, false in either case.

### 4.6 OPEN_NOW delivery-state rule

FSM acceptance of OPEN_NOW is not proof of successful external delivery.

The pre-distribution FSM boundary must not mark a lifecycle as `LIVE_SENT`, `DELIVERED`, or equivalent merely because OPEN_NOW was accepted or a SignalEvent was constructed.

Any successful-delivery state requires canonical delivery proof at the approved downstream boundary.

---

## 5. `SignalEvent` — CANONICAL ENGINE-TO-DISTRIBUTION OBJECT

### 5.1 Purpose

SignalEvent remains the canonical semantic object produced by the signal engine for a stage that passed the FSM execution-handoff boundary.

It does not itself route, publish, mutate entitlement, register outcomes, or execute a broker trade.

### 5.2 Canonical fields

Conceptual contract:

```text
SignalEvent
- schema_version: str
- event_type: str
- stage: str
- signal_id: str
- symbol: str
- timeframe: str
- direction: str
- score_total: float
- buffer_mode: str
- buffer_distance: float
- expiry_minutes: int
- candle_ts: int
- created_ts: int
- entry_price: float
- payload: object
```

Compatibility-only field:
- `buffer_price` may exist as an explicit legacy alias for `buffer_distance` while migration remains necessary, but it is not the strategic truth.

### 5.3 Stage rule

`stage` must be exactly one of:
- PRE;
- CONFIRM;
- OPEN_NOW.

The SignalEvent stage must equal the exact actionable stage accepted by `FSMExecutionHandoff`.

### 5.4 Stable identity rule

PRE, CONFIRM and OPEN_NOW SignalEvents for the same trade idea must preserve the same governed `signal_id`.

Distribution and retries must not invent a new signal identity.

### 5.5 Construction gate

The signal engine may build a SignalEvent only when:

`handoff.accepted_for_signal_event == True`

A blocked, duplicate-suppressed, rejected or non-actionable handoff must not produce a distribution candidate.

### 5.6 Candidate is not delivery

SignalEvent construction means only:
- an upstream actionable stage was accepted by FSM;
- the signal engine could construct a coherent canonical engine-to-distribution object.

It does not mean:
- distribution was authorized;
- a route was selected;
- Telegram was called;
- a message was delivered;
- entitlement was consumed;
- outcome interaction became eligible;
- broker execution occurred.

---

## 6. `SignalExecutionResult` — NEW EXECUTION-LAYER CONTRACT

### 6.1 Purpose

`SignalExecutionResult` represents the signal engine's execution verdict after FSM and is the source material for the canonical `signal_execution_result` observability event.

It is not strategy truth, FSM truth, or route-level distribution truth.

### 6.2 Minimum fields

Conceptual contract:

```text
SignalExecutionResult
- execution_attempt_id: str
- outcome: str
- reason: str
- signal_id: str | None
- stage: str | None
- created_ts: int
- fsm_handoff_disposition: str
- destination_class: str
- distribution_authorized: bool
- distribution_attempted: bool
- candidate: SignalEvent | None
- payload_reference: object | string | None
```

Execution outcome values:
- `EMITTED`
- `NOT_EMITTED`
- `BLOCKED`
- `SKIPPED`
- `FAILED`
- `DEFERRED`

### 6.3 Trace completeness

The execution result must allow observability to reconstruct:
- execution attempt identity;
- setup/signal correlation;
- outcome;
- reason;
- timestamp;
- destination/channel class;
- payload/reference status;
- originating FSM handoff disposition.

### 6.4 Pre-distribution destination class

Before route selection, destination class must remain explicit.

Examples:
- `UNRESOLVED_PRE_DISTRIBUTION`;
- `DISTRIBUTION_DISABLED`.

Concrete route IDs and transport evidence belong downstream.

### 6.5 Remediation-phase rule

During the currently approved remediation scope:
- distribution remains disabled;
- `distribution_authorized` remains false;
- `distribution_attempted` remains false;
- accepted SignalEvent candidates may result in `DEFERRED`;
- no external send is performed;
- no outcome registration is performed;
- no broker execution is performed.

---

## 7. FSM MODULE CONTRACT

`fsm_runtime.py` / the canonical FSM layer owns:
- lifecycle state evaluation;
- persistence-safe transition application;
- cooldown/watchlist/focus invariants;
- lifecycle continuity;
- handoff semantics to signal engine.

It must not:
- format Telegram payloads;
- decide route entitlement;
- claim delivery success before downstream proof;
- build distribution policy.

Required conceptual interfaces after v3 implementation may include:
- `load_state()`;
- `save_state(state)`;
- `apply_transition(state, decision, now_ts)`;
- `enforce_invariants(state)`;
- a post-FSM adapter/orchestrator that returns `FSMExecutionHandoff`.

Exact implementation function names may vary if the semantic contract is preserved.

---

## 8. SIGNAL ENGINE MODULE CONTRACT

The signal engine remains the runtime orchestrator and owns:
- scan cadence;
- strategy invocation;
- FSM invocation;
- consumption of `FSMExecutionHandoff`;
- SignalEvent construction after acceptance;
- engine-level dedup;
- SignalExecutionResult construction;
- emission of execution observability evidence;
- downstream distribution invocation only when separately authorized.

It must not:
- redefine strategy mathematics;
- bypass FSM;
- infer accepted stage from raw score/DecisionObject alone;
- own tier/route entitlement policy;
- format Telegram messages;
- claim external visibility without route/publisher proof.

Canonical gating sequence:

```text
DecisionObject
  -> FSM
  -> FSMExecutionHandoff
  -> if accepted_for_signal_event: build SignalEvent
  -> build SignalExecutionResult
  -> emit signal_execution_result observability
  -> route only when separately authorized
```

---

## 9. DISTRIBUTION ROUTER CONTRACT

The substantive v2.0.0 router contract remains preserved.

Distribution owns:
- route config/state;
- entitlement policy application;
- route dedup;
- route reset;
- per-route publish-or-skip decision;
- route observability.

It receives only canonical upstream SignalEvents that have passed FSM/engine boundaries.

It must not:
- re-evaluate strategy truth;
- invent signal stages;
- mutate signal identity;
- treat an upstream candidate as permission to bypass entitlement.

Distribution activation is outside CHANGE_ID 20260831-01.

---

## 10. TELEGRAM PUBLISHER CONTRACT

The Telegram publisher remains transport-only.

It owns send/edit/document transport calls and transport error reporting.

It does not own:
- strategy decisions;
- FSM acceptance;
- execution gating;
- tier/route policy;
- analytics.

No Telegram call is authorized by this proposed remediation.

---

## 11. OUTCOME SERVICE CONTRACT

Outcome service remains downstream of governed signal delivery and expiry/eligibility rules.

An internal SignalEvent candidate or `SignalExecutionResult=DEFERRED` does not make outcome interaction eligible.

Outcome registration remains outside the current remediation scope.

---

## 12. OBSERVABILITY LOGGER CONTRACT

The observability logger owns schema-aligned event/proof emission.

It must support the promoted canonical schema and must not silently accept semantically invalid events as canonical proof.

After v3 promotion, it must be able to log `signal_execution_result` distinctly from decision, FSM and route events.

Observability failure must not fabricate the underlying trading truth.

---

## 13. ANALYTICS CONTRACT

Analytics remains downstream and read-only with respect to live trading behavior.

It may consume decision, FSM, execution, distribution and outcome evidence but must not mutate live strategy/FSM/distribution state from derived analytics alone.

---

## 14. LEGACY COMPATIBILITY

Legacy/generic interfaces may remain temporarily only behind explicit compatibility adapters.

Examples that must not remain canonical primary truth after migration:
- generic dict outputs replacing DecisionObject;
- `buffer_price` as primary strategy truth;
- raw FSM transition event as stage-acceptance proof;
- generic `decision` observability carrying mixed strategy/FSM/execution truth;
- tier-specific publication ownership inside Telegram transport.

Compatibility must be narrow, observable and removable.

---

## 15. V3 IMPLEMENTATION INVARIANTS

1. DecisionObject always precedes FSM.
2. Signal engine always consumes explicit post-FSM handoff semantics.
3. PRE/CONFIRM/OPEN_NOW may each form SignalEvent only after explicit acceptance.
4. Duplicate/blocked/rejected stages cannot form a distribution candidate.
5. Stable signal identity is preserved across lifecycle.
6. SignalEvent creation is not delivery success.
7. OPEN_NOW acceptance is not `LIVE_SENT`.
8. Execution outcome remains separate from strategy and FSM outcome.
9. Route/destination truth remains downstream of execution truth.
10. No hardcoded/fabricated market evidence is introduced to satisfy an interface.

---

## 16. PROMOTION GATE

This proposed document may be promoted only when:
- proposed `EVENT_SCHEMA_SPEC_v3.0.0.md` matches `SignalExecutionResult` semantics;
- proposed `OBSERVABILITY_LOGGING_SPEC_v3.0.0.md` matches the execution evidence obligations;
- Owner review accepts the explicit FSM stage-acceptance contract;
- supersession/master-index/reference repair is prepared;
- no runtime code change is bundled into the canonical promotion.

Until promotion, `MODULE_INTERFACE_SPEC_v2.0.0.md` remains active.

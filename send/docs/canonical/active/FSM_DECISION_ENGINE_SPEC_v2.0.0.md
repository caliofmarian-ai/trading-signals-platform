# FSM_DECISION_ENGINE_SPEC_v2.0.0

Version: 2.0.0  
Status: PROPOSED COMPLETE CONSOLIDATED SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: operational lifecycle interpretation between DecisionObject and Signal Engine, including exact-stage handoff semantics  
Supersession Intent: `FSM_DECISION_ENGINE_SPEC_v1.0.0.md`

Linked proposed/current authorities:
- Root Strategy Stack successor
- `ALGO_SPEC_v3.0.0.md`
- `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md`
- `DECISION_OBJECT_CANONICAL_SPEC_v2.0.0.md`
- `SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md`
- `MODULE_INTERFACE_SPEC_v3.0.0.md`
- `EVENT_SCHEMA_SPEC_v3.0.0.md`
- `OBSERVABILITY_SPEC_v3.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`

---

## 0. Authority and promotion status

This is the complete proposed successor for FSM decision truth.

Until explicit promotion, `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` remains active.

The major version is required because the post-FSM handoff contract becomes explicit and distinguishes lifecycle-stage release from final trade-execution readiness.

This document does not authorize external publication or broker execution.

---

## 1. Purpose

FSM consumes a canonical DecisionObject and converts pre-FSM strategic truth into operational lifecycle meaning.

FSM must:
- preserve strategy truth rather than recompute it;
- manage state/lifecycle progression;
- enforce focus/watchlist/cooldown/duplicate/lifecycle rules assigned to FSM;
- expose exact requested/accepted stage;
- expose whether the stage may be handed to Signal Engine;
- expose whether the setup is final trade-execution ready;
- emit observable transition/handoff evidence.

---

## 2. Architectural position

Required order:

`Market -> SR/Corridor -> Time -> Scoring + Trade Physics -> DecisionObject -> FSM -> Signal Engine -> Distribution`

FSM sits after complete strategic evaluation and before Signal Engine.

It is not allowed to bypass DecisionObject or distribution boundaries.

---

## 3. FSM does not own strategy mathematics

FSM must not derive/rederive:
- indicators;
- corridor geometry;
- `available_space`;
- time model mathematics;
- classical score;
- Trade Physics S/T/P/V;
- deterministic TPS;
- learned probability.

It consumes these as DecisionObject evidence.

---

## 4. Baseline operational outcome families

FSM must distinguish at least:
- REJECT
- WAIT
- PREPARE
- CONFIRM
- OPEN_NOW
- DEGRADED
- BLOCKED

These are operational families, not Signal Engine execution outcomes.

---

## 5. Meaning of core families

### REJECT
The operational lifecycle cannot proceed because upstream or lifecycle truth makes the setup invalid.

### WAIT
No operational release yet; evidence may remain valid but insufficient for progression.

### PREPARE
Operationally relevant setup suitable for staged monitoring/pre-alert semantics where canonical lifecycle permits.

### CONFIRM
Advanced validated setup, but not automatically final trade-execution ready.

### OPEN_NOW
Operationally mature executable stage, subject to exact handoff and downstream Signal Engine/Distribution semantics.

### DEGRADED
Lifecycle remains represented but with explicit degradation/limited readiness.

### BLOCKED
Explicit operational guardrail prevents progression/release.

---

## 6. Required post-FSM handoff contract

For every material evaluation FSM exposes at least:
- `requested_stage: PRE | CONFIRM | OPEN_NOW | null`;
- `accepted_stage: PRE | CONFIRM | OPEN_NOW | null`;
- `signal_id` where applicable;
- prior/current state;
- `state_changed: bool`;
- `reason`;
- `reason_family`;
- transition event/reference;
- `stage_handoff_ready: bool`;
- `trade_execution_ready: bool`;
- blocker/duplicate/focus/cooldown context where applicable.

---

## 7. Exact-stage acceptance principle

A requested PRE/CONFIRM/OPEN_NOW stage is considered accepted only when FSM explicitly identifies that same stage as `accepted_stage` and declares `stage_handoff_ready=true`.

The following are not proof of acceptance by themselves:
- a transition event existing;
- `accepted=true` generic boolean;
- no exception;
- state unchanged but event emitted;
- cooldown/watchlist/duplicate event.

---

## 8. `stage_handoff_ready`

`stage_handoff_ready=true` means the accepted lifecycle stage may be released to Signal Engine for SignalEvent consideration.

It may be true for:
- PRE;
- CONFIRM;
- OPEN_NOW.

It must be false when:
- requested stage was not accepted;
- lifecycle identity invalid;
- duplicate/suppression blocks release;
- cooldown blocks release;
- watchlist/focus rule blocks release;
- state transition is only informational/no-op;
- required lifecycle precondition is absent.

---

## 9. `trade_execution_ready`

This is separate from stage handoff.

Rules:
- PRE -> false;
- CONFIRM -> false;
- OPEN_NOW -> may be true only after all final operational preconditions pass.

PRE/CONFIRM lifecycle candidates do not become executable trades merely because they are handoff-ready.

---

## 10. Stable signal identity

The same trade idea must preserve stable `signal_id` across PRE/CONFIRM/OPEN_NOW progression.

FSM must reject or block lifecycle transitions with incompatible signal identity according to invariant policy.

Signal identity continuity is required before exact-stage handoff.

---

## 11. PRE lifecycle

PRE may be accepted when:
- upstream DecisionObject requests PRE;
- structure/time/score/Trade Physics strategic truth is already finalized upstream;
- focus/watchlist policy permits entry/refresh/replacement;
- no duplicate/cooldown/invariant blocker applies.

When accepted:
- `accepted_stage=PRE`;
- `stage_handoff_ready=true`;
- `trade_execution_ready=false`.

When watchlist full/cooldown/duplicate prevents stage release, transition evidence may still exist but `stage_handoff_ready=false`.

---

## 12. CONFIRM lifecycle

CONFIRM may be accepted only with valid lifecycle continuity, including required prior focus/watchlist state and stable signal identity.

When accepted:
- `accepted_stage=CONFIRM`;
- `stage_handoff_ready=true`;
- `trade_execution_ready=false`.

A CONFIRM transition is not external publication and not final trade execution.

---

## 13. OPEN_NOW lifecycle

OPEN_NOW requires:
- valid prior lifecycle path including PRE-path requirement;
- stable signal identity;
- valid focus/watchlist state;
- no cooldown/duplicate/invariant blocker;
- upstream DecisionObject already contains coherent final strategic evidence.

When accepted:
- `accepted_stage=OPEN_NOW`;
- `stage_handoff_ready=true`;
- `trade_execution_ready` may be true.

FSM acceptance does not prove SignalEvent construction, distribution, publication or broker execution.

---

## 14. No false LIVE_SENT / delivered state

FSM must not mark a signal as externally sent/delivered merely because OPEN_NOW was accepted or a SignalEvent candidate may be built.

Externally delivered/sent state requires the downstream success boundary defined by Signal Engine/Distribution/visibility canon.

If legacy persistent states contain names such as LIVE_SENT, their activation point must align to actual governed delivery evidence after migration.

---

## 15. Duplicate handling

Duplicate stage/candle or signal-lifecycle requests must be explicitly classified.

A duplicate event may be accepted as an idempotent lifecycle observation without being released again to Signal Engine.

Therefore duplicate handling can yield:
- state unchanged;
- reason = duplicate/suppressed;
- `stage_handoff_ready=false`.

---

## 16. Cooldown handling

If cooldown policy blocks PRE/CONFIRM/OPEN_NOW:
- event/transition evidence may be emitted;
- state may remain unchanged;
- accepted stage must be null or otherwise explicitly non-released;
- `stage_handoff_ready=false`;
- reason must identify cooldown.

---

## 17. Focus/watchlist handling

Watchlist/focus constraints are operational truth.

FSM must expose when:
- symbol added;
- refreshed;
- replaced another entry;
- rejected because capacity/fullness/priority;
- removed/released;
- invalid/missing focus state prevented progression.

A focus blocker must not be mistaken for strategy weakness or Signal Engine failure.

---

## 18. Trade Physics relation

FSM may consume Trade Physics evidence from DecisionObject for explanation/readiness semantics only.

It must not recalculate TPS or component formulas.

Examples of allowable use:
- include TPS/Trade Physics tier in transition explanation;
- apply a future canonical gate only if ALGO/DecisionObject/FSM canon explicitly authorizes that gate;
- preserve Trade Physics snapshot reference in observability handoff.

Current proposed integration does not automatically convert TPS interpretation bands into FSM stage thresholds.

---

## 19. Learned probability relation

`trade_success_probability` may appear in DecisionObject only when a validated model is ready.

FSM must not:
- fabricate probability;
- treat probability as TPS;
- make production lifecycle depend on learned probability unless a separate canonical rule explicitly authorizes that influence.

Default current-scope role is evidence/recommendation unless promotion docs state otherwise.

---

## 20. Signal Engine handoff

Signal Engine consumes `FSMExecutionHandoff`.

It must not infer accepted stage from raw FSM events.

Handoff must be sufficient for Signal Engine to decide:
- candidate construction allowed?
- stage identity?
- final trade readiness?
- blocker/reason?

---

## 21. Observability requirements

FSM evidence must allow reconstruction of:
- requested stage;
- accepted stage;
- prior/resulting state;
- reason;
- state-change flag;
- handoff readiness;
- trade-execution readiness;
- signal identity continuity;
- focus/watchlist/cooldown/duplicate context;
- DecisionObject/Trade Physics reference;
- persistence result where applicable.

---

## 22. Persistence/restart discipline

Where FSM state is persistent:
- writes must be atomic/recoverable according to persistence canon;
- restart must restore valid lifecycle state;
- stale/invalid state must not silently authorize a stage;
- identity and cooldown/watchlist state must survive or be explicitly reconciled.

---

## 23. Forbidden patterns

Forbidden:
- raw strategy output bypassing DecisionObject;
- FSM recalculating Trade Physics;
- generic transition event treated as acceptance;
- PRE/CONFIRM excluded from handoff because trade-execution readiness is false;
- OPEN_NOW treated as externally sent before downstream success;
- duplicate/cooldown/watchlist blockers treated as successful stage release;
- learned probability used as hidden production gate;
- signal identity changing silently across lifecycle.

---

## 24. Code alignment questions

After promotion, implementation must answer:
- how requested/accepted stage are represented;
- where `stage_handoff_ready` is computed;
- where `trade_execution_ready` is computed;
- how duplicates differ from accepted release;
- how cooldown/watchlist blockers are represented;
- how OPEN_NOW avoids false sent state;
- how stable signal identity is enforced;
- how DecisionObject/Trade Physics reference is preserved without recomputation.

---

## 25. Promotion rule

On promotion:
- v2 becomes single active FSM authority;
- v1 moves to superseded status;
- Signal Engine/Module Interface/Event Schema/Observability/Root/Master must reference the compatible version;
- runtime remains unchanged until post-promotion canonical/code audit.

---

## 26. Final principle

FSM is the operational lifecycle authority between DecisionObject and Signal Engine.

It explicitly distinguishes what stage was requested, what stage was accepted, whether that stage may be handed downstream, and whether the setup is final trade-execution ready—without recomputing strategic or Trade Physics mathematics and without claiming downstream delivery success.

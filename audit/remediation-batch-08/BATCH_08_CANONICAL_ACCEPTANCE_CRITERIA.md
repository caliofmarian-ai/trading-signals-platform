# BATCH_08_CANONICAL_ACCEPTANCE_CRITERIA

## Scope
Authoritative source: `send/docs/canonical/active/TEST_PLAN_v2.0.0.md`.

## Requirement inventory (normative sections)
Legend:
- Level: UNIT / CONTRACT / INTEGRATION / E2E
- Status: COVERED / PARTIALLY COVERED / NOT TESTABLE OFFLINE

| Requirement ID | Subsystem | Existing coverage pre-B08 | Missing pre-B08 | Required level | Fixture/mocking need | Acceptance condition | B08 status |
|---|---|---|---|---|---|---|---|
| TP-8.1 | config integrity | batch_01,batch_02 | consolidated canonical proof | CONTRACT | isolated config root | invalid config blocked safely | COVERED |
| TP-8.2 | distribution surfaces | batch_03 | canonical grouped evidence | INTEGRATION | fake publisher | disabled/missing routes skip explicitly | COVERED |
| TP-8.3 | fs/state surfaces | batch_06 | failure-injection pack | FAILURE | temp fs + fault injection | explicit errors, no unsafe continue | COVERED |
| TP-8.4 | startup summary | partial batch_06 | startup-state evidence in canonical tree | UNIT/INTEGRATION | boot monkeypatch | actionable startup block on invalid state | PARTIALLY COVERED |
| TP-9.1 | restart watchlist | batch_06 | e2e restart evidence package | INTEGRATION | persisted tmp state | no duplicate PRE replay | COVERED |
| TP-9.2 | restart live-sent | batch_06 | explicit e2e duplicate suppression proof | E2E | persisted state + fake publisher | no duplicate OPEN_NOW after restart | COVERED |
| TP-9.3 | restart cooldown | batch_06 | canonical grouped traceability | INTEGRATION | fixed timestamps | cooldown preserved across restart | COVERED |
| TP-9.4 | restart tier counters | batch_03/06 | explicit e2e package | INTEGRATION | persisted dist state | counters preserved near limits | PARTIALLY COVERED |
| TP-9.5 | atomic persistence | batch_02/06 | dedicated failure-injection evidence | FAILURE | os.replace fault | last-valid-state preserved | COVERED |
| TP-10.1 | spike rejection | batch_02/07 | canonical unit grouping | UNIT | deterministic candles | spike case rejected with reason | PARTIALLY COVERED |
| TP-10.2 | SR compression | batch_02/07 | explicit corridor test ids | UNIT | deterministic candles | insufficient space rejected | PARTIALLY COVERED |
| TP-10.3 | feasibility | batch_02/07 | explicit canonical mapping | UNIT | deterministic candles | infeasible move rejected | PARTIALLY COVERED |
| TP-10.4 | trend regime adjust | batch_02 | grouped canonical evidence | UNIT | deterministic candles | WITH/FLAT/COUNTER behavior consistent | PARTIALLY COVERED |
| TP-10.5 | threshold hierarchy | batch_02 + canonical unit | none | UNIT | param override fixture | PRE<=CONFIRM<=OPEN enforced | COVERED |
| TP-10.6 | strategy determinism | batch_02 + canonical unit | none | UNIT | deterministic fixtures | identical inputs => identical outputs | COVERED |
| TP-11.1 | decision before fsm | batch_06 | explicit e2e trace | INTEGRATION | state fixture | decision evidence precedes FSM | PARTIALLY COVERED |
| TP-11.2 | corridor before time model | batch_02/07 | explicit pipeline-order probe | INTEGRATION | controlled strategy fixture | order observable/reconstructable | PARTIALLY COVERED |
| TP-11.3 | decision audit completeness | batch_03/07 | unified canonical evidence | INTEGRATION | jsonl assertions | reject/shortlist/emission auditable | PARTIALLY COVERED |
| TP-12.1..12.8 | FSM lifecycle invariants | batch_06 + canonical integration/e2e | consolidated IDs | INTEGRATION | persisted fsm state | valid transitions + invalid blocked + dedup | COVERED |
| TP-13.1 | Telegram required fields | batch_03 | canonical boundary test | CONTRACT | mocked callback | callback parse/delegation contract holds | COVERED |
| TP-13.2 | topic routing | batch_03 | canonical e2e package | INTEGRATION | fake publisher | correct channel/topic routing | COVERED |
| TP-13.3 | admin command validation | batch_05 + canonical security/e2e | none | CONTRACT/SEC | auth monkeypatch | unauthorized blocked; valid mutation validated | COVERED |
| TP-13.4 | symbol/admin UX | batch_05 | explicit canonical symbol UX tests | CONTRACT | admin fixtures | atomic symbol updates + reflected state | PARTIALLY COVERED |
| TP-14.1..14.6 | tier-state rules | batch_03 + canonical integration/e2e/failure | none | INTEGRATION | fake publisher | publish/count/reset/dedup rules honored | COVERED |
| TP-15.1..15.6 | outcome integrity | batch_04 + canonical integration/security | none | INTEGRATION/SEC | mocked membership | linkage/window/dedup/privacy/persistence hold | COVERED |
| TP-16.1..16.4 | observability/audit | batch_03/05/06 + canonical e2e | none | INTEGRATION | jsonl checks | no silent failures, auditable events | COVERED |
| TP-17 (truncated in source file) | analytics & research | batch_07 + canonical e2e | canon text truncated at heading | INTEGRATION/E2E | analytics fixture | advisory deterministic output persisted atomically | PARTIALLY COVERED |

## Explicit validation limitations
1. `TEST_PLAN_v2.0.0.md` in repository ends at line `## 17. Analytics and Research Va` (truncated heading), so downstream TP-17 subclauses could not be exhaustively mapped verbatim.
2. Live-only surfaces (real Telegram/Broker/Railway) intentionally excluded from offline acceptance scope.

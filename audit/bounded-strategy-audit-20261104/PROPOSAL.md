# Bounded live strategy evidence

CHANGE_ID: 20261104-BOUNDED-STRATEGY-AUDIT  
TITLE: Keep live strategy diagnostics bounded and retain independent research evidence  
TYPE: PATCH — diagnostic implementation correction  
OWNER: Marian Caliof  
REQUESTED_BY: Owner's 2026-11-04 instruction to resume Telegram verification and strategy study  
DATE: 2026-11-04  
TARGET_DOCS: Active Master Index v2; Observability v3; Signal Engine v3; Research v3; governance v2.0.1. Their authority and strategy semantics remain unchanged.  
TARGET_CODE: Admin runtime audit, bounded JSONL reader, research summary status, telemetry worker and runtime status overlay.

## Evidence and scope

Private audit generated 09:16:30Z confirms 3,484 actual Finnhub ticks, 500 M1/M5 candles and 1,069 evaluations in its earlier runtime snapshot. Its last 50 evaluations (09:14:19–09:16:11Z) are REJECT. A persisted warning at 08:52:03Z identifies a real PRE reaching Distribution and being blocked by `FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED`. This is progress beyond the earlier post-#220 audit; it is not OPEN_NOW, publication or outcome proof. Raw private quotes/identifiers are excluded from this repository.

`handle_audit_runtime` currently reads and retains every engine/admin/error record before slicing to 50. Therefore an operational request scales with years of history and blocks its Telegram handler. Its 50-event tail also loses sparse execution attempts among frequent rejections. Research status exists only in a shared read/modify/write runtime snapshot and can disappear during concurrent status writes, although the research worker has explicit enabled evidence.

RATIONALE: Obtain timely, bounded, correctly scoped live execution and research evidence needed for the Owner's study. This is not the unrelated UI-speed/retention work on hold.  
EXPECTED_IMPACT: Read recent JSONL bytes/records only; return explicit source bounds and UNKNOWN/unavailable states; include original recent execution records from a separately bounded window; preserve a small independently persisted research summary and overlay its last observation without claiming a heartbeat.  
RISK: Incomplete/corrupt/concurrently replaced source windows must not appear as absence of events. A summary is derived research evidence, never an outcome authority or worker-liveness proof.  
BLAST_RADIUS: Privileged diagnostics and derived research status only. No strategy thresholds, calibration values, provider, route permission, publication guard or broker action changes.  
VALIDATION_METHOD: Reproduce the full-history audit read with a regression; test byte/record bounds, original identities, append/rotation/corrupt/missing sources, permission-first access, exact snapshot provenance and research truth/count/denominator preservation; run full repository tests and required CI.  
ROLLBACK_PLAN: Revert this patch to main 5a5d2d49331be260cb445a523995cd6b7e480e38. Keep all append-only logs and authoritative research records. The derived status cache may be ignored by the old runtime.  
DEPLOYMENT_PLAN: Review bounded implementation/tests in PR, require passing CI, deploy through existing GitHub→Railway pipeline, verify active SHA and terminal SUCCESS, then obtain an actual private `/audit_runtime` result.  
MONITORING_WINDOW: Startup, one real audit delivery, bounded source metadata and actual live feed/research evidence after restart. Actual future opportunity acceptance and delivery remain separate acceptance conditions.  
SUCCESS_CRITERIA: Audit no longer scans the full history; source windows and sparse execution attempts are visible; research observation survives unrelated runtime status writes; production audit is actually delivered.  
FAILURE_TRIGGERS: Resource bounds exceeded, misleading zero/complete-history claims, evidence identity mutation, loss of permission checks, changed trading guards, failed tests/CI/deployment.  
APPROVAL_STATUS: Implementation and routine corrective deployment authorized by the Owner's current instruction and prior project continuation authority. No approval of missing calibration, data rights or broker access is inferred.

# V3_SECOND_PRECISION_DURATION_PROPOSAL_v1.0.0

Status: HISTORICAL PROPOSAL — NON-AUTHORITATIVE — NOT EXECUTION CALIBRATION
Date: 2026-11-09
Owner requirement: the calculated duration, including seconds, must be known at
CONFIRM and retained at OPEN and at the final observation.

Implementation continuation in PR #264 binds the kernel through the lifecycle.
The binding authority is now the second-resolution section of
`../active/V3_CONFIRMED_DURATION_AND_SIGNAL_CARD_OWNER_AMENDMENT_v1.0.0.md`.
This historical proposal records the original discrepancy and design rationale;
it is not independent evidence of deployment or strategy efficacy.

## Verified discrepancy at the original baseline

At baseline 9de20ad512340818fd5ed2f18d9ed39f23bd5dda,
`send/core/time_model.py` computes:

`model_expiry = ceil(clamp(t_needed_adjusted, configured_min, configured_max))`

in minutes. Formatting this as minutes/seconds does not remove that quantization.
The original first-CONFIRM study horizon copies this model value. Calibrated
execution remains a separate readiness domain and is not enabled by this work.

## Candidate kernel

`intelligence.second_precision_duration.prepare_candidate` consumes the existing
`t_needed_adjusted` and explicit existing min/max limits. It selects the smallest
whole-second duration not shorter than the adjusted requirement or minimum,
and never beyond the maximum. If no such duration exists it rejects the plan.
There is no default duration, additional multiplier, score or post-expiry retry.

Examples: 8.6 minutes becomes 516 seconds (8 min 36 s), not 9 minutes.
3.45 minutes becomes 207 seconds (3 min 27 s). 4.77 minutes is 286.2 seconds;
under this explicit whole-second candidate policy it becomes 287 seconds, NOT
4 min 77 s. This is quantization, not evidence that 287 is an optimal expiry.
Only representation drift within four floating-point ULPs and at most one
nanosecond may normalize to an existing positive whole second.

The primary value is integer `duration_seconds`. The `_minutes` value is only
a compatibility projection. The record is immutable and identifies policy
`ADJUSTED_MOVEMENT_SECOND_CEILING_V1`.

## Integration constraints retained by the implementation

1. Keep the internal Model Time feasibility window separate from a prospective
   exact-duration study. Do not globally replace the existing model ceiling and
   thereby silently remove time headroom or change calibration-grid semantics.
2. Freeze a policy-tagged seconds plan at the first CONFIRM, before publication;
   bind it to decision/opportunity, direction and actual successful receipt.
3. At OPEN revalidate the same duration against current physical requirements.
   A mismatch requires a new preparation; never change a prepared duration.
4. Existing PRE/CONFIRM chains and pending studies retain their original policy,
   number, expiry and outcome. No backfill or rewrite. New source identity and
   policy-specific cohorts must prevent mixing results with old minute buckets.
5. Entry, result, chart and periodic summaries consume the same primary seconds.
   The previous `_duration(287 / 60)` float-tail defect is covered by regression
   tests and primary-second rendering; the stored expiry is never truncated.
6. Keep objective quote sampling and missing-quote reporting truthful. A display
   with seconds does not establish second-accurate market coverage.
7. Keep execution-calibration gates and broker-disabled state unchanged. Do not
   reuse a calibration artifact trained on different timing semantics.
8. Require full CI and natural production receipts before claiming live delivery
   of this policy. Separate delivery correctness from prospective efficacy.

## Evidence boundary

The active amendment and corresponding code/tests define the implementation.
This proposal remains outside the active 43-domain inventory. Exact-head CI,
matching deployment and actual new-policy receipts must be recorded in PR #264;
a successful numerical test is not evidence of market performance.

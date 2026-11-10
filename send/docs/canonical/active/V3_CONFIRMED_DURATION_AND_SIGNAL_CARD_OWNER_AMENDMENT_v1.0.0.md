# V3_CONFIRMED_DURATION_AND_SIGNAL_CARD_OWNER_AMENDMENT_v1.0.0

Status: ACTIVE OWNER AMENDMENT — 2026-11-09

Owner instruction: CONFIRM must provide the strategy's exact duration in minutes
and seconds so it can be prepared in the application. OPEN NOW must show the
local opening clock. Stage images must be distinguishable, legible on a phone,
and share the short daily trade number.

This amendment refines the existing Time, FSM, Telegram UX, distribution and
research domains. The functional inventory remains 43. It supersedes the
interval-only CONFIRM presentation in the 2026-11-06 presentation amendment and
the published study horizon in the research visibility protocol for new chains.
It does not supply execution calibration, change the Model Time formula or
declare an estimated duration statistically optimal.

## Exact duration before opening

- PRE means watch. A prepared execution duration is not promised at PRE.
- The first accepted CONFIRM prepares one exact duration. For governed execution,
  this uses the existing calibrated formula `model_expiry * (1 - pressure_bias)`
  inside its governed interval. No new calibration constants or implicit defaults
  are introduced. The interval remains validation evidence rather than the value
  the user must choose from.
- The FSM persists the exact value, original interval, calibration identity,
  confirmation timestamp, direction and opportunity before delivery. Repeated
  evaluations and restarts cannot silently replace the plan.
- OPEN NOW revalidates the same duration against fresh physical movement time,
  the current governed interval and the same calibration identity. If it fails,
  no opening with a substitute duration is published. A new opportunity requires
  a fresh PRE/CONFIRM sequence. A missing historical plan is not backfilled.
- Private OPEN delivery also checks that its exact duration matches the actual
  successful CONFIRM receipt. Internal acceptance is not proof of delivery.
- The execution duration remains measured from entry; the wall clock is a
  separate value. CONFIRM shows its issuance time and “INTRARE: LA OPEN NOW”.
  It does not invent a future opening appointment. OPEN shows the source opening
  timestamp in Europe/Dublin. Telegram API time and phone receipt are distinct.

## Current uncalibrated private study flow

When the first CONFIRM has no governed execution duration, the explicitly labelled
private study may disclose a prospectively frozen model-derived duration as
“DURATĂ STUDIU”. New live opportunities follow the second-resolution policy below;
preexisting chains retain their original Model Time horizon. A failed available
calibrated plan is BLOCKED, not converted into an uncalibrated study.

New study records keep a separate `study_observation` bound to that CONFIRM
horizon. OPEN, observed simulated expiry, result text and result chart use this
same duration. At OPEN it must still be at least the currently required adjusted
movement time. Missing, changed or incompatible receipt evidence blocks entry.
The study remains `STUDIU · SIMULARE`, with broker execution disabled.

The existing OPEN-based bias grid, training/holdout evidence and parameter scope
remain independent. A study result cannot overwrite a calibration candidate or
select the best later outcome. A pending study horizon is sampled even if its
independent research grid has already finished. Historical persisted studies
retain their original declared horizons and outcomes.

Internal Model Time retains its existing integer-minute ceiling for physical
feasibility and independent calibration research. It is no longer the quantizer
for a new live private-study duration. Legacy fractional governed values retain
their precision: 3.45 minutes displays “3 MIN 27 S”; 4.77 displays “4 MIN 46.2 S”.
No display transformation changes a stored expiry or proves broker precision.

## Second-resolution private studies — Owner continuation, PR #264

The policy `ADJUSTED_MOVEMENT_SECOND_CEILING_V1` consumes the existing unrounded
`t_needed_adjusted` and the configured minimum/maximum. It selects the smallest
whole-second duration at least as long as the adjusted requirement and minimum.
If no whole second fits below the maximum it rejects; it never clamps a required
movement time down to the maximum. No new score, multiplier or default is added.
For example, 8.6 minutes produces 516 seconds (8 min 36 s), not 9 minutes.
4.77 minutes produces 287 seconds under this explicit whole-second study policy;
that is distinct from formatting an already governed 286.2-second duration.

Only live strategy evaluations with an explicit observation clock can introduce
the new policy. Historical replay without that clock is unchanged. The first new
PRE marks its opportunity. At its first CONFIRM the FSM freezes primary integer
`duration_seconds`, the source adjusted time and limits, parameter fingerprint,
opportunity/direction, confirmation time and decision/audit identities. A digest
binds the complete plan. Missing plans cannot be filled at a later CONFIRM/OPEN.
Old PRE/CONFIRM chains are not upgraded; current results are not rewritten.

The model producer family remains `CONFIRM_MODEL_TIME`; the separate explicit
`study_duration_policy` distinguishes adjusted-time seconds from old minute
horizons. The actual successful CONFIRM receipt stores the policy, primary seconds
and plan ID. OPEN requires an exact match, rechecks fresh adjusted movement time
and unchanged parameter scope, and does not substitute a newly computed duration.

Entry/expiry scheduling, result, chart and periodic evidence use the same primary
seconds. Compatibility minutes must equal seconds/60. Rendering from primary
seconds avoids float tails such as 46.9999999999998. Legacy conversion may suppress
only machine representation drift within four ULPs and at most one nanosecond.
Genuine fractional seconds are not truncated. This duration amendment leaves
quote windows and arrival grace unchanged; a missing expiry quote remains
UNKNOWN, not a later WIN. The subsequent 2026-11-10 prospective quote-recovery
amendment in `V3_PHYSICAL_STUDY_VISIBILITY_PROTOCOL_v1.0.0.md` versions arrival
grace separately and preserves every frozen duration and source-time window.

The duration release introduced storage protocol V4, which reads V2/V3 records
unchanged and backs up the original pre-upgrade file before its first V4 save.
New/old results have separate duration
policy cohorts. The aggregate is explicitly historical, not performance evidence
for the new policy. Numerical correctness, API delivery and prospective strategy
efficacy are distinct. This policy does not validate an optimal expiry, promote
an execution-calibration artifact, or authorize broker execution.

## Image contract

Presentation erratum — 2026-11-09: the earlier orange CONFIRM and blue OPEN
wording transcribed the Owner's final instruction incorrectly. The corrected
colors below apply to both the top banner and the active bottom button. The
card background stays dark blue; BUY/SELL text keeps its separate direction
color. This correction changes neither durations nor trading gates.

| Element | Presentation |
|---|---|
| PRE | Muted pale yellow stage button |
| CONFIRM | Muted purple stage button, independent of direction |
| OPEN NOW | Muted green for BUY; muted red for SELL |
| BUY / SELL | Separate green / red direction indication |
| Trade identifier | Large inset #N, same Dublin daily number for all stages/results |
| Current stage | Same colored top button and checked bottom stage; other stages neutral |
| Timing | Explicit minutes/seconds duration, separate local clock with seconds |

Cards are square with essential fields sized for phone viewing. The number sits
inside the stage banner, away from the image edge. The caption has two searchable
lines; the photo carries the details. If rendering fails before any photo request,
one full text fallback preserves the actual timing, number and simulation status.
A photo transport failure is not followed by an immediate duplicate text send.

Mockups carry an explicit example label. Production acceptance requires tests,
the exact deployed commit and natural API receipts; a model image is not proof
that a phone displayed a production message or that execution calibration exists.

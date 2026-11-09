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
private study may disclose the already computed Model Time horizon as
“DURATĂ STUDIU”. The frozen first-CONFIRM value and timestamp are carried in the
successful receipt. A failed available calibrated plan is BLOCKED, not converted
into an uncalibrated study.

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

Model Time retains its existing integer-minute ceiling. A real value of five
minutes displays “5 MIN 00 S”. Fractional governed values are converted to minutes
and seconds without truncation: 3.45 minutes displays “3 MIN 27 S”; 4.77 displays
“4 MIN 46.2 S”. A seconds-capable display does not invent seconds in the strategy
or prove the broker supports that precision.

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

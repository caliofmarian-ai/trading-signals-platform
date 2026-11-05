# Paired lifecycle cooldown research V1

Owner requested continued calibration. Production evidence at 19:42 UTC on
2026-11-05 showed 2,287 of 5,760 severity-0 evaluations blocked by COOLDOWN.
The current FSM applies at least 300 seconds after rejection or focus expiry.
These counts are evaluation counts, not distinct lost trades or win/loss proof.

This separate prospective experiment compares cooldown durations of 1, 30, 60,
120 and 300 seconds in independent copied research FSMs. All policies use score
severity 0 to isolate only the lifecycle duration; the production score baseline
remains 14. The 300-second policy is the unchanged lifecycle timing control,
not a claim that score severity 0 is current production configuration.

Only entry into a new copied COOLDOWN has its deadline adjusted. Existing
cooldowns are not cleared on every tick. Every canonical strategy hard gate,
exact-stage FSM acceptance and the minimum 30-second PRE lead remains required.
Both normal rejection and focus-lease expiry must use the declared policy.
No module constant is monkeypatched; no shared or persisted production FSM,
score parameter, calibration artifact, broker setting or destination is changed.

Reuse existing Model Time paper observation and restart-safe immutable archive
mechanics. Missing real quotes stay UNKNOWN. Each archive profile index maps to
the ordered declared cooldown grid above within this experiment's own directory.
Cross-policy samples are correlated; do not add them into an independent sample.
The observed chain rate is descriptive for the current observation window and
cannot establish a sustainable 30 signals/hour or 80% efficacy on a short sample.

This is not a replacement for the existing 0..20 severity study or the paired
expiry study. Their files, original starts and quotes remain unchanged. Cadence
paper outcomes cannot be silently imported into the active expiry-calibration
cohort, which has a different operational admission policy. Any future proposal
must retain both its tested score profile and its tested lifecycle duration.

The existing Owner/shadow research opt-ins gate the experiment. Public logs use
`TSP_LIFECYCLE_CADENCE_RESEARCH` with counters and timing gaps, never raw prices
or opportunity identifiers. The private Owner audit contains the same read-only
summary. There is no automatic selection, production parameter write or publish.

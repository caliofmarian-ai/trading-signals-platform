# Correct empirical transport percentiles

Live report at 11:22:04 UTC on 5 November 2026 contained two successful private
API samples, 0.078538 and 0.082255 seconds, but reported p50=0.082255 and
p95=0.078538. With five samples, the old p95 index also excluded the observed
maximum. The mixed indexes were not a valid consistent percentile convention.

Compute both empirical percentiles with the nearest-rank convention
`sorted_samples[ceil(p * n) - 1]`, preserve null for no samples, and report the
method plus the bounded last-512-successful-deliveries sample scope. Reject
invalid/non-finite/negative samples instead of emitting misleading numbers.
With the observed five-sample set the corrected p50 is 0.078538 seconds and p95
is 0.091372 seconds. These are descriptive API measurements; they do not prove
phone receipt or predict future network latency.

No strategy, parameter hash, publication rule, execution expiry, experiment ID,
counter, start time or deadline changes. The existing two-hour observation ends
at 12:51:59.106 UTC. Implementation and CI can proceed during observation;
deployment is deferred until the fixed observation is complete to preserve
uninterrupted prospective sampling. The original reports remain historical
evidence, and the corrected percentile method is explicit in later summaries.

The existing exact-Owner private audit also gains a read-only projection of
validated model-horizon research records. Each observed entry/expiry quote and
timestamp is exported with the hypothetical/non-authoritative domain, an exact
validated-object digest and the parameter hash when present. Labels are checked
against recorded prices by the same source validator, without recovering,
rewriting or promoting records. Inventory is capped at 128 files, aggregate
reads at 2 MiB, each file at 128 KiB, and output at the latest 16 records.
Unknown nested fields and arbitrary text are excluded. Invalid or over-bound
evidence reports explicit unavailability rather than a false zero cohort.

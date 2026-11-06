# Calibration quote-coverage diagnostics V1

6 November 2026. The pre-buffer cohort has 39 distinct entries. At the longest
candidate horizon, 13 outcomes are UNKNOWN. An UNKNOWN is not a directional loss
or buffer failure; its source must be distinguished before choosing how to
improve measurement. The new buffer cohort remains prospective.

Candidate counts, training counts and holdout summaries now expose the existing
stored unknown reasons as a bounded `unknown_reasons` histogram:

- ENTRY_OBSERVATION_MISSING: no admissible real entry quote;
- EXPIRY_OBSERVATION_MISSING: entry observed, no admissible expiry quote;
- PROVIDER_CHANGED: provider scope was interrupted;
- OTHER: missing/unrecognized historical reason, with no raw text published.

Only UNKNOWN contributes. PENDING, INFEASIBLE and observed WIN/LOSS/DRAW are not
quote-gap events. The histogram is derived from the existing private records;
it never relabels a result, fills a quote, changes a sampling tolerance, resets
the cohort or changes calibration eligibility/selection. It cannot distinguish
provider silence from worker scheduling within an expiry gap; that requires
additional evidence, not an assumption.

The related all-level severity log truncation was fixed in #246. Its aggregate
marker retains all 21 levels under a 48-KiB ceiling while private state retains
raw timing samples and horizon histories. This change preserves that contract.

No provider request, strategy gate, active parameter, execution calibration,
Telegram publication, app service or broker action is introduced. Diagnostics
and hypothetical paper outcomes are not validated efficacy.

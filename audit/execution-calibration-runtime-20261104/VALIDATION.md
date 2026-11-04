# Local validation — 2026-11-04

Base: `bede7424605ec5ad1c23f3773199866fed347761`.

- Focused calibration/runtime/expiry/parameter regressions: **69 passed in 3.52 s**.
- Full repository suite: **1,865 passed in 48.93 s**.
- `git diff --check` and compilation of the two changed runtime modules: passed.
- New calibration-input test module: 51 cases, including exact file provenance, schema/duplicate-field ambiguity, non-finite/type/range validation, approval/validity windows, version/parameter/provider/instrument/buffer mismatches, whole-range expiry consistency, malformed/oversized/nonregular/symlink files, reload/restart/suspension/deletion, and actual `run_once` argument capture.
- The runtime integration fixture uses synthetic **test-only** strategy evidence: actual FSM acceptance and expiry gate produce OPEN_NOW 4.5 minutes from the temporary test artifact. The real Finnhub distribution guard still blocks publication. Missing/expired inputs still reach strategy evaluation with `None`, then block OPEN_NOW with `EXECUTION_TIME_UNAVAILABLE`. No external provider or Telegram request is made by offline tests.

No production numeric calibration is created. No score, market source, expiry formula, distribution permission, broker state or hypothetical/official outcome boundary is changed. Reference presence and parsing do not establish empirical calibration quality or broker compatibility.

Required exact-head CI and deployment evidence belong to the linked PR after publication. Local tests establish implementation behavior; they do not establish actual Telegram signal delivery, completed research observations, broker settlements, strategy win rate or profitability. #217 and #208 remain open until their remaining live acceptance criteria are independently met.

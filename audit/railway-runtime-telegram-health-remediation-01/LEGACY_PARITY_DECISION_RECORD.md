# LEGACY_PARITY_DECISION_RECORD

- The canonical single-process Railway runtime remains the live runtime.
- No legacy sidecar, external runner, or `legacy/bot_control.py` runtime path was restored.
- Required parity behavior was restored through current canonical modules and startup wiring only.
- `legacy/bot_control.py` remains treated as historical / externally-operated evidence, not as a live runtime dependency.

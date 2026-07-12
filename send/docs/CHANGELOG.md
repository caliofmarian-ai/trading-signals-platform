# CHANGELOG — Binary Signals Engine

All notable changes to this project will be documented in this file.

Format notes:
- Versions follow **SemVer**: MAJOR.MINOR.PATCH
- Each change that affects behavior must be reflected here.
- The canonical behavioral reference is: `docs/ALGO_SPEC.md (active canonical successor: ALGO_SPEC_v2.0.0.md)`
- The single source of truth for tunables is: `config/algo_params.json`
- Secrets (tokens/IDs/keys) live only in `.env`

---

## [Unreleased]
### Added
- (pending)

### Changed
- (pending)

### Fixed
- (pending)

### Removed
- (pending)

### Security
- (pending)

---

## [1.0.0] — 2026-03-02
### Added
- **ALGO_SPEC.md (active canonical successor: ALGO_SPEC_v2.0.0.md)** created as the canonical behavioral reference (engine contract).
- **CHECKLIST.md** created to enforce safe patching and consistent validation.
- **algo_params.json** introduced as source of truth for all algorithm parameters (no algorithm constants in `.env`).
- Defined the **signal lifecycle**:
  - **PRE** (Focus Candidate)
  - **CONFIRM** (Calculated Setup)
  - **OPEN_NOW** (manual execution moment)
- Defined the **focus system** (max 2 symbols in focus; wide scan pauses non-focus symbols).
- Defined **dynamic buffer concept**:
  - buffer is a safety distance; not a fixed number
  - expressed as **pips** for Forex and **points + %** for Crypto
- Defined **dynamic expiry concept**:
  - expiry computed from volatility + momentum + trend and clamped to a min/max window
- Defined **hard gates** (reject rules):
  - SR space requirement
  - spike/news-like filters
  - feasibility checks
  - cooldown rules
- Defined **confidence scoring model (0–100)** with thresholds:
  - PRE ≥ 70
  - CONFIRM ≥ 75 (+ all hard gates)
  - OPEN_NOW ≥ 80 (+ all hard gates)
- Defined **Telegram UX rules**:
  - SIGNALS_LIVE must contain all user-facing details (buffer value, expiry, confidence)
  - BUFFER_LOGS must contain diagnostic snapshots + reject reasons + parameter hash

### Changed
- Established policy: **No brand/product name inside code/spec/docs** at this stage.
- Established policy: **Parameters are documented in spec, tuned in algo_params.json, and implemented in code** (3-layer truth).

### Fixed
- N/A (initial release)

### Removed
- N/A (initial release)

### Security
- `.env` restricted to secrets only (no algorithm tunables).
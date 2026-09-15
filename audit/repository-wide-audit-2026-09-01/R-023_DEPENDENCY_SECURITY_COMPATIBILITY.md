# R-023 Dependency Security Compatibility Evidence

Issue: #151 — R-023 Dependency security compatibility upgrade

Current rebased baseline: `main = 69ed55a45ab8d238075da194b97409c8707f7ee3`  
Branch: `remediation/r023-dependency-security-main69ed`  
Prior implementation PR: #156 / head `5d13ff3ad3a038948c21386734e443bc0afe74e9` (historical evidence only after main advanced)

## Scope

R-023 changes only:
- `requirements.txt`;
- `tests/canonical/unit/test_dependency_transport_compatibility.py`;
- `tests/canonical/unit/test_dependency_library_io_compatibility.py`;
- this evidence record.

No runtime module, provider policy, symbol scope, strategy/FSM behavior, Telegram authorization, Railway configuration, canonical authority, CI workflow, or broker-execution behavior is changed.

## Reviewed dependency targets

Selected direct pins:
- `requests==2.34.2`
- `websocket-client==1.9.2`

Fresh public verification on 2026-09-15 confirms PyPI lists Requests 2.34.2 (released 2026-05-14) and websocket-client 1.9.2 (released 2026-08-31) as current releases; both support the repository's Python 3.12 target.

References:
- https://pypi.org/project/requests/
- https://pypi.org/project/websocket-client/

## Requests security rationale

The baseline `requests==2.31.0` is below reviewed patched floors for:
- CVE-2024-35195 / GHSA-9wx4-h78v-vm56;
- CVE-2024-47081 / GHSA-9hjg-9r4m-mvj7;
- CVE-2026-25645 / GHSA-gc5v-m9x4-r6x2.

References:
- https://github.com/advisories/GHSA-9wx4-h78v-vm56
- https://github.com/advisories/GHSA-9hjg-9r4m-mvj7
- https://github.com/advisories/GHSA-gc5v-m9x4-r6x2
- https://github.com/psf/requests/blob/main/HISTORY.md

Repository usage reviewed for the compatibility decision is ordinary Requests GET/POST/Response/RequestException behavior. No active custom `HTTPAdapter`, `verify=False`, or `extract_zipped_paths` dependency was identified in the prior R-023 audit. The target remains above the reviewed security floors without requiring an application API migration for the active call surface.

## websocket-client compatibility rationale

The baseline `websocket-client==1.8.0` is upgraded to `1.9.2`. The active market feeds use the low-level contract:
- `websocket.create_connection(url, timeout=30)`;
- `.send(...)`;
- `.recv()`;
- `.close()`.

No active `WebSocketApp` callback/run_forever contract is part of this upgrade boundary. The compatibility tests exercise both the repository call shape and real websocket-client handshake/frame code with an in-memory preconnected transport while external network access is blocked.

No exhaustive vulnerability-free claim is made for either dependency.

## Regression coverage

`test_dependency_transport_compatibility.py` verifies:
- exact reviewed direct pins;
- Requests runtime version and default TLS verification;
- Telegram POST shape/timeout;
- Telegram transport exception fail-closed behavior;
- Finnhub and Twelve Data low-level WebSocket connection shape.

`test_dependency_library_io_compatibility.py` separately exercises real installed-library code while simulating only transport I/O:
- Requests POST / Session / PreparedRequest / Response preparation;
- JSON serialization, timeout propagation and TLS verification default;
- Timeout and SSLError classification through Telegram publisher behavior;
- websocket-client HTTP upgrade validation;
- client masking and text-frame send/receive;
- invalid-upgrade rejection;
- receive timeout and connection-closed behavior.

DNS and socket-connect guards remain active in these tests. They do not prove live provider connectivity, a real certificate handshake, Railway deployment, or Telegram live acceptance.

## Prior branch evidence and why it is not final evidence

The earlier PR #156 reached head `5d13ff3ad3a038948c21386734e443bc0afe74e9` and passed its then-current Required Repository CI with the same four-file logical scope. After R-024 merged, `main` advanced to `69ed55a45ab8d238075da194b97409c8707f7ee3`, making that branch stale/non-mergeable.

Rather than force-update or treat stale CI as transferable proof, this branch was created directly from current main and only the reviewed four-file R-023 write-set was reapplied. Final acceptance therefore requires a fresh exact-head CI run on this rebased branch.

## Residual risk

Transitive dependencies remain resolved within upstream declared bounds because this task does not introduce a lockfile authority. Permanent repository CI provides behavioral regression detection, but deterministic transitive locking remains a separate governance decision.

Live provider connectivity, Railway deployment, Telegram multi-role acceptance and production runtime behavior are separate evidence classes.

## Required final validation

Before merge, the exact final branch head must pass the permanent `Required Repository CI` gate, including:
1. exact-head checkout/SHA verification;
2. dependency installation on Python 3.12;
3. repository CI governance checks;
4. provider selector regression;
5. Telegram Admin regression;
6. critical canonical contract regressions, including R-024 authority checks;
7. full `python -m pytest -q` suite including both R-023 compatibility files.

## Owner execution instruction

On 2026-09-15 the Project Owner consolidated project execution into one ChatGPT agent. Branch + PR + permanent exact-head CI + explicit self-audit remain required. The agent is authorized to merge low-risk completed remediation after those gates pass, without a separate orchestrator handoff. High-risk product/go-live/provider-credential decisions still require explicit Owner input.

## Invariants unchanged

- real market data only;
- one governed provider at a time;
- governed EUR/USD/Finnhub scope unchanged;
- two-second evaluation semantics unchanged;
- Telegram authorization unchanged;
- autonomous mutation unchanged;
- broker execution remains DISABLED.

# R-023 Dependency Security Compatibility Evidence

Issue: #151 — R-023 Dependency security compatibility upgrade

Baseline reviewed: `e520a51269a7ff34ffc7398276b75005dd67f20f`

Branch: `remediation/r023-dependency-security`

Date: 2026-09-10

## Scope and decision

R-023 changes only the two direct runtime dependency pins plus focused compatibility tests and this evidence record. It does not change provider policy, symbols, evaluation cadence, Telegram authorization, strategy/FSM semantics, Railway configuration, secrets, CI workflow ownership, or broker execution.

Selected targets:

- `requests==2.34.2`
- `websocket-client==1.9.2`

These targets were selected after security and repository-usage review, not by an unqualified latest-version bump.

## Requests security review

Baseline `requests==2.31.0` is below multiple reviewed security remediation floors:

1. CVE-2024-35195 / GHSA-9wx4-h78v-vm56 affects Requests `<2.32.0` and concerns TLS verification state reuse after a `Session` request with `verify=False`.
2. CVE-2024-47081 / GHSA-9hjg-9r4m-mvj7 affects Requests `<2.32.4` and concerns `.netrc` credential disclosure with maliciously crafted URLs.
3. CVE-2026-25645 / GHSA-gc5v-m9x4-r6x2 affects Requests `<2.33.0` in `requests.utils.extract_zipped_paths()`. Standard Requests HTTP use is not affected, and repository search found no use of that utility, but the baseline pin remains below the patched floor.

Upstream references:

- https://github.com/advisories/GHSA-9wx4-h78v-vm56
- https://github.com/advisories/GHSA-9hjg-9r4m-mvj7
- https://github.com/advisories/GHSA-gc5v-m9x4-r6x2
- https://github.com/psf/requests/blob/main/HISTORY.md
- https://pypi.org/project/requests/

`2.34.2` was chosen because it is the current stable Requests release as of this review, supports Python 3.12, is above all identified patched-version floors, and does not require repository migration for the APIs actually used here. The repository does not use a custom `HTTPAdapter`, does not call `extract_zipped_paths`, and repository search found no `verify=False` call. The relevant runtime surface is ordinary `requests.get`/`requests.post`, `Response.status_code`, `Response.json()`, and `requests.exceptions.RequestException` subclasses.

Requests 2.32.0 and 2.32.1 are yanked upstream. Requests 2.32.2 introduced a migration requirement for custom `HTTPAdapter` subclasses, but this repository has no such usage. Requests 2.34.x adds typing and proxy/path correctness changes; no repository call site depends on the changed typing surface.

## websocket-client maintenance and compatibility review

Baseline `websocket-client==1.8.0` is upgraded to `1.9.2`.

No reviewed websocket-client security advisory was identified in the sources inspected for this task. That is evidence of no identified advisory, not proof that no vulnerability exists.

`1.9.2` is the current stable PyPI release as of this review and advertises Python 3.12 support. The 1.9 line includes reconnect, error-handling, thread-safety, receive-path, and proxy/no-proxy maintenance work. Upstream references:

- https://pypi.org/project/websocket-client/
- https://github.com/websocket-client/websocket-client/blob/master/ChangeLog

Repository compatibility is narrow and mechanically testable. Both provider implementations use the low-level API only:

- `websocket.create_connection(url, timeout=30)`
- returned socket `.send(...)`
- returned socket `.recv()`
- returned socket `.close()`

No repository use of `WebSocketApp` was found, so callback-signature and `run_forever()` changes are outside the active runtime call surface. Provider reconnect remains repository-controlled: exceptions are caught, the feed waits two seconds, and retries; decision data remains fail-closed until real history/live-price freshness requirements are satisfied.

## HTTP and transport assumptions reviewed

### Telegram

`send/core/telegram_publisher.py` uses HTTPS Telegram Bot API endpoints with explicit `timeout=10` for message operations and `timeout=20` for document upload. Transport failures in delete handling are classified through `requests.exceptions.RequestException`. The focused R-023 regression verifies the post-call signature, timeout, default TLS verification behavior, and RequestException fail-closed classification without making a live Telegram request.

### Twelve Data

`send/runtime/twelvedata_market_data.py` uses `requests.get` for REST bootstrap with `timeout=20`, explicit HTTP 429 handling, non-200 fail-closed handling, and parsed JSON validation. Existing canonical tests inject the HTTP function and verify lazy network behavior, real-candle construction, local rate-limit enforcement, and fail-closed stream behavior.

### Finnhub

`send/runtime/finnhub_market_data.py` uses `websocket.create_connection(..., timeout=30)` and a single governed `OANDA:EUR_USD` subscription. Existing canonical tests verify subscription identity, persistence, freshness, real-history requirements, and fail-closed behavior. R-023 adds a compatibility test that exercises the installed websocket-client entry point through a monkeypatched connection function, so no external credential or fabricated live network result is required.

## Transitive dependency decision

R-023 does not add unrelated transitive pins. Requests already declares compatibility bounds for its HTTP stack, and no evidence found in this repository justifies converting the two-line direct dependency file into a transitive lockfile as part of this security fix. Adding such pins would expand scope and could create a competing dependency authority.

Residual risk: fresh environments can resolve newer compatible transitive versions within Requests' declared bounds. Permanent repository CI should detect a behavioral regression, but deterministic transitive locking remains a separate maintenance decision if the project later adopts a lockfile authority.

## Added R-023 regression

`tests/canonical/unit/test_dependency_transport_compatibility.py` verifies:

- exact reviewed direct pins are installed;
- Requests runtime version is the reviewed target;
- Requests `Session` retains TLS certificate verification enabled by default;
- Telegram `requests.post` call shape and timeout remain compatible;
- Telegram RequestException timeout handling remains fail-closed;
- Finnhub low-level `websocket.create_connection(..., timeout=30)` remains compatible;
- Twelve Data low-level `websocket.create_connection(..., timeout=30)` remains compatible.

These tests make no external network calls and contain no production credentials.

## Required exact-head validation

Before merge readiness, the final branch head must pass:

1. import/compile validation;
2. `tests/canonical/unit/test_dependency_transport_compatibility.py`;
3. existing Requests/Twelve Data/Finnhub compatibility regressions;
4. `tests/canonical/unit/test_market_data_provider_control.py`;
5. `tests/telegram_admin_ui_restoration/test_admin_ui_restoration.py`;
6. full `python -m pytest -q`;
7. exact-head GitHub Actions CI.

If R-022 becomes canonical first, this branch must be rebased/reconciled onto the new main and revalidated under the permanent CI gate before merge.

## Invariants unchanged

- real market data only;
- one governed provider at a time;
- current governed EUR/USD/Finnhub scope unchanged;
- two-second evaluation cadence unchanged;
- truth-domain boundaries unchanged;
- Telegram authorization unchanged;
- autonomous mutation unchanged;
- broker execution remains DISABLED.

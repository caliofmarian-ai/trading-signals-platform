# Companion application validation — 2026-11-05

The 0.1.0 results below are historical. The 0.1.1 startup correction supersedes the original Android launcher and APK. See the release evidence at the end.

Base source: `74b583fc3f912a23137f21eb313db0d662b495b7`. All additions are confined to `apps/signals_app/`. The existing canonical documents, engine files, root deployment files and Telegram entrypoints are unchanged.

- Complete regression command: `python -m pytest -q apps/signals_app/tests tests` — **2,161 passed**, two dependency deprecation warnings, 61.60 seconds.
- JavaScript: `node --check apps/signals_app/static/app.js` — passed.
- Android: Gradle 8.11.1 / Android Gradle Plugin 8.10.1 / API 36 / minimum API 24, `assembleDebug` — **BUILD SUCCESSFUL**.
- Final APK: `TradingSignals-0.1.0-test.apk`, 4,851,898 bytes.
- SHA-256: `548ee515110e4a6892119fafb0ce6012c68c2735d16d53e355c747f2d458d698`.
- APK signature: verified APK Signature Scheme v2 with the Android **debug/test** certificate. Zip alignment verified, including 16 KiB page alignment. This is not a release/Play signing key.
- Signing-certificate SHA-256: `4A:84:6D:83:CC:6A:D6:21:7F:30:2D:DA:CB:F2:51:92:FD:EE:AC:9C:F7:35:F4:C5:1E:03:4E:29:5A:E5:B7:7C`.
- Artifact inspection: 398 ZIP entries; no Python backend/strategy files, subscription/payment ledgers, environment files or private keys in the APK. Own-package classes are generated Android resource identifiers only; executable libraries are Google Android Browser Helper / AndroidX and their public dependencies.
- Dedicated app service: deployed **SUCCESS** at `https://signals-app-production-ba26.up.railway.app/`. `/healthz` and `/api/config` returned 200; unauthenticated `/api/session` returned 401.
- Published authentication screen was inspected in an actual browser. Local authenticated account, channel-access, CSRF, identity-linking and outcome-separation paths are covered by integration tests. A desktop browser screenshot is not Android device acceptance.
- Telegram service retained deployment `315ed0da-d109-4c5f-be87-91366da8ae1a` on `main`; its source/start command/volume were not changed. No Telegram messages, group-description edits or control commands were sent.

## Remaining acceptance

Live market-source setup and calibration parity; continuous current canonical subscription snapshots; actual Android installation, verified-origin full-screen launch and background push receipt; objective market-outcome projection; authenticated Telegram-control bridge; production signing and Google Play publication. The app engine is disabled until its independent source is configured. Do not infer any of those results from a successful build, API health response, or synthetic test fixture.

APK delivery: a private owner copy was saved, and the public app download at `https://signals-app-production-ba26.up.railway.app/download/android` was uploaded successfully and downloaded again. The downloaded bytes matched the local SHA-256 above. Its MIME type is `application/vnd.android.package-archive`. The hosted Digital Asset Links file returned the exact application ID and signing-certificate fingerprint above. Public upload was permitted after artifact inspection established that the APK contains no private backend code or secrets.


## Android 0.1.1 startup correction

Reported symptom: the installed 0.1.0 APK showed loading then returned to the home screen. The old manifest launched Android Browser Helper `LauncherActivity` with a translucent theme; its implementation calls `finish()` after handing off to the browser. No device crash log was available, so the exact OEM failure remains unconfirmed.

The replacement uses a persistent, opaque Activity containing the existing HTTPS application. It handles unavailable WebView, main-frame network/HTTP failure and renderer termination with an in-app recovery panel. Cookies and safe deep links remain supported. External origins, file/content access, mixed content and native JavaScript bridges are disabled. A new APK uses the same package ID and debug-signing certificate with a higher versionCode, enabling an in-place test update.

- `testDebugUnitTest assembleDebug`: **BUILD SUCCESSFUL**; **16 Android/JVM tests passed**, including cold start without any browser at API 28, 33 and 36, missing WebView, renderer failure/retry, network/server errors, state recreation and origin-policy attacks. These are Robolectric tests, not a physical-device/emulator run.
- `python3 -m pytest -q apps/signals_app/tests`: **17 passed**. Added download replacement coverage to prevent the stale 0.1.0 volume upload from being served after this release.
- `node --check apps/signals_app/static/app.js`: passed. The native-test UI reports background-notification limitations and handles sign-out when PushManager is unavailable.
- APK: `TradingSignals-0.1.1-test.apk`, versionName **0.1.1**, versionCode **2**, minimum API 24, target API 36.
- APK size: **24702 bytes**. SHA-256: `9e01f693723e5bfd34715f925bead66963102eebb625d4d795aa1e37b7e6cbf8`.
- APK Signature Scheme v2 verified; signing-certificate SHA-256 remains `4A:84:6D:83:CC:6A:D6:21:7F:30:2D:DA:CB:F2:51:92:FD:EE:AC:9C:F7:35:F4:C5:1E:03:4E:29:5A:E5:B7:7C`. Zip alignment verified with 16 KiB support.
- APK inspection: 6 ZIP entries; native host classes/resources only, no backend, market strategy, keys or account/subscription data. The smaller package no longer includes the browser-helper/AndroidX libraries. It loads its signed-in interface from the existing HTTPS service.
- The reviewed APK is bundled under `android/releases/` for atomic delivery with the application deployment. `/download/android` uses its versioned filename and `Cache-Control: no-store`. The legacy uploaded file is retained as a fallback only when no bundled release exists.

Physical installation, startup and login on the reporting phone still require confirmation. **The WebView APK has no background Web Push transport.** Browser/PWA Push is separate and remains unverified on devices. The live engine and continuous subscription source remain unconnected, and no live-signal or real-device-notification claim is made by these tests. Telegram source, configuration and deployment are outside this correction.

Hosted release verification: dedicated `signals-app` deployment `e7cdf5a5-dece-4405-8cf5-aeb02eee069c` reached **SUCCESS** using application commit `de6499adab2648b7583f600bcb908949b3e68339`. A fresh public `/download/android` response returned 24,702 bytes, `TradingSignals-0.1.1-test.apk`, the Android package MIME type, and SHA-256 `9e01f693723e5bfd34715f925bead66963102eebb625d4d795aa1e37b7e6cbf8`, exactly matching the reviewed signed artifact. `/healthz` returned 200 and `/api/config` retained `owner_configured: true`. Read-back confirmed the separate Telegram service still uses `main` and deployment `315ed0da-d109-4c5f-be87-91366da8ae1a`. Later branch commits preserve existing ignore rules or record evidence; they do not change the deployed runtime or APK.

## Independent app market-source integration

The app worker now selects EUR/USD from the existing market catalog, seeds only app-owned runtime directories, strips Telegram destinations/credentials, disables broker execution and imports the unchanged existing engine. Its router boundary writes only APP events. The Twelve Data key is configured as a Railway reference on the dedicated app service; its value is not read into development tools, browser code or the APK.

A source heartbeat alone no longer creates an OBSERVING state. Both recent successful market data and a completed canonical-engine evaluation are required. Stale workers/evaluations, missing history and rate limits produce non-healthy states. Owner Overview exposes bounded, whitelisted source evidence and Execution Time calibration availability, without raw upstream messages or credentials. Empty feeds do not claim that an unconnected source is working.

Validation: `python3 -m pytest -q apps/signals_app/tests` and the existing signal-engine persistence/scheduling, provider-control, signal-execution, runtime-calibration, runtime-parameter and observability-lineage tests — **120 passed**, two existing dependency warnings, 5.78 seconds. This includes 29 app tests and an in-process fixture confirming that an existing SignalEvent reaches only the APP router. `node --check apps/signals_app/static/app.js` passed. Fixtures are local tests, not live publication evidence. Android native code/APK are unchanged from the phone-confirmed 0.1.1 release.

Live source readiness, actual candidate publication and independent-worker parity must be assessed from the deployed owner dashboard and source evidence; no market or publication result is inferred from these tests.

Source acceptance exposed a real Twelve Data REST integration error: the existing parser interprets candle timestamps as UTC, while the broad-history request did not specify a timezone. The canonical market model rejected future-dated M1 evidence (`MarketModelUnavailable`, `market_model.py:204`). An app-process-only HTTP adapter now adds `timezone=UTC` to that exact existing history endpoint, preserving credentials, rate control, parser and strategy code. The separate canonical streaming-history adapter already requests UTC. Readiness allows the unchanged once-per-minute wide-scan cadence, immediately becomes unavailable after an evaluation error, and still rejects missing/stale evidence. Frontend assets require revalidation and the updated entry script has an explicit version query.

Updated targeted suite: **122 passed**, including timezone/credential preservation, normal minute-wide cadence and failed-evaluation health regression coverage. Native APK bytes remain unchanged. Deployed source and publication acceptance are tracked separately below.

Live acceptance — 2026-11-05: dedicated app deployment `7490d97a-46f6-479d-a3d2-487a6b66cbf0` reached **SUCCESS** at runtime commit `a344930137ee24990c2b58c0dc291acc5026a057`. At 19:08 UTC the worker emitted `OBSERVING / READY` after its first actual Twelve Data EUR/USD evaluation. The authenticated OWNER Overview visibly showed Market data connected, one completed evaluation, fresh market/evaluation timestamps, last decision **REJECT**, and **Awaiting calibration evidence**. PRE/CONFIRM/OPEN_NOW publication counters remained zero. This proves a real source/evaluation connection, not an accepted live signal or an execution-timing calibration. The UTC correction replaced the prior future-candle rejection without modifying shared strategy code. The owner separately confirmed that the installed 0.1.1 APK opens on their phone; the agent also completed and verified an OWNER browser login. Native background notifications and continuous subscription sync remain pending.

## Both provider sources

The owner requested concurrent use of FINNHUB and Twelve Data. The app now keeps
its independent Twelve Data engine and accepts current, authenticated status from
the existing FINNHUB calibration runtime. Separate OWNER cards show each source's
own data/evaluation evidence. The bridge does not publish signals, open a second
provider stream, merge candles, or grant member distribution. Local Twelve Data
REST reservations are bounded by a persistent daily/minute ledger, including
stream-history bootstrap, without claiming the actual provider account plan.

Targeted app/engine/provider/execution/parameter regression: **78 passed**, two
dependency warnings, 3.53 seconds. JavaScript syntax validation passed. Added
coverage includes machine authentication and OWNER access, independent health,
stale/future/wrong-source rejection, no signal/push writes from bridge evidence,
restart/UTC-midnight quota behavior, concurrent reservations and no network I/O
after the cap. Separate existing-runtime startup/provider tests: **72 passed**.
Production acceptance for this dual-source release is recorded separately once
the two deployed services and incoming real evidence have been verified.

Production acceptance: app runtime commit `76276d8cf31b392b0bba65024984b1c8fe18fd13`
is live in successful deployment `393f6bb9-7918-4a86-95d3-f16a83815f02`.
The public entry HTML serves the versioned dual-source script and FINNHUB owner
card; the published JavaScript consumes the separate `sources` array. Public
HTML, JavaScript and `/healthz` all returned HTTP 200. At 19:42:02 UTC the app
worker confirmed an actual Twelve Data EUR/USD evaluation (`OBSERVING`, count 1).
The configured app caps are 700 REST reservations per UTC day and 8 per minute.
The provider account's paid/free billing plan remains unverified; no subscription
or upgrade operation was performed.

The existing-runtime adapter was merged as PR #239 and deployed from main commit
`9b3a28b0a5879392bd105ec7f8b7fcc693a0c1f8` in successful deployment
`fe7458ff-f192-431b-a35d-b26fdaf9b016`. Required Repository CI passed on both the
reviewed branch and merged main. The app authenticated and accepted FINNHUB
status at 19:46:47 UTC, marked actual evaluation/data evidence `OBSERVING` at
19:46:52, then correctly became unavailable during a real 14-second quote gap
at 19:47:07 and returned to `OBSERVING` at 19:47:12. The source's own real-tick
evidence confirmed the gap and recovery. No additional Finnhub stream, source
switch, strategy parameter change or broker execution was introduced. This
establishes concurrent source monitoring and real evaluations, not completed
execution-expiry calibration or newly published signals.

Validation limitation: isolated startup-preflight tests expose an existing
cached `/opt/binarybot/config/admin_permissions.json` fixture-path dependency
(2 failures, 14 passes); the same two failures reproduce on the unchanged
pre-integration baseline. The full local existing-runtime suite passed 2,168
tests, and required CI passed with the final merged source. Isolated bridge
tests passed 3 and current expiry tests passed 20. No unrelated permission
runtime or fixture change was included in this provider integration.

## Single-symbol provider assignment — 2026-11-05

Owner approved FINNHUB → EUR/USD and Twelve Data → GBP/USD, with exactly one symbol per provider. The dedicated app service's `SIGNALS_APP_SYMBOLS` is set to `GBP/USD`. The app worker now defaults to GBP/USD and rejects an empty, unknown or multi-symbol selection before making market requests. The existing FINNHUB service is not changed. The durable Twelve Data budget and the 700-request cap remain in force; no provider account/billing operation is performed.

Targeted selection validation: **5 passed, 12 deselected** (`catalog_selection`, `unknown_symbol`, `multiple_symbols`, `default_app_symbol`). These verify both supported single-pair selections, immutable source catalog/isolation, rejection of multiple/unknown symbols and the approved GBP/USD default. Live data/evaluation acceptance is recorded separately after deployment.

Live acceptance: dedicated app runtime commit `b9f2b912902175404b5fa0e0e96a152cdadc085c` is running in successful deployment `7db7c5cb-25e4-4e6b-ba95-7982c260c4e5`. At 20:59:00 UTC the worker recorded a real GBP/USD evaluation (`TWELVE_DATA`, `OBSERVING`, count 1). At 21:01 UTC the authenticated OWNER Overview showed both sources as **Market data connected**: FINNHUB with only EUR/USD (1,697 completed evaluations), and Twelve Data with only GBP/USD (3 completed evaluations). No multi-symbol request or account upgrade was used.

The persistent Twelve Data counter progressed from 148/700 before the selection change to 160/700 at final acceptance, across both app restarts; the daily ledger was not reset. The existing FINNHUB/Telegram service remained on the same successful deployment `5c0b7a3b-08ac-4e91-bbb3-1e2aa5f0fbac` throughout this symbol assignment. Its brief source-unavailable indicator recovered with current real quote/evaluation evidence, without relaxing freshness gates. Execution Time remains awaiting calibration evidence; a decision label alone is not evidence that an OPEN_NOW signal was published.

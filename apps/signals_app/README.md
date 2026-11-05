# Trading Signals companion application

An optional Android/installable application surface in the **existing** repository. It imports the existing SignalEvent, subscription registry, billing contract and strategy engine. It does not copy strategy implementation or create a competing canonical specification.

The Telegram entrypoint, existing root deployment configuration, `send/`, `scripts/`, and canonical documents are unchanged. Application code and state belong here and in a separate `signals-app` service/volume. Do not merge or redeploy the Telegram service as part of deploying this folder.

## Run and test

From the repository root, with Python 3.12:

```sh
python -m pip install -r requirements.txt -r apps/signals_app/requirements.txt
python -m pytest -q apps/signals_app/tests
python -m apps.signals_app serve
```

Open `http://127.0.0.1:8765`. Accounts use scrypt password hashes and revocable, HttpOnly, SameSite cookies. State-changing member requests require a session CSRF token. The app's account authority does not automatically grant Telegram administrator rights.

For a local application owner, use the interactive command (password is not a command argument):

```sh
python -m apps.signals_app create-owner --email YOUR_EMAIL
```

Alternatively configure a private `SIGNALS_APP_SETUP_TOKEN` of at least 32 characters and open `/#setup=TOKEN`. This is a one-time owner bootstrap, not a public registration role selector. The fragment is removed before API requests. Never commit setup/ingest keys, credentials, signing keys or runtime databases.

## Channels and subscription continuity

Channel identifiers and limits come directly from the existing billing/channel contracts: **FREE, BASIC, PRO, ELITE**. The membership model is **EXCLUSIVE**. A new app account has the canonical free baseline. A paid subscriber connects their existing identity using an email-bound, single-use, 15-minute link issued by the application owner. The link only connects identities; it never creates a payment or activates/upgrades a subscription.

Before issuing a link, supply current canonical subscription evidence to authenticated `POST /api/internal/subscriptions`:

```json
{"generated_at": 1793900000, "records": ["FULL_CANONICAL_SUBSCRIPTION_EVENT_OBJECTS"]}
```

The example timestamp/records above describe the shape only; actual input must contain the complete existing append-only registry events and a current Unix timestamp. The original registry validator checks sequence/version continuity before an atomic app-local replacement. Outdated snapshots cannot grant paid access: snapshot evidence expires after 300 seconds and access is checked again for each feed/push request. A production source must refresh the snapshot and propagate reversals/expiries continuously. **This source connection is not automatically created by deploying the app.**

Issue an existing subscriber's link through the owner screen, or:

```sh
python -m apps.signals_app invite --email MEMBER_APP_EMAIL --subscriber-ref VERIFIED_EXISTING_REFERENCE
```

No source prices are invented. Paid checkout is unavailable when source prices are not configured. No copy of the existing subscriber's payment is taken.

## Signal engine and transport

The engine is disabled by default. The dedicated app service can enable it independently and select a subset of the existing market catalog with `SIGNALS_APP_SYMBOLS` (default `EUR/USD`). Its own engine/config/state directories live on the app volume. Do not label an HTTP health check or a running loop as live signal acceptance.

To run the existing engine in an **independent process**, configure a member-distribution-capable existing market provider and set `SIGNALS_APP_ENGINE_ENABLED=1` **on the app service only**. The child seeds its own engine/config/state directories, imports `send/core/signal_engine.py`, and replaces only its own in-memory router boundary with the APP transport. It never starts `system_boot`, Telegram polling, or a broker worker. It clears Telegram credentials/destinations from its own environment before imports. The app transport preserves the existing Finnhub personal-use restriction and rejects member distribution for unsupported providers. A provider credential can be referenced from the existing Railway service without reading it into the browser or APK. This does not switch or redeploy the Telegram service.

An alternative trusted source may POST an existing-engine candidate to `/api/internal/signals`, with `Authorization: Bearer SIGNALS_APP_INGEST_TOKEN`:

```json
{"provider":"TWELVE_DATA","candidate":{"event_type":"SIGNAL_CANDIDATE","stage":"PRE"}}
```

This is an abbreviated shape, not a valid signal. Actual input must contain the complete shared SignalEvent, FSM transition, decision and execution references. Candidates must already have passed the existing upstream FSM/execution gate. Never expose this machine credential in the Android/browser client. APP events and counters are app-local, and do not claim Telegram delivery. `OPEN_NOW` expiry is copied exactly from Execution Time, never Model Time; replayed/history entries do not receive a new entry deadline. Signal stages are immutable and deduplicated per channel/signal/stage. Daily entry limits and London reset timing come from existing channel configuration.

Independent engine instances share source logic but are **not proven to emit identical live sequences**: live data timing, calibration and persisted state must also be reconciled. No production parity is claimed until tested with actual provider data and devices.

Source readiness requires both a recent real market-data success and a completed existing-engine evaluation. A loop heartbeat, stale persisted health, missing history or a rate-limited provider cannot produce a healthy indicator. The owner Overview shows market/source status, last data/evaluation timestamps, current-process evaluation count, last decision kind and whether Execution Time calibration evidence exists. This diagnostic does not relax any strategy/FSM/execution gate. Missing calibration remains missing evidence; no synthetic signals are published to prove a connection.

## Notifications, outcomes and Telegram control

Web Push uses a persistent app-only VAPID key and a retried outbox. The application rechecks active access/session before sending, drops obsolete entry alerts, removes expired endpoints, and stops alerts on sign-out. Lock-screen notices contain no market/entry/member details. Actual background delivery still needs device acceptance; an enabled browser permission alone is not delivery proof.

Android test version 0.1.1 hosts the same HTTPS application in its own persistent WebView window. The original browser-helper launcher finished its activity after handing off to a browser; on the reported phone that left no usable application window. The new host keeps loading, network/server errors and retry controls inside the app, preserves cookies, handles Android back navigation, and permits navigation only to the application origin. It exposes no native JavaScript bridge and disables file/content access and mixed content. Digital Asset Links still associates application links with the signed package.

**Background Web Push is not supported by this WebView test host.** The hosted browser/PWA still has its existing Web Push path, while the APK explicitly reports this limit. A native background-notification transport remains required before Android notification acceptance. Live signals and subscription synchronization remain unconnected as documented above.

From `android/`, run `gradle --project-cache-dir /tmp/signals-app-gradle-cache testDebugUnitTest assembleDebug`. Keep Gradle project caches outside this repository because the existing repository-hygiene tests prohibit lock-file artifacts, including ignored ones. The versioned, debug-signed test APK is bundled under `android/releases/` so the dedicated app deployment and `/download/android` distribute the reviewed version instead of an older uploaded file. A bundled release takes precedence over the legacy private upload endpoint. Never commit signing keys. Release signing, Play Console ownership, store review and physical Android acceptance remain explicit release steps. A debug APK is for testing, not a Play release.

Objective market results and member self-reports are separate data domains. The initial owner dashboard shows unknown win rate when objective settled evidence is absent. It does not turn missing outcomes into losses or self-reported wins into objective performance. An objective-outcome adapter is still needed before strategy performance claims.

The requested future Telegram-control connection is **not active**. It must call the existing command/permission authorities using an authenticated canonical actor mapping and display confirmed command outcomes. An application OWNER account alone is not proof of Telegram Owner identity. No bot credentials, production control calls, group-description edits or messages are performed by this release.

## App-service settings

Use a dedicated service, its own volume at `/app-data`, and the feature branch containing this folder. Keep the Telegram service on its original branch/start command. Explicit app start command: `python -m apps.signals_app serve`. Build both root and application requirements. Health check: `/healthz`. Do not apply the existing root Telegram start command to the app service.

| Variable | Meaning |
| --- | --- |
| `SIGNALS_APP_PUBLIC_URL` | Exact HTTPS origin, also used for request-origin validation |
| `SIGNALS_APP_DATA_DIR` | App-only persistent state directory |
| `SIGNALS_APP_SETUP_TOKEN` | Private, single-use owner bootstrap key |
| `SIGNALS_APP_INGEST_TOKEN` | Private machine source key, at least 32 characters |
| `SIGNALS_APP_ENGINE_ENABLED` | `0` by default; only `1` starts the isolated engine |
| `SIGNALS_APP_SYMBOLS` | Comma-separated subset of the existing market catalog; default `EUR/USD` |
| `SIGNALS_APP_ANDROID_SHA256` | Comma-separated signing-certificate SHA-256 fingerprints for Digital Asset Links |
| `PORT` | HTTP listener, default 8765 |

APK builds and server health do not establish store publication, current subscription sync, live data calibration, or real-device notification delivery.

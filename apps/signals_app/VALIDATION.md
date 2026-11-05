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

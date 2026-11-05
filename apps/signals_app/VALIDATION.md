# Companion application validation — 2026-11-05

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

# Companion app source status

The optional `scripts.app_source_bridge` exports status from the existing FINNHUB
calibration runtime to the existing companion app. It reuses the current source
and does not open a second WebSocket or send market, signal, Telegram or broker
requests. The existing provider selection and strategy parameters are unchanged.

Configure only on the existing runtime service:

- `APP_SOURCE_BRIDGE_ENABLED=1`
- `APP_SOURCE_BRIDGE_ORIGIN=${{signals-app.SIGNALS_APP_PUBLIC_URL}}`
- `APP_SOURCE_BRIDGE_TOKEN=${{signals-app.SIGNALS_APP_INGEST_TOKEN}}`

The key stays in Railway references and is sent only as a bearer header to the
configured HTTPS app origin. Redirects are refused. A daemon sends at most one
small status request every five seconds with a three-second timeout. A failure
does not block the engine, readiness or startup. Disabling the flag restores the
original behavior without changing provider state or calibration records.

The payload includes only source identity, timestamps, current-process evidence,
evaluation count/kind and whether execution calibration evidence is available.
Stopped, stale, wrong-provider or prior-process status cannot be marked current.
Provider credentials, prices, candles, account identities, raw exception text
and runtime paths are excluded. The app accepts fresh authenticated evidence
only and displays it to OWNER separately from its Twelve Data source. This
endpoint does not publish a signal or establish member-distribution permission.

# Pocket Option compatibility and strategy research — 2026-11-05

Status: **RESEARCH / SOURCE AUDIT / UI OBSERVATION — NOT ACTIVE CANON**.

Repository: `caliofmarian-ai/trading-signals-platform`.
Audited main: `77641158d7abf16a23edcc9bbadd8ab24ab77015`.
Companion-app comparison: PR [#236](https://github.com/caliofmarian-ai/trading-signals-platform/pull/236), head `9cce08cdfba03296f76c2ba642e694afa16cb713` (open/draft when inspected).

Technical continuation in Romanian: [export evidence, indicator parity, candle coverage and expiry precision](APROFUNDARE_TEHNICA_RO.md). It records later observations and supersedes initial UNKNOWN statements only where direct follow-up evidence is identified, including confirmation of the second EMA 200 label and the XLS export control. A completed export file remains unverified.

## Rezumat pentru Owner

Proiectul are deja un motor de analiză și instrumente de cercetare utile, dar **nu este încă racordat și validat pentru Pocket Option**. Lipsesc sursa autorizată de cotații Pocket, identificarea exactă a instrumentelor, comparația indicatorilor, expirarea verificată și reconcilierea rezultatelor brokerului. Nu putem transforma rezultatele Finnhub sau Twelve Data în rezultate Pocket OTC prin schimbarea numelui simbolului.

Există o distincție importantă: motorul din `main` selectează alternativ furnizorii, însă aplicația din PR #236 are două surse separate, Finnhub pentru EUR/USD și Twelve Data pentru GBP/USD. Raportul nu recomandă reconstruirea acestei funcții deja prezente în ramura aplicației. Dovezile de funcționare consemnate acolo sunt istorice; nu reprezintă o verificare nouă a producției în această sesiune.

Am inspectat interfața autentificată și am găsit indicatori, instrumente grafice, semnale native, ordine condiționate și prezentarea botului Telegram oficial. Niciuna dintre aceste constatări nu dovedește un API autorizat pentru botul nostru sau o strategie profitabilă. Prioritatea este corectitudinea datelor și a rezultatului, apoi experimentele controlate cu indicatori și treptele 0–20.

## 1. Evidence classes and verdict

| Evidence class | Established in this audit | Not established |
|---|---|---|
| UI observed | Authenticated terminal and native feature menus; demo restored after research | Continuous monitoring, order execution, fill accuracy, future feature availability |
| Source verified | Current main and separate companion-app source at the SHAs above | Current deployed configuration or current Railway/Telegram state |
| Historical acceptance record | PR #236 records separate-source evaluation and deployment evidence | Independent reproduction of those live observations today |
| Offline tests | 128 existing relevant tests passed | Broker integration, strategy efficacy or device receipt |
| Official published sources | Vendor terms/product descriptions and Irish regulator requirements | Account-specific exception, usable developer authorization or profitable predictions |
| Proposed research | Tools, data contracts and acceptance criteria below | Implemented production changes or approved calibration |

**Decision:** retain the existing research/signal foundation. Pocket compatibility is **UNVERIFIED**, with concrete missing components. An authenticated website is a viewing surface, not a data/execution integration. An observation made earlier in a voice conversation is not a current quote.

## 2. Published platform constraints

The current Public Offer [W1] restricts service by citizenship/permanent residence; its country list includes Ireland and Romania. It specifies broker-processed quotations, server-side execution, normal processing typically 0–4 seconds with longer delays possible, per-trade payouts and entry-versus-expiry settlement. Equal prices return the stake. Results involving unauthorized bot software may be canceled or revised. These are contractual statements, not independently measured execution quality.

The vendor's payments overview [W8] separately excludes EEA residents while discussing cryptocurrency. No crypto-withdrawal exception to geographic eligibility was found. The assertion that crypto alone permits otherwise restricted use remains **unverified and inconsistent with the retrieved published material**. An account-specific claim needs official clarification; no support message was sent. The current Irish regulator page [W9] confirms binary-options retail-sale intervention measures. This is not a finding that opening a demo is itself a criminal offence. Legal classification and applicable permissions must be resolved before real-money product deployment; a product label does not settle that assessment.

The official bot article [W5] advertises Telegram automation, manual/automatic modes and risk settings. The broader bot article [W6] mentions API integration but does not provide an endpoint contract, authentication/key issuance specification, data licence or authorization for this project's bot. **Official custom API availability is NOT VERIFIED**, rather than proven absent. An official built-in bot is not evidence that it accepts arbitrary inbound signals from our Telegram bot. An unofficial library is not a substitute for permission or interface documentation.

The company explanation still linked by the OTC schedule [W3, W4] says its OTC price movements do not depend on the corresponding general-market price. The exact OTC generator and a meaningful executable order-book/volume feed were not established. We therefore must not infer those mechanics, market manipulation, predictability or guaranteed profitability.

## 3. What was actually observed inside the application

These are point-in-time UI observations on 5 November 2026. No screenshots containing account information are committed. Navigating to informational pages displayed a non-demo header; no real trading screen, funding operation or order was activated. The final verified URL was the demo terminal.

| UI surface | Observation | Practical use and limit |
|---|---|---|
| Demo terminal | `CAD/JPY OTC`, M1, candlesticks, ATR14 and RSI14, two Moving Average entries | Confirms the research surface, not data parity with our feeds |
| First MA settings | Period 50, type EMA directly verified in the dialog | The second MA's exact period/style was not independently confirmed in a dialog in this audit |
| Indicator menu | ADX, ATR, Bollinger Bands, CCI, Envelopes, Ichimoku, MACD, Momentum, MA, RSI, Stochastic, Volume, SuperTrend, Vortex and others | Availability inventory only; no incremental predictive value established |
| Drawing tools | Horizontal/vertical lines, ray, Fibonacci retracement/fan, trend line, parallel channel, rectangle, Andrews' Pitchfork | Manual annotations and retrospective explanation; no new predictive evidence by themselves |
| Time selector | Duration field and presets S3/S15/S30/M1/M3/M5/M30/H1/H4 visible | Availability snapshot; accepted duration, rounding and exact settlement still need observation |
| Signals panel | Direction arrows, Copy signal controls, Telegram icon, System signals setting | Observed UI warning treats signals as supplementary indicator-based analysis, not absolute accuracy; no copy control clicked |
| Pending Trades | Separate time-triggered and asset-price-triggered forms, payout minimum and duration fields | Could reduce manual timing effort in a separately authorized workflow; no pending order created |
| Social Trading | Demo panel says this section is available only for real accounts | No demo copy-trading acceptance; no follower/leader fill parity evidence |
| Help → Apps | Official Telegram bot, Analytics, Signals and Trading Strategies app descriptions | Product discovery; no bot authorization, app installation or external account linking performed |
| Trade state | No open trades shown when inspected | Not proof of historical performance or account-wide absence of trades |

The observed CAD/JPY OTC payout was 92% at that observation only; another tab displayed 80%. These are not permanent rates. Displayed terminal clock and timezone must not be treated as synchronized UTC evidence without measuring offset. Website schedule timezone [W3] is a separate concept from candle time, host time and execution time.

The observed native MA colors were not the green/orange convention discussed earlier. Cosmetic convention and settings synchronization between devices are not proof of numerical indicator parity.

## 4. Repository compatibility audit

Line references below apply to the exact audited main SHA. App-only references apply to the separate PR head.

| Area | Source evidence | Conclusion |
|---|---|---|
| Providers | `send/core/market_data_provider_control.py:11–14,128–213` | FINNHUB and TWELVE_DATA; exclusive selection within one existing runtime |
| Finnhub identity | `send/runtime/finnhub_market_data.py:13–15,57–64` | EUR/USD maps to `OANDA:EUR_USD`; not Pocket EUR/USD OTC |
| Twelve Data | `send/runtime/twelvedata_market_data.py:14–18,59–97` | External REST/stream infrastructure exists; subscription entitlement and present health are not inferred |
| Source routing | `send/runtime/market_client.py:39–53,321–346` | Consumes external provider evidence; no Pocket quote or settlement adapter found in audited main |
| App's two-source arrangement | PR #236 `apps/signals_app/README.md`, `source.py:22–50`, `paired_sources.py:10–65`, `worker.py` | Separate app engine plus authenticated Finnhub status bridge, not candle merging or shared multi-provider strategy state |
| Approved app assignment | PR #236 README and VALIDATION, final single-symbol section | Finnhub EUR/USD retained; separate Twelve Data app uses GBP/USD only. Recorded live acceptance is historical, not rerun here |
| Broker boundary | `README.md:16`; `send/runtime/startup_preflight.py:237–242` | Existing preflight rejects enabled broker execution; enabling a flag is not an integration solution |
| Scan cadence | `send/runtime/engine_loop.py:16–39` | Two-second sleep after processing; no guarantee of two-second end-to-end latency |
| EMA/RSI/ATR | `send/core/market_model.py:95–126,311–324` | EMA50/200 and ATR14 from M5; RSI14 from M1 |
| Strategy ordering | `send/core/strategy_v2.py:74–95`; active Master Index | Market → Corridor → Time → Scoring/Physics → DecisionObject → FSM, with downstream execution |
| Broker-scoped timing | `send/core/runtime_execution_calibration.py:159–183`; related tests | Calibration binds source, symbol, buffer mode, versions, parameters and validity; OTC mismatch is rejected |
| Expiry | `send/core/execution_model.py:111–136` | Missing calibrated execution expiry remains unavailable; internal Model Time is not an automatic broker duration |
| Severity research | `send/intelligence/signal_severity_scale.py:6–30`; `live_score_severity_research.py:1–33` | Existing 0–20 research scale; baseline 14; score-cutoff experiment, not success probability |
| Outcome | `send/core/market_outcome_evidence.py:300–339` | Provider result explicitly does not assert live payout or broker performance |
| Timing receipts | `send/core/owner_signal_delivery.py:119–150` | API acceptance is recorded; phone receipt and broker execution remain unproven |

The earlier statement that simultaneous providers were not implemented was correct only for the shared main runtime's selector. It is incomplete for the wider project because the app branch already implements separated sources. Do not open a duplicate task to rebuild that arrangement. Inspect current branch/deployment evidence before proposing its integration into main.

### Indicator and timeframe parity

Bot EMA seeds from the first supplied historical close; RSI averages the latest 14 gains/losses without Wilder recursion; ATR averages 14 true ranges. Pocket smoothing, initialization, warm-up and forming-candle rules were not verified. Switching an entire Pocket chart to M1 may also switch its visible EMA timeframe; it does not preserve a proven M5 trend calculation.

A faithful comparison needs matched source, exact OHLC/time boundaries, adequate history, price precision, smoothing, seed, gap policy and closed/forming-candle policy. Freeze and compare M5 EMA50/EMA200/ATR14 and M1 RSI14 separately. Matching period numbers or line colors is insufficient.

### Buffer, obstacles and time

The active authority is `send/docs/canonical/active/CANONICAL_MASTER_INDEX_v2.0.0.md`, listing 43 functional authorities. `TIME_MODEL_UNIFIED_CANON_v3.0.0.md:186–198` defines buffer as required directional price distance; `TRADE_PHYSICS_MODEL_SPEC_v1.0.0.md:152–156` binds required space to it. Runtime derives `ATR14(M5) × multiplier`: SMALL 0.30, MEDIUM 0.55, LARGE 1.00 (`market_model.py:344–347`, `algo_params.json:15–18`).

This report does not rename buffer as a stop-loss or override the separate buffer-canon audit. Keep three targets distinct: buffer reached before expiry, favorable price at exact expiry, and broker settlement/P&L. A favorable excursion can reverse before expiry. Canonical research already distinguishes those labels (`RESEARCH_AND_LEARNING_FRAMEWORK_SPEC_v3.0.0.md:185–189`; `TRADE_PHYSICS_INTELLIGENCE_SPEC_v1.0.0.md:298–309`).

Current structural pivots are observable reference zones, not visibility into hidden orders. Directional effective speed sums weighted favorable steps; opposing steps contribute to gross movement, not negative favorable speed (`market_model.py:253–270`). Existing flow efficiency is therefore not net-displacement efficiency or measured liquidity/friction. Distance divided by speed is conditional model time, not knowledge of the next blockage's exact time.

The active time canon separates Model, Execution and Telemetry Time (`TIME_MODEL_UNIFIED_CANON_v3.0.0.md:75–89,410–431`). Preserve that boundary when assessing broker presets and calibrated duration.

## 5. Tools to build or extend, in priority order

All entries are **proposals**, not runtime changes from this audit. Reuse existing modules before creating competing implementations.

| Priority / tool | What it should produce | Acceptance evidence |
|---|---|---|
| P0 — Instrument registry | Venue/product, canonical pair, explicit OTC flag, provider symbol, broker identity, precision, session, quote type | No silent spot↔OTC conversion; missing identity prevents comparison |
| P0 — Permitted data-access assessment | Documented read-only data interface, permitted storage/use, history/tick cadence and authorization | Official interface/permission evidence; no scraped session credential or undocumented client promoted into authority |
| P0 — Paired-feed recorder | Time-aligned observations on the same instrument; source and receive times, clock offset, gaps, candle disagreement and horizon-direction disagreement | Regular and OTC datasets separated; provenance retained; unknown samples remain unknown |
| P0 — Indicator parity harness | Numerical comparison on identical inputs; first-divergence explanation and declared tolerance | EMA, RSI and ATR match declared formulas/warm-up; chart screenshots alone insufficient |
| P0 — Expiry capability matrix | Product-specific duration vs fixed expiry, supported increments, rounding, request vs acceptance time | Observed accepted expiry; no rounding of calibrated horizons without reevaluation |
| P0 — Demo reconciliation journal | Intended signal, accepted entry and final settlement, payout and timing lineage | Broker-confirmed result or UNVERIFIED; no provider WIN relabeled broker WIN |
| P1 — Latency ledger | Source→ingest→decision→API accept→device receipt→human action→broker accept→settlement | p50/p95/p99 per segment and missingness; unobserved receipt/click stays null |
| P1 — Payout-aware analysis | Real contemporaneous payout, WIN/LOSS/DRAW/VOID/UNKNOWN counts and costs | Separate gross return, net profit and stake refund; no permanently assumed92% |
| P1 — Existing severity/expiry lab | Extend current research only after governing source/product scope | Frozen training/holdout, dependence and repeated-comparison treatment; no automatic promotion |
| P2 — Obstacle diagnostics | Existing corridor clearance, ATR margin, wick/body and speed evidence with explanations | Causal decision-time features, incremental out-of-sample improvement or explicit no-benefit finding |
| P2 — Optional feature experiments | ADX regime, Bollinger compression, speed-decay and path-efficiency hypotheses | One predeclared change at a time; no new production gate merely from an appealing chart |
| P2 — Native-signal benchmark | Log native indicator signals as a separate comparator if permitted | No assumed independence, privileged data access or verified predictive edge |
| Later — Copy divergence | Separate eligible leader/follower entry, expiry, payout, rejection and result evidence | Native feature plus lawful eligibility, approved execution and actual divergence measurements |

Price-derived tools cannot see institutional positions or hidden liquidity. The menu's Volume indicator does not establish centralized FX/OTC volume provenance. Do not add volume-profile/order-flow tools on this evidence alone.

Useful candidate definitions for future experiments include ATR-normalized distance to the nearest previously confirmed structural zone; proportion of recent candle travel lost to reversals; and recent favorable-speed change. Existing `trade_physics.py:258–267` and `market_model.py:363–386` already contain clearance, ATR margin, speed ratio, movement stress and wick/noise information. In particular, `buffer/ATR` equals the configured multiplier under the current formula: renaming it an energy score adds no independent information. New path-efficiency definitions must not silently replace canonical `flow_efficiency`.

## 6. Minimal evidence contract for broker-matched research

This is a proposed observation schema, not a new canonical execution authority. Store actual evidence privately. The public repository contains specifications and sanitized aggregates only.

| Group | Required evidence |
|---|---|
| Identity | research_run_id, signal/cycle_id, source/provider, venue/product, symbol, OTC flag, mode, strategy/version/parameter hash, level, buffer mode |
| Market | source_quote_ts_utc, local_received_ts_utc, monotonic receipt time, price/precision/quote type, candle close/completeness, permitted provenance |
| Intent | decision_ts, stage, direction, intended entry validity interval, model duration, calibrated execution duration and calibration identity |
| Delivery | request/send/API-accept times; actual device receipt and user action only if observed; missingness and clock-offset evidence |
| Broker observation | opaque private order reference, accepted entry_ts/price, exact expiry_ts/settlement price, actual payout, rejection/void/draw reason |
| Labels | independent buffer-reach and terminal-direction labels; broker settlement state; source/domain; unknown reasons; costs and net result when known |

No credentials, session strings, identity documents, wallet addresses, raw account history or private notifications belong in git. Do not fabricate broker ticks by interpolating pixels or provider candles. A manual note is an explicitly labeled observation, not a certified automated feed.

### Payout arithmetic

For unit stake, net win return `r`, total-loss return `-1` and refunded draw `0`:

`expected_return = P(WIN) × r - P(LOSS)`.

Without draws/voids/costs, break-even decisive win rate is `1/(1+r)`.

| Net win payout | Break-even rate |
|---:|---:|
| 92% | 52.08% |
| 80% | 55.56% |
| 70% | 58.82% |

These are mathematical examples, not observed returns or sufficient acceptance thresholds. With variable payouts calculate trade-level returns; an unweighted headline win rate is insufficient. Unknown outcomes are not losses, wins or draws. No martingale or stake escalation is proposed.

### Research protocol and stop conditions

Reuse `send/docs/EXECUTION_EXPIRY_CALIBRATION_PROTOCOL_V1.md`: it already predeclares pressure-bias candidates, chronological training/holdout, overlap handling, unknown labels and multiple-level adjustment. Its current Finnhub evidence does not transfer to another source, GBP/USD, or Pocket OTC. Keep the existing cohort intact; establish a separate governed cohort for a changed source/product.

Existing level 0–20 experiments preserve data, structure, time and Physics gates; level 0 is not permission to bypass data correctness. TPS/score are deterministic quantities, not calibrated win probabilities. Predeclare the hypotheses and evaluation metric, separate regular/OTC and sessions, thin correlated/overlapping entries, freeze parameters before holdout and report all candidates/missing data. Existing numerical cohort rules are experiment policy, not proof of independent observations or sufficient broker validity.

Stop a comparison on unknown identity, stale/missing data, unresolved clock offset, source/version drift, missing actual expiry, undocumented payout or unverified result. Report insufficiency rather than extending the experiment until a target is reached. A best-looking level does not become production merely by ranking first.

## 7. Delivery phases and shared-agent ownership

1. **Documented access and identity:** clarify eligibility, data rights and custom-integration interfaces; record supported products and exact symbol identity. This does not block offline/source/UI research.
2. **Read-only parity:** matched recording and indicator comparison; extend observed evidence without activating orders or changing strategy.
3. **Broker-demo validation:** subject to applicable eligibility and explicit operating scope, observe manual/native demo operations and reconcile accepted timestamps, prices, expiry and settlement. Do not infer fills from button clicks.
4. **Prospective strategy experiments:** reuse the existing lab with broker-matched input/labels, frozen candidate definitions and untouched chronological evaluation.
5. **Review:** publish evidence and gaps; any broker implementation, production gate or canonical change is a separately governed scope. No automatic activation follows from this report.

Coordinate as bounded tasks: data/source owner handles access and identity; strategy owner handles indicator/feature parity; timing owner handles execution-expiry and latency; outcome owner handles settlement/economics; integration guardian verifies scope/authority separation. App #236 remains its own lane. The current report changes only this audit directory; it does not promote new canon, alter buffer semantics, merge app work or change runtime configuration.

## 8. Verification and remaining unknowns

Existing targeted regression command executed against audited main:

```sh
PYTHONPATH=send python -m pytest -q tests/canonical/unit/test_market_data_provider_control.py tests/canonical/unit/test_finnhub_market_data_foundation.py tests/canonical/unit/test_twelvedata_live_stream.py tests/canonical/unit/test_market_model.py tests/canonical/unit/test_time_model.py tests/canonical/unit/test_runtime_execution_calibration.py tests/canonical/unit/test_live_score_severity_research.py tests/canonical/unit/test_signal_severity_analysis.py
```

Result: **128 passed**, one upstream anyio/pytest deprecation warning, 6.57 seconds. No source code changed. Tests establish the specified offline behaviors only. No full-suite, Railway, device-notification, live-order, live-payout or profitability acceptance is claimed by this audit.

Unresolved: authorized custom interface and data licence; account/product eligibility; exact broker asset identifiers; indicator formula parity; clock offsets and receipt latency; accepted duration/fixed-expiry behavior; broker data/settlement reconciliation; demo-to-real differences; and current deployment state. Built-in bot configuration and its inbound-signal capability were not tested. Current public API authorization remains unknown.

## 9. Sources and provenance

Official public sources retrieved on **2026-11-05**. Product/blog descriptions are vendor claims, not independent performance tests. Their publication dates and current availability are different facts. UI observations are transient and are recorded separately above.

| ID | Primary source | Evidence scope |
|---|---|---|
| W1 | [Public Offer](https://pocketoption.com/en/public-offer/) | Contractual constraints; sections General Provisions, Trading Operations and List of Countries |
| W2 | [Quick Start](https://pocketoption.com/en/quick-start/) | Public product guide and links to native documentation |
| W3 | [OTC Assets Schedule](https://pocketoption.com/en/assets-otc/) | OTC product schedule, timezone, link to company OTC explanation |
| W4 | [PocketOption OTC explanation](https://pocketoption.medium.com/myth-2-trading-on-otc-is-not-worth-a-risk-b300b75a289) | Company article dated 2020-01-10, still linked by W3; distinction from general-market prices |
| W5 | [Official Telegram Signal Bot description](https://pocketoption.com/blog/en/interesting/trading-platforms/pocket-option-trading-signal-bot/) | Vendor article dated 2025-03-24; advertised settings/automation, not custom API authorization |
| W6 | [Trading Bot article](https://pocketoption.com/blog/en/knowledge-base/trading/pocket-option-trading-bot/) | Vendor article dated 2025-05-07; generic API statements, not a developer specification |
| W7 | [Payment Policy](https://pocketoption.com/en/payment-policy) | Payment mechanics; does not establish a geographic crypto exception |
| W8 | [Official Payment Methods overview](https://pocketoption.com/blog/en/product-guides/pocket-option-payment-methods-overview/) | Discusses crypto alongside EEA service exclusion |
| W9 | [Central Bank of Ireland — MiFID Requirements](https://www.centralbank.ie/regulation/industry-market-sectors/investment-firms/mifid-firms/mifid-requirements) | Current Intervention Measures section |
| UI1 | [Demo terminal](https://pocketoption.com/en/cabinet/demo-quick-high-low/) | Authenticated UI feature observations, not a public live data feed |
| UI2 | [Applications](https://pocketoption.com/en/cabinet/applications/) | Authenticated official app catalog inspected; no linked bot activated |
| UI3 | [Platform Guide](https://pocketoption.com/en/cabinet/platform-guide/) | Authenticated guide navigation headings; not used as proof of untested functionality |

Repository citations use the pinned SHA above, not an assumption that future main is unchanged. Main and app branch were inspected separately. Read this report together with the active Master Index, existing expiry-calibration protocol and current deployment evidence; it cannot supersede any of them.

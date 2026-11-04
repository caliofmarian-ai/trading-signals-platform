# Live trading-system tests — 2026-11-04

## Result and scope

The complete local repository suite passes: **1,788 passed in 46.79 seconds**, with no failures or skips. Critical module compilation, `git diff --check` and dependency consistency also pass. This validates the proposed source changes, not their production deployment or trading profitability.

Production was inspected through Railway and the already authenticated Owner account in Telegram. The tested deployment remains `5f5e468a0e6ce1e20406f4e76ebcb308d0ed13fd`, Railway status `SUCCESS`, one of one replicas online, no recent failures in the inspected eight-hour window. No broker execution, payments, provider changes, threshold changes, role grants, membership changes or synthetic signal publication were performed.

## Automated evidence

Command: `PYTHONPATH=send python -m pytest -q` using Python 3.12 and the pinned repository requirements.

- Initial full run: 1,783 passed, three failures. One boot-test failure was caused by the extra `SHADOW_MODE=1` test-launch override; it passes under the normal CI command without source changes. Two genuine repeatable test failures came from fixed October 30 event fixtures evaluated against the moving wall clock. The two tests now freeze the observation clock to their fixture date; production window filtering is unchanged.
- Added two regression cases, for `REJECT` and `NO_SIGNAL` with a prior FSM opportunity ID. Both reproduce the exact observed production exception before the fix and pass after it. They also assert no signal identity in serialized decisions and no signal handoff, preserving rejection blockers.
- Focused decision assembly, FSM and lifecycle regressions: 51 passed.
- Final full suite: 1,788 passed, zero failed, zero errors, zero skipped. It includes canonical contracts, strategy/FSM, persistence/recovery, distribution and objective telemetry, security, Telegram application/transport, billing adapter fixtures and repository governance.

## Confirmed live journeys

| Journey | Observed result |
|---|---|
| Telegram account and project access | PASS: existing authenticated account, project group and bot accessible |
| Private `/admin` | PASS: Owner role and canonical admin root visible |
| Private Operations → Diagnose | PASS: running, market data ready, recovery healthy, shadow on, broker disabled |
| Private `/audit_runtime` | PASS: actual JSON document delivered and downloaded; generated at `2026-11-04T06:05:15Z` |
| Decision Visibility | PASS: actual persisted decision, rejection reasons and model evidence displayed |
| Symbols & Coverage | PASS: Finnhub exclusive, EUR/USD effective scope locked, Twelve Data inactive |
| Distribution | PASS for read-only configuration rendering; route mappings and zero counters do not prove external delivery |
| Back navigation | PASS for tested panels, with noticeable delayed responses |
| Group `ADMIN_COMMANDS`, `/diagnose` | PASS: actual runtime diagnosis returned in the configured topic |
| Group `/diagnose@dropi_trading_bot` | FAIL: `Unknown admin command.`; separately recorded as issue #215 |
| Group `SIGNALS_LIVE` | No new signal delivery observed; newest visible entries were from September 2 |

## Real market/strategy evidence

The generated runtime audit confirms `RECEIVING_REAL_TICKS`, `REAL_TICK_CONFIRMED`, Finnhub persistence active, market-data age one second against a ten-second freshness limit, and 500 real stored candles for each of M1 and M5. Contiguous heads are M1=417 and M5=500 against the unchanged minimum of 201. Older gaps outside the necessary contiguous M1 head remain disclosed; missing candles were not synthesized.

The runtime recorded 47,592 strategy evaluations. All 50 decisions in the bounded recent engine sample (`06:03:00.476Z`–`06:04:53.615Z`) were `REJECT`. This is evidence of actual strategy evaluation, not a whole-day rejection rate or measured win rate.

The bounded recent-error sample contains 49 `non-actionable decisions must not expose signal_id` errors and one slow-callback warning. It is a last-50 sample, not a global rate. Later Telegram diagnosis also displayed callback delays and a callback acknowledgement failure; issue #202 remains unresolved.

Raw audit data, account identifiers, tokens, prices and other chat content are intentionally excluded. `runtime_summary.json` contains an allowlisted operational summary and the raw artifact checksum.

## Proposed strategy correction

`decision_assembly.py` previously evaluated the supplied opportunity-ID branch before checking whether the new decision was actionable. Consequently, an existing FSM opportunity could give a `REJECT` or `NO_SIGNAL` an illegal non-null signal ID and cause `DecisionObject` validation to raise.

The assembler now checks the canonical actionable-kind set first. Only PRE/CONFIRM/OPEN_NOW can inherit or create a signal ID. Non-actionable decisions retain `None`; scoring, thresholds, blockers and FSM ownership remain unchanged. The existing actionable-opportunity regression remains green.

## Remaining live acceptance boundaries

- **Correction deployment:** pending review/integration and a subsequent real production observation of the fixed case. The production SHA above does not contain this patch.
- **Telegram dispatch (#215):** addressed diagnostic command fails while its plain equivalent works. Do not silently normalize arbitrary other-bot commands or weaken the chat/topic/role gates when fixing it.
- **Telegram latency:** live slow processing and acknowledgement failures remain observable (#202).
- **Signal delivery:** existing `FINNHUB_PERSONAL_USE_DISTRIBUTION_BLOCKED` code gate is preserved (#208); read-only mapping readiness is not provider distribution authorization or an end-to-end delivery proof.
- **Outcomes:** no newly published signal → objective expiry result journey was verified. No claimed 30 signals/hour, 80% win rate or profitability.
- **Other identities:** non-Owner roles were tested in isolated automated fixtures, not through real independent accounts.
- **Billing:** tests use isolated fixtures; no real Revolut/KuCoin transactions, paid entitlement or channel-membership lifecycle was executed. #168/#169 remain live acceptance gates.
- **Broker:** remains disabled. Real financial transactions were not part of this test run.

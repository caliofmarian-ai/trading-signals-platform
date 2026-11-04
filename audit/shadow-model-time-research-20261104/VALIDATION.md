# Validation — private Model Time research

Base production source: `e8728e9f8da453739cecdf9175719ed65979e833` (#216), observed Railway SUCCESS. The complete baseline suite had 1,788 tests.

Proposed source validation on 2026-11-04:

- 26 new isolated regression cases cover both directions and WIN/LOSS/DRAW, no-lookahead entry, bad/stale/future/synthetic/provider-mismatched observations, explicit UNKNOWN, immutable final labels, provider switches, restart gaps, duplicate opportunities, disabled/execution-enabled guards, corrupt evidence, worker integration, independent truth storage and index-write recovery.
- Focused collector, canonical telemetry, execution model and persistence-boundary suite: **46 passed**.
- Complete repository suite: **1,814 passed in 50.85 seconds**, no failed/skipped tests.
- Critical module compilation and `git diff --check`: PASS.

The worker integration regression verifies that collecting a private research entry does not create official trade telemetry or make absent ExecutionCalibration available. Summary output excludes private prices and opportunity identities. Failure of research storage and even its warning logger does not escape into canonical signal execution.

Activation is separately observable through `TSP_SHADOW_RESEARCH_EVIDENCE` and `runtime_status.shadow_model_time_research`. It is not proven by tests or variable-name presence. A successful deployment and actual `enabled=true` worker evidence are required before claiming this experiment is running. Actual opportunity enrollment and completed observations may initially be zero; real WIN/LOSS/DRAW/UNKNOWN remain unproven until observed.

Remaining manual-signal launch dependencies include #217 (governed Execution Time calibration), #208 (provider/route authorization and real delivery acceptance), and the selected broker's instrument, quote and contract compatibility. This change does not resolve those dependencies or certify profit.

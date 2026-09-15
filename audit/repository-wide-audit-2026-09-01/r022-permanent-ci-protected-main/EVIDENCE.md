# R-022 — Permanent repository-wide CI and protected-main gate evidence

Issue: #150  
Parent remediation: #97  
Assigned baseline: `e520a51269a7ff34ffc7398276b75005dd67f20f`

## Verified pre-change repository state

At the assigned baseline:

- `main` resolves exactly to `e520a51269a7ff34ffc7398276b75005dd67f20f`;
- GitHub reports `main` as `protected: false`;
- required status-check contexts/checks are empty;
- the repository ruleset collection is empty;
- `.github/workflows/` contains only `provider-selector-validation.yml`;
- that historical workflow validates pull requests to `main` and manual dispatch, but does not validate the resulting push/merge commit on `main`.

## Permanent CI architecture decision

R-022 replaces the provider-specific workflow identity with one repository-wide workflow authority:

- workflow file: `.github/workflows/repository-ci.yml`;
- workflow display name: `Repository CI`;
- stable required check/job name: `Required Repository CI`;
- triggers: every pull request targeting `main`, every push to `main`, and manual dispatch;
- no path/path-ignore filters;
- no `continue-on-error`;
- read-only repository contents permission;
- Python 3.12, matching the established CI runtime;
- explicit exact-SHA checkout plus `git rev-parse HEAD` equality assertion;
- provider-selector focused regression retained;
- Telegram Admin focused regression retained;
- critical canonical/contract regression layer retained explicitly;
- complete `python -m pytest -q` repository regression remains mandatory.

The `push` trigger is intentional. Pull-request validation certifies the exact proposed branch head, while push-to-main validation certifies the actual commit that becomes canonical `main`. Railway deployment status does not substitute for either GitHub CI proof.

## Exact-head semantics

For a pull request, checkout is pinned to `github.event.pull_request.head.sha`. For push/manual contexts it resolves to `github.sha`. The workflow then compares the checked-out `git rev-parse HEAD` value to that expected SHA and fails immediately on mismatch.

This keeps the tested commit identity explicit instead of relying on the default pull-request merge ref checkout behavior.

## Critical regression coverage

The permanent job keeps dedicated early gates for:

1. the R-022 workflow governance contract itself;
2. provider selector control;
3. Telegram Admin restoration/regression behavior;
4. canonical contract tests plus the R-021 primary-v3 Event Schema/distribution/research migration regressions;
5. the full repository test suite.

These focused layers do not replace the full suite; they fail earlier and make loss of critical coverage visible.

## Branch/ruleset protection authority

The connected ChatGPT GitHub App can write Actions workflows, repository contents, issues and pull requests, but its installation permission set does not include GitHub `administration`. No connector action is exposed for mutating branch protection or repository rulesets.

Therefore R-022 must not claim that protected-main enforcement has been enabled programmatically.

### Minimal Owner administrative action

After `Required Repository CI` has appeared as a successful check on the R-022 pull request, configure protection for `main` in GitHub repository settings using either a branch ruleset or classic branch protection with these effective rules:

- target branch: `main`;
- require a pull request before merging;
- require status checks to pass before merging;
- required check: **`Required Repository CI`**;
- require the branch to be up to date before merging;
- do not allow bypass of the protection for administrators/roles that can otherwise bypass it;
- do not allow force pushes;
- do not allow branch deletion.

After saving the rule, independently re-inspect the `main` branch/ruleset state. Closure evidence must show protection active and `Required Repository CI` configured as required. Until that administrative setting is verified, repository CI is implemented but direct-push prevention is not proven.

## Scope boundaries preserved

R-022 does not change:

- `requirements.txt`;
- canonical document semantics/status metadata;
- provider or symbol policy;
- strategy/FSM mathematics or lifecycle;
- 2-second engine cadence;
- Telegram authorization/RBAC;
- Railway variables/secrets;
- autonomous mutation state;
- broker execution state.

Final exact-head Actions run, test counts and post-change branch-protection inspection are recorded in the pull-request/orchestrator evidence after the final head exists.

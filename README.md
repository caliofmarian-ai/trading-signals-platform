# trading-signals-platform

Repository baseline initialized from uploaded archive content without canonical reconciliation.

## Current repository status

- Uploaded archive content has been imported under `/home/runner/work/trading-signals-platform/trading-signals-platform/send`.
- Source artifacts were preserved as provided, including historical, backup, and duplicate tracks.
- Canonical governance reconciliation has been completed (see Canonical Reconciliation 01 below).

## Canonical Documentation

- [Authoritative Canonical Master Index](./send/docs/canonical/active/CANONICAL_MASTER_INDEX_v1.0.0.md)

## Baseline documentation

- [Document Inventory](./DOCUMENT_INVENTORY.md)
- [Repository Baseline Report](./REPOSITORY_BASELINE_REPORT.md)

## Audits

- [Canonical Audit 01](./audit/canonical-audit-01/)
- [Canonical Reconciliation 01](./audit/canonical-reconciliation-01/)
- [Railway Deployment Preparation 01](./audit/railway-deployment-preparation-01/)

## Canonical offline tests

- Default offline command: `PYTHONPATH=send python -m pytest -q tests`
- Canonical BATCH-08 test reports: `audit/remediation-batch-08/`

## Railway operator docs

- [Operator Runbook](./audit/railway-deployment-preparation-01/RAILWAY_OPERATOR_RUNBOOK.md)

# RAILWAY_OPERATOR_RUNBOOK.md

1. Open Railway.
2. Create a new project or select an existing safe project.
3. Connect `caliofmarian-ai/trading-signals-platform`.
4. Select the intended branch.
5. Add one persistent volume.
6. Mount the volume at `/data`.
7. Add non-secret variables from `/.env.example`.
8. Add secrets (`TWELVE_DATA_API_KEY`, optional `TELEGRAM_BOT_TOKEN`, optional `COMMUNITY_FEEDBACK_SALT`).
9. Confirm the start command is `PYTHONPATH=send python -m scripts.railway_start`.
10. Perform the first deployment.
11. Read init output; confirm directories/config were seeded.
12. Run the readiness command inside the service environment: `PYTHONPATH=send python -m scripts.railway_healthcheck --mode readiness`.
13. Confirm `SHADOW_MODE=true` and `ENABLE_BROKER_EXECUTION=false`.
14. Confirm there is still no broker execution, Pocket Option integration, or paper trading.
15. Only after the base service is healthy, add Telegram credentials and private test-channel IDs, then set `ENABLE_TELEGRAM=true`.
16. If startup fails, keep the same volume, review logs, fix configuration, and redeploy; if needed, roll back the code revision without deleting persisted state.

Do **not** let Railway auto-insert real secrets into repository files.

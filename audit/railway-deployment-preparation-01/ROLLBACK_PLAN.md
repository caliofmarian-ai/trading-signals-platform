# ROLLBACK_PLAN.md

1. Keep the existing Railway volume attached.
2. Roll back to the previous repository revision if a deployment-preparation regression is found.
3. Re-deploy with the same env vars and volume.
4. If the issue is config-only, fix the bad env/config and redeploy without deleting persisted data.
5. Only delete/reset the volume if the owner intentionally wants a fresh shadow environment.

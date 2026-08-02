# Test Matrix

## Dispatcher-level APP navigation
- `/start` seeds Home and generation.
- Home → Status records Home as parent.
- Status → Back returns Home.
- Home → Help → Status → Back unwinds correctly.
- Refresh does not grow APP history.
- Stale generation after `/start` is rejected.
- APP callbacks use the real chat/topic session key.
- Slash and callback entry points produce equivalent APP state.
- Back without history falls back safely.
- Owner APP admin entry exposes APP Back/Home only when there is a real APP parent.

## Admin navigation regressions
- Roles reload confirm cancel returns to Roles.
- Successful Roles reload returns to Roles and Cancel performs no mutation.
- Profile selector → confirmation → Cancel returns to selector without mutation.
- Profile apply returns to the selector/current-state surface.
- Files Home → directory → Prev/Next → Files Home stays on one edited anchor.
- Docs list/download leaves the docs listing anchor active.
- Research report download leaves the research anchor active.
- Operations → Engine → Refresh preserves Operations as the immediate parent.
- System Health → Engine → Refresh preserves System Health as the immediate parent.
- Operations → Diagnose → Refresh preserves Operations as the immediate parent.
- System Health → Diagnose → Refresh preserves System Health as the immediate parent.
- Strategy-context symbol mutations preserve Strategy as parent.
- Diagnose audit callbacks preserve originating parent on error.
- Admin root renders remain canonical while allowing optional APP Back on APP entry.

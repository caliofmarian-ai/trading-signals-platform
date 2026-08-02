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
- Strategy-context symbol mutations preserve Strategy as parent.
- Diagnose audit callbacks preserve originating parent on error.
- Admin root renders remain canonical while allowing optional APP Back on APP entry.

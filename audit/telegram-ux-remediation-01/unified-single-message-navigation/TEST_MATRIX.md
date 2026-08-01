# Test Matrix

1. `/start → /status → /admin → /engine → /symbols` one message: **covered**
2. `Home → Admin → Engine → Admin` one message: **covered**
3. `Admin → Distribution → Symbols & Coverage` one message: **covered**
4. Slash then callback one message: **covered**
5. Callback then slash one message: **covered**
6. Same page repeated no-op: **covered** (`message is not modified` tests)
7. Different page edits same message: **covered**
8. Successful ADMIN_NAV edit updates tracking: **covered**
9. Failed ADMIN_NAV edit sends one tracked replacement: **covered**
10. Deleted active message sends one replacement only: **covered**
11. Same user different chats isolated: **covered**
12. Same user different topics isolated: **covered**
13. File delivery remains separate document: **covered**
14. Signal/operational publishing unaffected: **covered** (existing canonical/batch outcome+distribution tests)
15. Unauthorized/rate-limited navigation no accumulation: **covered**
16. Representative end-to-end one-message journey: **covered**

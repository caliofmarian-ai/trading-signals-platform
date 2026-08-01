# Updated Live Acceptance Checklist

## A. Clean baseline
- [ ] Delete the private conversation.
- [ ] Send `/start` and confirm exactly one bot message A.
- [ ] Send `/admin` and confirm message A is edited; no message B.
- [ ] Send `/engine` and confirm message A is edited.

## B. Restart
- [ ] Restart Railway without deleting message A.
- [ ] Wait for the poller startup line identifying exactly one polling instance.
- [ ] Send `/admin` and confirm message A is edited.
- [ ] Send `/engine` and confirm message A is edited.
- [ ] Send `/start` and confirm message A is edited.

## C. Redeploy
- [ ] Redeploy the same revision or this corrective revision.
- [ ] Send `/status` and confirm message A is edited.
- [ ] Press Home and confirm message A is edited.

## D. Deleted-message recovery
- [ ] Delete message A.
- [ ] Send `/admin` and confirm exactly one replacement message B.
- [ ] Send `/engine` and confirm message B is edited.
- [ ] Confirm no message C appears.

## E. Responsiveness and evidence
- [ ] Repeated commands continue receiving responses.
- [ ] Bot never becomes silent.
- [ ] Railway logs show one poller instance per runtime process.
- [ ] Persisted state contains only approved minimal metadata.

# Security and Privacy Analysis

## Navigation integrity
- APP Back only renders supported canonical page ids.
- Unsupported or looped APP history entries fall back to Home.
- Stale APP generations are rejected.

## Authorization re-checks
- Admin entry continues to check owner/admin-topic access.
- Roles reload checks both context and permission at execution time.
- Existing file path validation remains the authority for file/document downloads.

## Privacy boundaries
- Session state is separated by chat and topic, so one chat/topic cannot drive another session's navigation.
- No new secret-bearing data is stored in APP navigation state.

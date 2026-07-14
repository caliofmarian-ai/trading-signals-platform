# OPEN_FINDINGS

## Remaining limitations
- Incident aggregation state is process-local; it resets on process restart.
- Generic critical incidents escalate and aggregate, but explicit recovery messaging is currently implemented only for incidents that have a clear runtime recovery signal in this remediation scope (notably Twelve Data HTTP 429).
- Operator notifications depend on valid Telegram admin destination configuration and a working Telegram bot token.

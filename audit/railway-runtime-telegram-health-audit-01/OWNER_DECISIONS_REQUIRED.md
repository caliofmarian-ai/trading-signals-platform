# OWNER_DECISIONS_REQUIRED

1. **Command UX policy**
   - Should `/start`, `/help`, `/status` be restored in canonical bot path?
2. **Unsupported command behavior**
   - Preferred behavior: explicit "unsupported command" reply vs silent ignore.
3. **Admin reply routing**
   - Should admin replies always target admin topic, or reply in originating chat context?
4. **Startup/recovery notifications**
   - Destination: admin control chat or admin proof chat?
5. **Error escalation policy**
   - Thresholds for Telegram alerting on repeated 429/schema failures.
6. **Legacy parity strategy**
   - Reintroduce external sidecar behavior (if needed) vs keep single-process canonical model.
7. **BATCH-09 retrospective**
   - Keep deletion classification as-is, or reclassify `legacy/bot_control.py` as externally-operated historical component.

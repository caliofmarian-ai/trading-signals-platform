# STATE_PERSISTENCE_SPEC

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

STATE_PERSISTENCE_SPEC

BinaryBot — Runtime State Persistence Specification
Version: 1.0.0
Status: Canonical

Linked Documents:
FSM_DECISION_ENGINE_SPEC_v1.0.0.md
SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md
CHANNEL_CONFIG_SPEC_v2.0.0.md
OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

---

1. PURPOSE

This document defines how runtime state is stored and recovered by the system.

State persistence ensures that system behaviour remains consistent across restarts.

Without persistent state the following problems may occur:

• duplicate signals  
• counter corruption  
• silent tiers reactivating incorrectly  
• cooldown bypass  

Persistent state is mandatory for stable trading signal operations.

---

2. STATE STORAGE LOCATION

Runtime state must be stored on disk.

Recommended directory:

/opt/binarybot/state/

Example files:

tier_counters.json
tier_state.json
system_state.json
cooldowns.json
focus_state.json

These files must be loaded during system startup.

---

3. TIER COUNTERS

File:

tier_counters.json

Structure example:

{
  "FREE": 2,
  "BASIC": 7,
  "PRO": 14,
  "ELITE": 0
}

Meaning:

Number of OPEN_NOW signals successfully published today per tier.

Rules:

• Counters increase only after successful publish  
• Counters persist across restarts  
• Counters reset only during daily reset  

---

4. TIER STATE

File:

tier_state.json

Structure example:

{
  "FREE": "ACTIVE",
  "BASIC": "ACTIVE",
  "PRO": "ACTIVE",
  "ELITE": "ACTIVE"
}

Possible values:

ACTIVE  
SILENT  

Rules:

When OPEN_NOW limit is reached:

tier → SILENT

Silent tiers receive no signals.

Tier states must persist across restarts.

---

5. RESET STATE

File:

system_state.json

Structure example:

{
  "last_daily_reset": "2026-03-04"
}

Purpose:

Prevents multiple resets during the same trading day.

Reset logic:

IF current_date_london != last_daily_reset  
AND time >= 08:10 London  

→ execute reset

Then update:

last_daily_reset = today

---

6. COOLDOWN STATE

File:

cooldowns.json

Structure example:

{
  "EURUSD": 1710001220,
  "GBPUSD": 1710001450
}

Meaning:

Timestamp until which symbol is locked.

Rule:

IF now < cooldown_until  
→ symbol remains in COOLDOWN state.

Cooldown must persist across restarts.

---

7. FOCUS STATE

File:

focus_state.json

Structure example:

{
  "watchlist": ["EURUSD","GBPUSD"]
}

Rules:

• Maximum 2 symbols in watchlist  
• Reloaded on restart  
• Prevents sudden focus changes  

---

8. WRITE SAFETY

State files must be written atomically.

Recommended approach:

write temp file  
rename temp file → target file

Example:

tier_counters.tmp → tier_counters.json

This prevents corruption during crashes.

---

9. STARTUP BEHAVIOR

On system startup:

1. Load all state files
2. Validate data integrity
3. Restore tier states
4. Restore counters
5. Restore cooldowns
6. Restore watchlist

If a file is missing:

System must recreate it with default values.

---

10. GUARANTEES

If persistence is implemented correctly:

• counters survive restarts  
• silent tiers remain silent  
• cooldowns cannot be bypassed  
• focus state remains stable  
• reset logic remains deterministic  

This guarantees safe long-running bot operation.

---

End of STATE_PERSISTENCE_SPEC.md

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.

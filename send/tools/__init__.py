from __future__ import annotations

import importlib
import os


# Preserve the canonical R-019 runtime by default. When the Owner explicitly
# supplies either local civil-time scheduling variable, expose the timezone-
# aware adapter through the same package-level import used by system_boot,
# railway_init, and the one-shot CLI. Partial/invalid local configuration is
# intentionally selected too so it fails closed instead of silently falling
# back to the legacy UTC scheduler.
if os.getenv("STRATEGY_AUDITOR_DAILY_TIME", "").strip() or os.getenv("STRATEGY_AUDITOR_TIMEZONE", "").strip():
    importlib.import_module("tools.strategy_auditor_runtime")
    strategy_auditor_runtime = importlib.import_module("tools.strategy_auditor_local_time")

from __future__ import annotations

import os
import sys

from scripts.railway_common import apply_path_contract, resolve_base_dir
from core.observability_logger import send_control_notification
from scripts.railway_healthcheck import readiness_report
from scripts.railway_init import initialize_for_railway


def main() -> int:
    try:
        base_dir = resolve_base_dir(require_explicit=True)
        apply_path_contract(base_dir)
        initialize_for_railway(base_dir=base_dir)
        readiness_report(base_dir=base_dir)
        os.environ["RAILWAY_READINESS_EVALUATED"] = "1"
        send_control_notification("BOT STARTING", "BinaryBot Railway runtime passed initialization and readiness checks.")

        from runtime.system_boot import start_system

        start_system()
        return 0
    except Exception as exc:
        send_control_notification("STARTUP BLOCKED", f"Railway startup failed safely: {exc}")
        print(f"Railway start failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import contextlib
import os
import sys
from typing import Any, Dict

from scripts.railway_common import apply_path_contract, resolve_base_dir
from core.observability_logger import send_control_notification
from scripts.railway_healthcheck import readiness_report
from scripts.railway_init import initialize_for_railway
from scripts.admin_role_reconcile import reconcile_primary_admin_from_source


def _install_telegram_ui_diagnostic_stream_routing() -> None:
    """Route healthy UI initialization diagnostics to Railway stdout.

    `core.telegram_app_nav` historically writes its diagnostic payload through
    stderr.  Rewriting that large navigation module solely for the deployment
    stream boundary would create unnecessary change surface.  Railway startup
    therefore installs a narrow adapter before `runtime.system_boot` imports
    and uses the module.  Only a successful/deferred/skipped
    TELEGRAM_UI_STATE_INITIALIZED event is redirected to stdout; every warning
    or error diagnostic keeps the original stderr path.
    """

    from core import telegram_app_nav

    original = telegram_app_nav._emit_stdout_diagnostic
    if getattr(original, "_railway_stream_routed", False):
        return

    def _routed(code: str, context: Dict[str, Any]) -> None:
        status = str((context or {}).get("status") or "").strip().lower()
        healthy_initialization = (
            code == "TELEGRAM_UI_STATE_INITIALIZED"
            and status in {"ok", "deferred", "skipped"}
        )
        if healthy_initialization:
            with contextlib.redirect_stderr(sys.stdout):
                original(code, context)
            return
        original(code, context)

    setattr(_routed, "_railway_stream_routed", True)
    telegram_app_nav._emit_stdout_diagnostic = _routed


def main() -> int:
    try:
        base_dir = resolve_base_dir(require_explicit=True)
        apply_path_contract(base_dir)
        initialize_for_railway(base_dir=base_dir)
        reconcile_primary_admin_from_source(base_dir=base_dir)
        readiness_report(base_dir=base_dir)
        os.environ["RAILWAY_READINESS_EVALUATED"] = "1"
        send_control_notification("BOT STARTING", "BinaryBot Railway runtime passed initialization and readiness checks.")

        _install_telegram_ui_diagnostic_stream_routing()
        from runtime.system_boot import start_system

        boot_result = start_system()
        if boot_result is False:
            raise RuntimeError("Runtime system boot returned a blocked startup state")
        return 0
    except Exception as exc:
        send_control_notification("STARTUP BLOCKED", f"Railway startup failed safely: {exc}")
        print(f"Railway start failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

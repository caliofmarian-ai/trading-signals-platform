from __future__ import annotations

import sys

from scripts.railway_common import apply_path_contract, resolve_base_dir
from scripts.railway_healthcheck import readiness_report
from scripts.railway_init import initialize_for_railway


def main() -> int:
    base_dir = resolve_base_dir(require_explicit=True)
    apply_path_contract(base_dir)
    initialize_for_railway(base_dir=base_dir)
    readiness_report(base_dir=base_dir)

    from runtime.system_boot import start_system

    start_system()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

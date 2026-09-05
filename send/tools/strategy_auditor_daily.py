import json
import sys
from typing import Any, Dict, Optional

from tools import strategy_auditor_runtime


def run_auditor(*, now=None, settings_path: Optional[str] = None) -> Dict[str, Any]:
    return strategy_auditor_runtime.run_auditor(
        mode="manual",
        now=now,
        settings_path=settings_path,
    )


def main() -> int:
    result = run_auditor()
    print(json.dumps(strategy_auditor_runtime.result_for_cli(result), indent=2, sort_keys=True))
    return strategy_auditor_runtime.exit_code_for_result(result)


if __name__ == "__main__":
    sys.exit(main())
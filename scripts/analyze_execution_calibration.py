"""Analyze a private expiry-calibration state; no activation/network/broker path."""
import json
import sys
import time
from pathlib import Path
from intelligence.execution_expiry_calibration import _read, analyze


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Expected one private calibration state JSON file")
    state = _read(Path(sys.argv[1]))
    if state is None:
        raise SystemExit("Calibration source is missing")
    print(json.dumps(analyze(state, now_ts=time.time()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

"""Bounded, price-free timing diagnostics; never a sampling or strategy gate."""
from collections import deque
import math
import time

WINDOW = 128


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return {"sample":0,"min":None,"p50":None,"p95":None,"max":None}
    return {"sample":len(ordered),"min":ordered[0],"p50":ordered[math.ceil(.5*len(ordered))-1],
            "p95":ordered[math.ceil(.95*len(ordered))-1],"max":ordered[-1]}


class LoopTimingEvidence:
    def __init__(self,poll_seconds,*,monotonic=time.monotonic):
        if not math.isfinite(poll_seconds) or poll_seconds<=0:
            raise ValueError("INVALID_POLL_INTERVAL")
        self.poll_seconds=poll_seconds
        self.monotonic=monotonic
        self.intervals=deque(maxlen=WINDOW)
        self.work=deque(maxlen=WINDOW)
        self.started=None
        self.last_report_slot=None

    def begin(self):
        stamp=self.monotonic()
        if self.started is not None and stamp>=self.started:
            self.intervals.append(stamp-self.started)
        self.started=stamp

    def finish(self,*,now_ts,provider):
        stamp=self.monotonic()
        if self.started is not None and stamp>=self.started:
            self.work.append(stamp-self.started)
        slot=int(now_ts//60)
        if self.last_report_slot is not None and slot<=self.last_report_slot:
            return None
        self.last_report_slot=slot
        return {"protocol":"TELEMETRY_LOOP_TIMING_V1","observed_at":now_ts,
                "provider":provider if provider in {"FINNHUB","TWELVE_DATA"} else "UNAVAILABLE",
                "scope":"LAST_128_MEASURED_LOOP_INTERVALS_AND_WORK_DURATIONS_IN_THIS_PROCESS",
                "configured_sleep_seconds":self.poll_seconds,
                "loop_interval_seconds":distribution(self.intervals),"loop_work_seconds":distribution(self.work),
                "loop_intervals_gt_2s":sum(value>2 for value in self.intervals),
                "no_market_price_content":True}

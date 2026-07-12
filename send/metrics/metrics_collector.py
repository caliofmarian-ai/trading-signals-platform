# /opt/binarybot/metrics/metrics_collector.py
# BinaryBot — Metrics Collector

import time
from collections import defaultdict

# memorie temporară pentru metrici runtime
_metrics = defaultdict(int)

_start_time = time.time()


def increment(metric_name: str, value: int = 1):
    """
    Increment a metric counter.
    """
    _metrics[metric_name] += value


def set_metric(metric_name: str, value):
    """
    Set metric value directly.
    """
    _metrics[metric_name] = value


def get_metric(metric_name: str):
    """
    Return metric value.
    """
    return _metrics.get(metric_name, 0)


def snapshot():
    """
    Returns current metrics snapshot.
    """
    return dict(_metrics)


def uptime_seconds():
    """
    Returns bot uptime.
    """
    return int(time.time() - _start_time)


def reset():
    """
    Reset all metrics.
    """
    _metrics.clear()
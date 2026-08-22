import threading
from typing import Dict

class ObservabilityService:
    """
    Observability Service tracking durations and total counts across pipeline operations.
    Exposes metrics in standard Prometheus-compatible exposition format.
    """
    _lock = threading.Lock()
    _metrics = {
        "jobs_discovered_total": 0,
        "jobs_matched_total": 0,
        "applications_prepared_total": 0,
        "applications_submitted_total": 0,
        "applications_failed_total": 0,
        "human_interventions_total": 0,
        "source_errors_total": 0,
        "browser_failures_total": 0,
        "ai_failures_total": 0,
    }

    @classmethod
    def increment(cls, metric_name: str, amount: int = 1):
        with cls._lock:
            if metric_name in cls._metrics:
                cls._metrics[metric_name] += amount

    @classmethod
    def get_metrics_prometheus(cls) -> str:
        with cls._lock:
            lines = []
            for k, v in cls._metrics.items():
                lines.append(f"# HELP jobpilot_{k} Help string for {k}")
                lines.append(f"# TYPE jobpilot_{k} counter")
                lines.append(f"jobpilot_{k} {v}")
            return "\n".join(lines) + "\n"

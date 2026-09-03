"""Validation on 2 usable positives only. Never train on them."""
from __future__ import annotations

def lead_time_minutes(first_alarm, failure_time) -> float | None:
    if first_alarm is None or failure_time is None:
        return None
    return (failure_time - first_alarm).total_seconds() / 60.0

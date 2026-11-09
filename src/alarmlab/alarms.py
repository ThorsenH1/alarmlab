"""A resettable, causal alarm state machine with persistence and hysteresis."""

import numpy as np


def alarm_states(
    scores, threshold, eligible, warmup, on_steps=3, off_steps=5, release_ratio=0.8
):
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("Threshold must be finite and positive.")
    if on_steps < 1 or off_steps < 1 or not 0 < release_ratio < 1:
        raise ValueError("Invalid alarm configuration.")
    states, starts = [], []
    active = False
    on_count = off_count = 0
    for value, ok, initial in zip(scores, eligible, warmup, strict=True):
        started = False
        if initial or not ok or not np.isfinite(value):
            active = False
            on_count = off_count = 0
            state = "WARMUP" if initial else "REVIEW"
        else:
            on_count = on_count + 1 if value > threshold else 0
            off_count = off_count + 1 if value < threshold * release_ratio else 0
            if not active and on_count >= on_steps:
                active = started = True
            if active and off_count >= off_steps:
                active = False
                on_count = 0
            state = "ALARM" if active else ("WATCH" if value > threshold else "NORMAL")
        states.append(state)
        starts.append(started)
    return np.asarray(states), np.asarray(starts, dtype=bool)

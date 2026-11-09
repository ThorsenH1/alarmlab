"""Event-level evaluation without point adjustment or random row splitting."""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from .config import Config
from .models import METHODS


def event_table(predictions: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows = []
    for run_id, g in predictions.groupby("run_id", sort=False):
        normal = ~(g.fault_active | g.quality_fault_active)
        monitored = g.eligible & ~g.warmup
        onset = int(g.event_onset_s.iloc[0])
        has_event = bool(g.fault_active.any())
        has_quality = bool(g.quality_fault_active.any())
        for method in METHODS:
            starts = g[f"{method}_alarm_start"].astype(bool)
            hits = g.loc[starts & g.fault_active, "time_s"]
            delay = float(hits.iloc[0] - onset) if has_event and len(hits) else np.nan
            quality_hits = g.loc[
                g.quality_fault_active & g.quality_reason.isin(
                    ["missing_or_nonfinite", "stuck_sensor", "outside_physical_range"]
                ), "time_s"
            ]
            rows.append({
                "run_id": run_id, "domain": g.domain.iloc[0],
                "scenario": g.scenario.iloc[0], "method": method,
                "process_event": int(has_event),
                "detected_event": int(has_event and len(hits) > 0),
                "detected_within_120s": int(has_event and np.isfinite(delay) and delay <= 120),
                "delay_s": delay,
                "quality_event": int(has_quality),
                "quality_detected": int(has_quality and len(quality_hits) > 0),
                "quality_delay_s": float(quality_hits.iloc[0] - onset) if len(quality_hits) else np.nan,
                "false_starts": int((starts & normal & monitored).sum()),
                "normal_exposure_h": float((normal & monitored).sum() * cfg.dt_seconds / 3600),
                "alarm_time_normal_s": int(((g[f"{method}_status"] == "ALARM") & normal & monitored).sum() * cfg.dt_seconds),
                "coverage": float(monitored.sum() / max(1, (~g.warmup).sum())),
                "review_fraction": float(((~g.eligible) & ~g.warmup).sum() / max(1, (~g.warmup).sum())),
            })
    return pd.DataFrame(rows)


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def wilson_interval(successes: int, total: int):
    if total == 0:
        return [None, None]
    z = 1.959963984540054
    p = successes / total
    center = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [float(max(0, center - half)), float(min(1, center + half))]


def aggregate_events(events: pd.DataFrame, cfg: Config) -> list[dict]:
    results = []
    for (domain, method), g in events.groupby(["domain", "method"], sort=False):
        total = int(g.process_event.sum())
        detected = int(g.detected_event.sum())
        false_starts = int(g.false_starts.sum())
        exposure = float(g.normal_exposure_h.sum())
        delays = g.delay_s.dropna()
        # Episodes are the resampling unit, preserving within-run dependence.
        rng = np.random.default_rng(cfg.seed + 77)
        rates = []
        for _ in range(cfg.bootstrap_repetitions):
            b = g.iloc[rng.integers(0, len(g), len(g))]
            if b.normal_exposure_h.sum() > 0:
                rates.append(b.false_starts.sum() / b.normal_exposure_h.sum())
        results.append({
            "domain": domain, "method": method, "runs": len(g),
            "process_events": total, "detected_events": detected,
            "event_recall": _ratio(detected, total),
            "event_recall_wilson95": wilson_interval(detected, total),
            "recall_within_120s": _ratio(g.detected_within_120s.sum(), total),
            "median_delay_s_detected_only": float(delays.median()) if len(delays) else None,
            "false_alarm_starts": false_starts, "normal_monitored_hours": exposure,
            "false_alarms_per_hour": _ratio(false_starts, exposure),
            "normal_alarm_occupancy": _ratio(g.alarm_time_normal_s.sum() / 3600, exposure),
            "false_alarms_per_hour_cluster_bootstrap95": (
                np.quantile(rates, [.025, .975]).tolist() if rates else [None, None]
            ),
            "zero_count_poisson_upper95_per_hour": (
                float(-np.log(0.05) / exposure) if false_starts == 0 and exposure > 0 else None
            ),
            "coverage": float(g.coverage.mean()),
            "quality_event_recall": _ratio(g.quality_detected.sum(), g.quality_event.sum()),
        })
    return results


def add_point_metrics(summary: list[dict], predictions: pd.DataFrame):
    for entry in summary:
        sub = predictions[
            (predictions.domain == entry["domain"]) & predictions.eligible
            & ~predictions.warmup & ~predictions.quality_fault_active
        ]
        y = sub.fault_active.to_numpy()
        entry["scored_samples"] = len(sub)
        entry["point_average_precision"] = (
            float(average_precision_score(y, sub[f"{entry['method']}_score"]))
            if len(np.unique(y)) == 2 else None
        )
    return summary

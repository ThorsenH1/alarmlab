"""Run, evaluate and record the full synthetic experiment."""

import importlib.metadata
import platform
from pathlib import Path

import pandas as pd

from .config import Config
from .evaluation import add_point_metrics, aggregate_events, event_table
from .io import sha256, write_csv_gz, write_json
from .models import DetectorSuite, METHODS
from .simulator import make_dataset


def run_experiment(cfg: Config, output_dir: Path):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = make_dataset(cfg)
    train = data[data.split == "train"]
    calibration = data[data.split == "calibration"]
    test = data[data.split == "test"]
    sets = [set(part.run_id) for part in [train, calibration, test]]
    if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
        raise AssertionError("Episode leakage.")
    print(f"Generated {len(data):,} samples / {data.run_id.nunique()} episodes.", flush=True)
    suite = DetectorSuite(cfg).fit(train, calibration)
    predictions = suite.predict(test)
    events = event_table(predictions, cfg)
    summary = add_point_metrics(aggregate_events(events, cfg), predictions)
    # Ablation changes persistence only; never retunes thresholds on test data.
    ablations = []
    for domain, group in predictions.groupby("domain", sort=False):
        normal = ~(group.fault_active | group.quality_fault_active)
        observed = group.eligible & ~group.warmup
        exposure = float((normal & observed).sum() * cfg.dt_seconds / 3600)
        for method in METHODS:
            hit = group[f"{method}_score"] > suite.thresholds[method]
            previous = hit.groupby(group.run_id).shift(fill_value=False)
            raw_starts = hit & ~previous
            raw_false = int((raw_starts & normal & observed).sum())
            ablations.append({
                "domain": domain, "method": method,
                "without_persistence_false_starts": raw_false,
                "without_persistence_false_starts_per_hour": raw_false / exposure if exposure > 0 else None,
                "with_persistence_false_starts": int((group[f"{method}_alarm_start"] & normal & observed).sum()),
            })
    by_scenario = events.groupby(["domain", "method", "scenario"], sort=False).agg(
        events=("process_event", "sum"), detected=("detected_event", "sum"),
        detected_120s=("detected_within_120s", "sum"),
        median_delay_s=("delay_s", "median"), coverage=("coverage", "mean"),
        quality_events=("quality_event", "sum"), quality_detected=("quality_detected", "sum"),
        median_quality_delay_s=("quality_delay_s", "median"),
    ).reset_index()
    write_csv_gz(data, output_dir / "synthetic_observations.csv.gz")
    write_csv_gz(predictions, output_dir / "predictions.csv.gz")
    events.to_csv(output_dir / "event_metrics.csv", index=False)
    by_scenario.to_csv(output_dir / "scenario_metrics.csv", index=False)
    write_json(output_dir / "synthetic_summary.json", {
        "config": cfg.to_dict(), "summary": summary, "persistence_ablation": ablations,
        "model": suite.model_card_values(),
        "interpretation": {
            "event_detection": "A new alarm start at or after fault onset; pre-existing alarms do not count.",
            "false_alarm_exposure": "Monitored normal time only; abstention and warmup excluded.",
            "delay": "Conditional on detected events. Always read alongside missed events.",
            "coverage": "Fraction of post-warmup time eligible for model decisions, including fault periods.",
            "uncertainty": "Wilson intervals for episode recall; episode bootstrap for false alarm rates.",
            "zero_count": "A zero-event bootstrap [0,0] is not proof of zero risk; a Poisson reference upper bound is also provided.",
            "synthetic_only": True,
        },
    })
    manifest = {
        "config": cfg.to_dict(), "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in [
            "numpy", "pandas", "scipy", "scikit-learn", "matplotlib"
        ]},
        "rows": len(data), "episodes": int(data.run_id.nunique()),
        "split_runs": {name: sorted(part.run_id.unique()) for name, part in data.groupby("split")},
        "input_sha256": sha256(output_dir / "synthetic_observations.csv.gz"),
        "predictions_sha256": sha256(output_dir / "predictions.csv.gz"),
        "source_sha256": {f.name: sha256(f) for f in sorted(Path(__file__).parent.glob("*.py"))},
    }
    write_json(output_dir / "manifest.json", manifest)
    print("Training, calibration and held-out evaluation complete.", flush=True)
    return predictions

"""Build and execute a compact review notebook using the saved numerical data.

No Jupyter runtime is needed to create it. The emitted notebook uses ordinary
Python/pandas cells and can subsequently be rerun in Jupyter or VS Code.
"""

import contextlib
import io
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {
        "cell_type": "code", "metadata": {}, "execution_count": None,
        "source": text.splitlines(keepends=True), "outputs": [],
    }


cells = [
    markdown("# AlarmLab — research walkthrough\n\nThis executed notebook checks the supplied data and explains the event-level evaluation. See the methods document for the exact model definitions. It does not claim clinical or plant validation."),
    code('''from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

root = Path.cwd()
if not (root / "configs").exists():
    root = root.parent
assert (root / "configs/default.json").exists(), "Open from the repo or notebooks folder."
sys.path.insert(0, str(root / "src"))
from alarmlab.io import sha256
manifest = json.loads((root / "artifacts/manifest.json").read_text())
assert sha256(root / "artifacts/synthetic_observations.csv.gz") == manifest["input_sha256"]
print("Input checksum verified.")
print("Episodes:", manifest["episodes"], "| Samples:", manifest["rows"])
'''),
    markdown("## 1. Verify the independent units\n\nA run is the unit of the synthetic split. The observation count is much larger than the number of independent runs."),
    code('''data = pd.read_csv(root / "artifacts/synthetic_observations.csv.gz")
assert data.groupby("run_id").split.nunique().eq(1).all()
print(data.groupby(["split", "domain"]).agg(
    episodes=("run_id", "nunique"), samples=("time_s", "size")
).to_string())
'''),
    markdown("## 2. Reconstruct a displayed residual score\n\nThe anomaly score is the maximum absolute standardized sensor residual. The stored file contains these components, so one displayed score can be checked without trusting the chart."),
    code('''predictions = pd.read_csv(root / "artifacts/predictions.csv.gz")
summary = json.loads((root / "artifacts/synthetic_summary.json").read_text())
case = predictions[(predictions.scenario == "pump_wear") &
                   (predictions.domain == "in_domain") &
                   (predictions.time_s == 700)].iloc[0]
columns = [c for c in predictions if c.startswith("residual_z_")]
reconstructed = float(case[columns].max())
assert np.isclose(reconstructed, case.contextual_residual_score, rtol=1e-8)
threshold = summary["model"]["thresholds"]["contextual_residual"]
print(case[["run_id", "time_s", "contextual_residual_status"]].to_string())
print("Residual score:", round(reconstructed, 3))
print("Calibration threshold:", round(threshold, 3))
print("Score / threshold:", round(reconstructed / threshold, 3))
'''),
    markdown("## 3. Count events rather than adjusted points\n\nAn alarm must start after the annotated onset. A detector already in alarm before a fault is not counted as signalling that new fault."),
    code('''events = pd.read_csv(root / "artifacts/event_metrics.csv")
grouped = events.groupby(["domain", "method"]).agg(
    events=("process_event", "sum"),
    detected=("detected_event", "sum"),
    false_starts=("false_starts", "sum"),
    normal_hours=("normal_exposure_h", "sum"),
)
grouped["recall"] = grouped.detected / grouped.events
grouped["false_starts_per_hour"] = grouped.false_starts / grouped.normal_hours.replace(0, np.nan)
print(grouped.round(3).to_string())
'''),
    markdown("## 4. Inspect the stress failure\n\nCompare event recall with average precision and normal-time alarm occupancy. Good ranking of fault points cannot recover an alarm that started too early and stayed active."),
    code('''metrics = pd.DataFrame(summary["summary"])
focus = metrics[metrics.method == "contextual_residual"]
print(focus[["domain", "event_recall", "point_average_precision",
             "normal_alarm_occupancy", "coverage"]].round(3).to_string(index=False))
'''),
    markdown("## 5. Inspect the measured-data split\n\nThe UCI task uses completed cycles. Groups are full condition recipes, not patients or independent physical rigs. This distinction limits the conclusion."),
    code('''real = json.loads((root / "artifacts/real_benchmark.json").read_text())
rp = pd.read_csv(root / "artifacts/real_benchmark_predictions.csv.gz")
groups = {s: set(g.condition_group) for s, g in rp.groupby("split")}
assert not groups["train"] & groups["test"]
assert not groups["train"] & groups["calibration"]
assert not groups["calibration"] & groups["test"]
assert not set(real["features"]) & {"cooler", "valve", "pump_leakage", "accumulator", "unstable", "cycle_id"}
print("Disjoint recipe groups:", {k: len(v) for k, v in groups.items()})
table = pd.DataFrame(real["metrics"])
print(table[table.split == "test"][["task", "model", "balanced_accuracy", "macro_f1"]].round(3).to_string(index=False))
'''),
    markdown("## 6. Interpretation to write yourself\n\nExplain why the residual model's synthetic performance is favoured by its feature design. Explain why a one-rig perfect classification result is insufficient for a deployment claim. Specify a new development/test protocol before changing the alarm logic.\n\nThe first implementation was AI-assisted. Record your own experiment, configuration and interpretation in a separate commit."),
]


def main():
    previous = Path.cwd()
    os.chdir(ROOT)
    namespace = {"__name__": "__notebook__"}
    count = 0
    try:
        for cell in cells:
            if cell["cell_type"] != "code":
                continue
            count += 1
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                exec("".join(cell["source"]), namespace)
            cell["execution_count"] = count
            cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": capture.getvalue().splitlines(keepends=True)}]
    finally:
        os.chdir(previous)
    notebook = {
        "cells": cells, "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.13.0"},
        },
        "nbformat": 4, "nbformat_minor": 5,
    }
    for index, cell in enumerate(cells):
        cell["id"] = f"alarmlab-{index:03d}"
    target = ROOT / "notebooks/01_research_walkthrough.ipynb"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(notebook, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Executed {count} notebook cells.")


if __name__ == "__main__":
    main()

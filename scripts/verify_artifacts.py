"""Verify provenance, split integrity, metric bookkeeping and local doc links."""

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from alarmlab.io import sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    directory = args.output.resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        assert sha256(ROOT / "src/alarmlab" / name) == expected, f"Stale source fingerprint: {name}"
    assert sha256(directory / "synthetic_observations.csv.gz") == manifest["input_sha256"]
    assert sha256(directory / "predictions.csv.gz") == manifest["predictions_sha256"]
    sets = [set(ids) for ids in manifest["split_runs"].values()]
    for i, first in enumerate(sets):
        for second in sets[i + 1:]:
            assert not first & second, "Episode leakage in manifest"
    predictions = pd.read_csv(directory / "predictions.csv.gz")
    assert predictions.groupby("run_id").size().eq(manifest["config"]["steps"]).all()
    assert predictions.run_id.nunique() == len(manifest["split_runs"]["test"])
    events = pd.read_csv(directory / "event_metrics.csv")
    summary = json.loads((directory / "synthetic_summary.json").read_text(encoding="utf-8"))
    for row in summary["summary"]:
        group = events[(events.domain == row["domain"]) & (events.method == row["method"])]
        assert int(group.detected_event.sum()) == row["detected_events"]
        assert int(group.false_starts.sum()) == row["false_alarm_starts"]
        assert np.isclose(group.normal_exposure_h.sum(), row["normal_monitored_hours"])
        if row["normal_monitored_hours"] == 0:
            assert row["false_alarms_per_hour"] is None
        else:
            assert np.isclose(row["false_alarms_per_hour"], group.false_starts.sum() / group.normal_exposure_h.sum())
    real = json.loads((directory / "real_benchmark.json").read_text(encoding="utf-8"))
    assert len(real["features"]) == 36
    assert sha256(ROOT / "data/external/uci447_features.csv.gz") == real["source_sha256"]
    checked_links = 0
    broken = []
    for path in ROOT.rglob("*.md"):
        if any(part in {"node_modules", ".venv", ".git", "work"} for part in path.parts):
            continue
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if link.startswith(("https:", "http:", "#", "mailto:")):
                continue
            target = unquote(link.split("#", 1)[0]).strip("<>")
            if not target:
                continue
            checked_links += 1
            if not (path.parent / target).exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not broken, "Broken local links: " + "; ".join(broken)
    print(f"Verified source/data fingerprints, episode separation, event accounting and {checked_links} local document links.")


if __name__ == "__main__":
    main()

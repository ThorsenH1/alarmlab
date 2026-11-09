"""Separate real-data benchmark on UCI 447. No claims of nuclear validation.

The supervised target is cooler condition <100. Features are summaries of
physical sensors. Virtual efficiency channels and all condition labels are
excluded from predictors. Grouped holdout separates full condition recipes.
"""

import io
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, confusion_matrix,
    f1_score, roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .io import sha256, write_csv_gz, write_json

UCI_URL = "https://archive.ics.uci.edu/static/public/447/condition%2Bmonitoring%2Bof%2Bhydraulic%2Bsystems.zip"
UCI_SHA256 = "24128aad2ee45eea7e6b63ebbd9992cdf25d0483a2cebefbfc13bc69079af1f2"
REAL_SENSORS = ["TS1", "TS2", "TS3", "TS4", "FS1", "FS2", "VS1", "PS1", "PS2"]
TARGETS = ["cooler", "valve", "pump_leakage", "accumulator", "unstable"]


def download_archive(destination: Path):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Download is an explicit CLI action, never part of inference or the demo.
    with urllib.request.urlopen(UCI_URL, timeout=90) as response, destination.open("wb") as target:
        while block := response.read(1 << 20):
            target.write(block)
    if sha256(destination) != UCI_SHA256:
        raise ValueError("UCI archive checksum changed. Review source before use.")
    return destination


def extract_features(archive_path: Path, output_dir: Path):
    archive_path, output_dir = Path(archive_path), Path(output_dir)
    if sha256(archive_path) != UCI_SHA256:
        raise ValueError("Archive does not match the documented UCI 447 version.")
    extracted = {}
    with zipfile.ZipFile(archive_path) as archive:
        targets = np.loadtxt(io.BytesIO(archive.read("profile.txt")))
        for sensor in REAL_SENSORS:
            # Read one matrix at a time; never extract untrusted ZIP paths to disk.
            values = np.loadtxt(io.BytesIO(archive.read(f"{sensor}.txt")))
            if values.shape[0] != len(targets) or not np.isfinite(values).all():
                raise ValueError(f"Invalid sensor matrix: {sensor}")
            extracted[f"{sensor}_mean"] = values.mean(axis=1)
            extracted[f"{sensor}_std"] = values.std(axis=1)
            extracted[f"{sensor}_range"] = np.ptp(values, axis=1)
            x = np.linspace(-0.5, 0.5, values.shape[1])
            extracted[f"{sensor}_slope_per_cycle"] = values @ x / (x @ x)
    data = pd.DataFrame(extracted)
    data.insert(0, "cycle_id", np.arange(1, len(data) + 1))
    for j, name in enumerate(TARGETS):
        data[name] = targets[:, j].astype(int)
    path = output_dir / "uci447_features.csv.gz"
    write_csv_gz(data, path)
    manifest = {
        "dataset": "Condition monitoring of hydraulic systems",
        "creators": "Nikolai Helwig, Eliseo Pignanelli, Andreas Schuetze",
        "doi": "https://doi.org/10.24432/C5CW21",
        "source_url": UCI_URL,
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "archive_sha256": UCI_SHA256,
        "derived_sha256": sha256(path),
        "rows": len(data),
        "physical_sensors": REAL_SENSORS,
        "transformation": "Per 60-second cycle: mean, population std, range, linear slope per cycle.",
        "excluded_from_predictors": TARGETS + ["cycle_id", "CE", "CP", "SE"],
        "data_origin": "Measured hydraulic test-rig data, not nuclear or patient data.",
    }
    write_json(output_dir / "uci447_provenance.json", manifest)
    return path


def split_cycles(data: pd.DataFrame, seed: int):
    # Group labels are used ONLY to partition/evaluate, never as model features.
    groups = data[["cooler", "valve", "pump_leakage", "accumulator"]].astype(str).agg("|".join, axis=1)
    outer = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed)
    traincal, test = next(outer.split(data, groups=groups))
    inner = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=seed + 1)
    train_rel, cal_rel = next(inner.split(data.iloc[traincal], groups=groups.iloc[traincal]))
    splits = {"train": traincal[train_rel], "calibration": traincal[cal_rel], "test": test}
    assigned = {name: set(groups.iloc[idx]) for name, idx in splits.items()}
    if any(assigned[a] & assigned[b] for a, b in [("train", "calibration"), ("train", "test"), ("calibration", "test")]):
        raise AssertionError("Condition group leakage.")
    for name, indices in splits.items():
        if data.iloc[indices].cooler.lt(100).nunique() != 2:
            raise ValueError(f"{name} lacks one class; predefine a different grouped split.")
    return splits, groups


def probability_metrics(y, p):
    predicted = np.asarray(p) >= 0.5  # Fixed a priori for every model.
    return {
        "n": len(y), "positive_count": int(np.sum(y)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "macro_f1": float(f1_score(y, predicted, average="macro")),
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "average_precision": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else None,
        "confusion_matrix_tn_fp_fn_tp": confusion_matrix(y, predicted, labels=[0, 1]).ravel().tolist(),
    }


def run_benchmark(features_path: Path, output_dir: Path, seed: int = 20261109):
    features_path, output_dir = Path(features_path), Path(output_dir)
    data = pd.read_csv(features_path)
    provenance_path = features_path.with_name("uci447_provenance.json")
    if not provenance_path.exists():
        raise ValueError("Missing UCI provenance sidecar.")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if sha256(features_path) != provenance["derived_sha256"]:
        raise ValueError("Derived feature checksum differs from provenance.")
    columns = [f"{s}_{stat}" for s in REAL_SENSORS for stat in ["mean", "std", "range", "slope_per_cycle"]]
    x = data[columns].to_numpy(dtype=float)
    y = data.cooler.lt(100).astype(int).to_numpy()
    splits, groups = split_cycles(data, seed)
    estimators = {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000, class_weight="balanced")),
        "random_forest": RandomForestClassifier(
            n_estimators=240, max_depth=8, min_samples_leaf=5,
            class_weight="balanced", n_jobs=1, random_state=seed,
        ),
    }
    metrics = []
    predictions = data[["cycle_id", *TARGETS]].copy()
    predictions["condition_group"] = groups
    predictions["split"] = ""
    for split, indices in splits.items():
        predictions.loc[indices, "split"] = split
    targets = {
        "cooler_degradation": y,
        "pump_leakage": data.pump_leakage.gt(0).astype(int).to_numpy(),
    }
    for task, labels in targets.items():
        for name, estimator in estimators.items():
            estimator.fit(x[splits["train"]], labels[splits["train"]])
            for split in ["calibration", "test"]:
                indices = splits[split]
                probabilities = estimator.predict_proba(x[indices])[:, 1]
                predictions.loc[indices, f"{task}_{name}_probability"] = probabilities
                entry = {
                    "task": task, "model": name, "split": split,
                    **probability_metrics(labels[indices], probabilities),
                }
                # Group bootstrap respects repeated cycles sharing a condition recipe.
                rng = np.random.default_rng(seed + 3)
                test_groups = groups.iloc[indices].to_numpy()
                unique = np.unique(test_groups)
                draws = []
                for _ in range(300):
                    sampled = rng.choice(unique, len(unique), replace=True)
                    selected = np.concatenate([np.flatnonzero(test_groups == g) for g in sampled])
                    if len(np.unique(labels[indices][selected])) == 2:
                        draws.append(balanced_accuracy_score(labels[indices][selected], probabilities[selected] >= 0.5))
                entry["balanced_accuracy_group_bootstrap95"] = np.quantile(draws, [.025, .975]).tolist() if draws else [None, None]
                metrics.append(entry)
    # An explicitly labelled diagnostic, never the headline result.
    tr, te = train_test_split(np.arange(len(data)), test_size=0.25, random_state=seed, stratify=y)
    random_estimator = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000, class_weight="balanced"))
    random_estimator.fit(x[tr], y[tr])
    random_row_diagnostic = {
        "purpose": "Illustrate why random cycle splitting is a weaker validation design.",
        "model": "logistic_regression",
        "shared_condition_groups": len(set(groups.iloc[tr]) & set(groups.iloc[te])),
        **probability_metrics(y[te], random_estimator.predict_proba(x[te])[:, 1]),
    }
    result = {
        "task": "Supervised cooler degradation (<100) and exploratory pump leakage (>0) classification",
        "tasks": ["cooler_degradation", "pump_leakage"],
        "exploratory_note": "Pump leakage was added after inspecting the easy cooler task; it is not confirmatory validation.",
        "validation_note": "The split named calibration is a validation set here. Models and threshold 0.5 are fixed; probability calibration is not performed.",
        "data_origin": "Measured UCI 447 hydraulic test-rig data",
        "rows": len(data), "features": columns,
        "source_sha256": sha256(features_path),
        "split_design": "Disjoint full condition tuples; no identical recipe crosses splits.",
        "split_sizes": {k: len(v) for k, v in splits.items()},
        "split_groups": {k: len(set(groups.iloc[v])) for k, v in splits.items()},
        "metrics": metrics,
        "random_row_diagnostic": random_row_diagnostic,
        "limitations": [
            "All cycles come from one test rig; this is not external device validation.",
            "Condition groups do not guarantee independent acquisition sessions or remove all temporal dependence.",
            "Labels and unstable flag are excluded from model inputs.",
            "The cycle ends before inference: this is not an early-warning benchmark.",
            "Probabilities are uncalibrated model outputs, not physical failure probabilities.",
            "This supervised task does not validate the synthetic anomaly detector.",
        ],
    }
    write_json(output_dir / "real_benchmark.json", result)
    write_csv_gz(predictions, output_dir / "real_benchmark_predictions.csv.gz")
    return result

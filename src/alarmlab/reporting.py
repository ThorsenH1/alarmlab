"""Reports and a self-contained HTML replay built from actual experiment files."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .io import sha256
from .models import METHOD_LABELS, METHODS
from .simulator import SENSORS


def fmt(value, digits=3):
    return "not available" if value is None or pd.isna(value) else f"{value:.{digits}f}"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_reports(output_dir: Path):
    output_dir = Path(output_dir)
    synthetic = read_json(output_dir / "synthetic_summary.json")
    real = read_json(output_dir / "real_benchmark.json")
    manifest = read_json(output_dir / "manifest.json")
    summary = synthetic["summary"]
    figures = output_dir / "figures"
    figures.mkdir(exist_ok=True)
    colors = ["#a5a79b", "#78878b", "#446657"]
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "figure.facecolor": "#faf8f0", "axes.facecolor": "#faf8f0",
    })
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), layout="constrained")
    rows = [next(x for x in summary if x["domain"] == "in_domain" and x["method"] == m) for m in METHODS]
    labels = ["Sensor\nlimits", "Isolation\nForest", "Contextual\nresidual"]
    for ax, key, title in zip(axes, [
        "event_recall", "false_alarms_per_hour", "median_delay_s_detected_only"
    ], ["Event recall (24 simulated faults)", "False alarm starts / monitored hour", "Median delay / seconds (detected only)"]):
        values = [row[key] for row in rows]
        bars = ax.bar(labels, values, color=colors, width=.55)
        ax.set_title(title, fontsize=10, pad=15)
        ax.bar_label(bars, labels=[fmt(v, 2 if key != "median_delay_s_detected_only" else 0) for v in values], padding=5)
        ax.set_ylim(0, max(values) * 1.25)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    low = np.array([r["event_recall"] - r["event_recall_wilson95"][0] for r in rows])
    high = np.array([r["event_recall_wilson95"][1] - r["event_recall"] for r in rows])
    axes[0].errorbar(np.arange(3), [r["event_recall"] for r in rows], yerr=[low, high], fmt="none", color="#27374a", capsize=4)
    fig.suptitle("AlarmLab / synthetic held-out episodes", fontsize=16, fontweight="bold")
    fig.savefig(figures / "synthetic_results.svg")
    fig.savefig(figures / "synthetic_results.png", dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout="constrained")
    domains = ["in_domain", "noise_shift", "context_shift"]
    x = np.arange(3)
    for j, method in enumerate(METHODS):
        rows = [next(r for r in summary if r["domain"] == d and r["method"] == method) for d in domains]
        axes[0].bar(x + (j - 1) * .23, [r["event_recall"] for r in rows], .23, label=METHOD_LABELS[method], color=colors[j])
        occupancy = [r.get("normal_alarm_occupancy") for r in rows]
        axes[1].bar(x + (j - 1) * .23, [v if v is not None else 0 for v in occupancy], .23, color=colors[j])
    for ax in axes:
        ax.set_xticks(x, ["In domain", "3x sensor noise", "Ambient +12 C"])
        ax.set_ylim(0, 1.15)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
    axes[0].set_title("New-alarm event recall (abstentions count as misses)")
    axes[1].set_title("Normal-time alarm occupancy (monitored time)")
    axes[1].text(2, .06, "No monitored exposure\nin context shift", ha="center", fontsize=8)
    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle("Distribution shift exposes a failure mode", fontsize=15, fontweight="bold")
    fig.savefig(figures / "shift_stress_test.svg")
    fig.savefig(figures / "shift_stress_test.png", dpi=170)
    plt.close(fig)
    lines = [
        "# Experimental results", "",
        "Generated from saved predictions. All synthetic and real-data results below are separate experiments.",
        "", "## Synthetic monitoring experiment", "",
        f"Seed: {synthetic['config']['seed']}. {manifest['episodes']} independent episodes; {manifest['rows']:,} samples; 2-second sampling.",
        "Training and threshold calibration use separate normal episodes. Each held-out fault episode counts once.",
        "", "| Domain | Method | Detected / events | Recall 95% Wilson CI | False starts / h | Delay s* | Coverage |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for r in summary:
        ci = r["event_recall_wilson95"]
        lines.append(
            f"| {r['domain']} | {METHOD_LABELS[r['method']]} | {r['detected_events']} / {r['process_events']} "
            f"| [{fmt(ci[0])}, {fmt(ci[1])}] | {fmt(r['false_alarms_per_hour'])} "
            f"| {fmt(r['median_delay_s_detected_only'], 0)} | {r['coverage']:.1%} |"
        )
    lines += [
        "", "*Median delay is conditional on detection. Missed events remain in the recall denominator.",
        "False alarm exposure excludes warmup and abstentions. An unavailable rate means no monitored exposure, not zero false alarms.",
        "", "![Synthetic results](figures/synthetic_results.png)",
        "", "## The negative result matters", "",
        "The residual model is closely matched to the synthetic generator. Its strong in-domain performance is not evidence of superiority on physical plants.",
        "Under 3x sensor noise, it can latch into an alarm before a fault starts. A pre-existing alarm does not count as detecting a new event. Read event recall together with normal alarm occupancy and the complete traces.",
        "The context gate abstains when ambient temperature is shifted outside training bounds. Abstained fault episodes count as missed in end-to-end recall. Abstention is not successful anomaly detection.",
        "Noise monitoring, revised alarm reset logic and adaptive calibration are future hypotheses; they have not been silently added to improve these held-out numbers.",
        "", "![Shift stress test](figures/shift_stress_test.png)",
        "", "## Real hydraulic sensor benchmark", "",
        f"{real['rows']} measured 60-second cycles and {len(real['features'])} derived features. Fixed threshold: 0.5.",
        f"Split sizes: {real['split_sizes']}. Condition-group counts: {real['split_groups']}.",
        "The 'calibration' split is a validation set in this supervised experiment; no probability calibration or model selection was performed.",
        "", "| Target | Model | Test balanced accuracy | Group-bootstrap 95% CI | Macro F1 | ROC AUC | TN / FP / FN / TP |",
        "|---|---|---:|---|---:|---:|---|",
    ]
    for r in real["metrics"]:
        if r["split"] != "test":
            continue
        ci = r["balanced_accuracy_group_bootstrap95"]
        lines.append(
            f"| {r['task']} | {r['model']} | {r['balanced_accuracy']:.3f} | [{fmt(ci[0])}, {fmt(ci[1])}] "
            f"| {r['macro_f1']:.3f} | {fmt(r['roc_auc'])} | {r['confusion_matrix_tn_fp_fn_tp']} |"
        )
    diag = real["random_row_diagnostic"]
    lines += [
        "", "The cooler task is easy on this rig. A perfect observed test score and a degenerate [1,1] bootstrap interval are not proof of perfect future performance.",
        "Pump leakage is an exploratory extension added after seeing the easy cooler result. It is reported as exploratory, not as confirmatory evidence.",
        f"The random-row diagnostic shares {diag['shared_condition_groups']} condition recipes across train/test and gives cooler balanced accuracy {diag['balanced_accuracy']:.3f}. It is a weaker split design even if its score matches the grouped result.",
        "", "Limitations: one rig, no independent deployment site, no guaranteed session independence, no early-warning labels. Raw virtual efficiency channels are excluded.",
        "", "## Reproduction and provenance", "",
        "Run python run.py all --output artifacts/rerun. Compare configuration, event counts and hashes in the manifests. Exact floats can vary across library/platform versions.",
        "The distributed environment versions are in manifest.json and requirements-tested.txt.",
        "Source and data fingerprints in the manifest identify the run; rerun after edits before describing results as current.",
        "", "Sources: [UCI 447](https://doi.org/10.24432/C5CW21), [scikit-learn data leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).",
        "",
    ]
    (output_dir / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def build_demo(output_dir: Path, demo_dir: Path):
    output_dir, demo_dir = Path(output_dir), Path(demo_dir)
    synthetic = read_json(output_dir / "synthetic_summary.json")
    predictions = pd.read_csv(output_dir / "predictions.csv.gz")
    traces = []
    for (domain, scenario), group in predictions.groupby(["domain", "scenario"], sort=False):
        run_id = group.run_id.iloc[0]
        g = group[group.run_id == run_id]
        traces.append({
            "id": run_id, "domain": domain, "scenario": scenario,
            "onset": int(g.event_onset_s.iloc[0]), "t": g.time_s.tolist(),
            "sensors": {s: g[s].round(5).tolist() for s in SENSORS},
            "expected": {s: g[f"expected_{s}"].round(5).tolist() for s in SENSORS},
            "residuals": {s: g[f"residual_z_{s}"].round(5).tolist() for s in SENSORS},
            "context": {c: g[c].round(5).tolist() for c in ["heat_kw", "pump_pct", "ambient_c"]},
            "quality": g.quality_reason.fillna("").tolist(),
            "methods": {
                m: {
                    "scores": g[f"{m}_score"].round(6).tolist(),
                    "tail": g[f"{m}_tail_rank"].round(6).tolist(),
                    "states": g[f"{m}_status"].tolist(),
                } for m in METHODS
            },
        })
    # Pandas serialisation maps missing numeric values to JSON null.
    traces = json.loads(pd.Series(traces).to_json(orient="values"))
    payload = {
        "synthetic": synthetic, "traces": traces,
        "real": read_json(output_dir / "real_benchmark.json"),
        "scenarios": json.loads(pd.read_csv(output_dir / "scenario_metrics.csv").to_json(orient="records")),
        "manifest": read_json(output_dir / "manifest.json"),
        "predictions_sha256": sha256(output_dir / "predictions.csv.gz"),
    }
    source = Path(__file__).resolve().parent / "web"
    template = (source / "index.html").read_text(encoding="utf-8")
    style = (source / "traditional.css").read_text(encoding="utf-8")
    app = (source / "app.js").read_text(encoding="utf-8")
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("<!--STYLE-->", f"<style>{style}</style>")
    html = html.replace("<!--DATA-->", f"<script>window.ALARMLAB_DATA={data};</script>")
    html = html.replace("<!--APP-->", f"<script>{app}</script>")
    demo_dir.mkdir(parents=True, exist_ok=True)
    (demo_dir / "index.html").write_text(html, encoding="utf-8")

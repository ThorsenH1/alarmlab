"""Causal features and label-independent data-quality gates."""

import numpy as np
import pandas as pd

from .simulator import CONTEXT, SENSORS

FEATURE_NAMES = [
    "filtered_pump", "filtered_pump_squared", "pump_squared",
    "heat_kw", "thermal_proxy", "filtered_ambient", "ambient_c",
]
BOUNDS = {
    "temperature_c": (-10, 120), "flow_lpm": (0, 180),
    "pressure_bar": (0, 30), "vibration_mm_s": (0, 15),
    "heat_kw": (0, 200), "pump_pct": (1, 100), "ambient_c": (-20, 60),
}


def validate_frame(frame: pd.DataFrame) -> None:
    required = ["run_id", "time_s", *SENSORS, *CONTEXT]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if frame.empty or frame["run_id"].isna().any():
        raise ValueError("Empty frame or missing run identifiers.")
    if not frame.index.is_unique:
        raise ValueError("The DataFrame index must be unique.")
    if frame.duplicated(["run_id", "time_s"]).any():
        raise ValueError("Duplicate run/timestamp pair.")
    if not np.isfinite(frame["time_s"].to_numpy(dtype=float)).all():
        raise ValueError("Timestamps must be finite.")
    for _, group in frame.groupby("run_id", sort=False):
        if not (group["time_s"].diff().dropna() == 2).all():
            raise ValueError("Each run must be ordered and sampled every two seconds.")
    for column in SENSORS + CONTEXT:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f"Sensor/context column must be numeric: {column}")


def causal_features(frame: pd.DataFrame) -> np.ndarray:
    """Uses only known controls up to the current timestamp; never fault labels."""
    validate_frame(frame)
    chunks = pd.DataFrame(index=frame.index, columns=FEATURE_NAMES, dtype=float)
    for _, g in frame.groupby("run_id", sort=False):
        # No interpolation or backward filling across missing/future samples.
        pump = g["pump_pct"].ewm(alpha=0.25, adjust=False).mean()
        thermal = (g["heat_kw"] / (0.08 * 1.18 * pump)).ewm(alpha=0.06, adjust=False).mean()
        chunks.loc[g.index] = np.column_stack([
            pump, pump**2, g["pump_pct"]**2, g["heat_kw"], thermal,
            g["ambient_c"].ewm(alpha=0.06, adjust=False).mean(), g["ambient_c"],
        ])
    return chunks.to_numpy(dtype=float)


def quality_reasons(frame: pd.DataFrame) -> np.ndarray:
    """Missing/range/stuck checks, with no dependency on scenario annotations."""
    reasons = np.full(len(frame), "", dtype=object)
    values = frame[SENSORS + CONTEXT].to_numpy(dtype=float)
    reasons[~np.isfinite(values).all(axis=1)] = "missing_or_nonfinite"
    for col, (low, high) in BOUNDS.items():
        out = ((frame[col] < low) | (frame[col] > high)).to_numpy()
        reasons[out] = "outside_physical_range"
    # Equality runs: six identical readings => five differences equal to zero.
    positions = pd.Series(np.arange(len(frame)), index=frame.index)
    for _, g in frame.groupby("run_id", sort=False):
        for col in SENSORS:
            equal = g[col].diff().eq(0)
            streak = equal.groupby((~equal).cumsum()).cumsum()
            stuck = streak.ge(5).to_numpy()
            idx = positions.loc[g.index].to_numpy()[stuck]
            reasons[idx] = np.where(reasons[idx] == "", "stuck_sensor", reasons[idx])
    return reasons


def warmup_mask(frame: pd.DataFrame, warmup_steps: int) -> np.ndarray:
    return frame.groupby("run_id", sort=False).cumcount().to_numpy() < warmup_steps

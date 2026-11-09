"""Three normal-only detectors with disjoint empirical threshold calibration."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .alarms import alarm_states
from .config import Config
from .features import causal_features, quality_reasons, validate_frame, warmup_mask
from .simulator import CONTEXT, SENSORS

METHODS = ["raw_limits", "isolation_forest", "contextual_residual"]
METHOD_LABELS = {
    "raw_limits": "Robust sensor limits",
    "isolation_forest": "Isolation Forest",
    "contextual_residual": "Contextual residual",
}


def robust_location_scale(x):
    center = np.median(x, axis=0)
    scale = np.maximum(1.4826 * np.median(np.abs(x - center), axis=0), 1e-6)
    return center, scale


def empirical_tail(reference, values):
    """Conservative tail rank. NOT a probability of failure."""
    reference = np.sort(np.asarray(reference, dtype=float))
    if not len(reference) or not np.isfinite(reference).all():
        raise ValueError("A finite, nonempty calibration reference is required.")
    values = np.asarray(values, dtype=float)
    result = (1 + len(reference) - np.searchsorted(reference, values, side="left")) / (len(reference) + 1)
    return np.where(np.isfinite(values), result, np.nan)


class DetectorSuite:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.fitted = False

    def fit(self, train: pd.DataFrame, calibration: pd.DataFrame):
        validate_frame(train)
        validate_frame(calibration)
        train_ids = set(train.run_id)
        if train_ids & set(calibration.run_id):
            raise ValueError("Training and calibration must have disjoint run IDs.")
        for part in [train, calibration]:
            if "fault_active" in part and part.fault_active.any():
                raise ValueError("Normal-only fitting cannot include process faults.")
            if "quality_fault_active" in part and part.quality_fault_active.any():
                raise ValueError("Normal-only fitting cannot include quality faults.")
        self.training_ids = sorted(train_ids)
        self.calibration_ids = sorted(set(calibration.run_id))
        tx = causal_features(train)
        clean = (quality_reasons(train) == "") & ~warmup_mask(train, self.cfg.warmup_steps)
        if clean.sum() < 100:
            raise ValueError("At least 100 clean post-warmup training samples required.")
        y = train[SENSORS].to_numpy(dtype=float)
        self.raw_center, self.raw_scale = robust_location_scale(y[clean])
        self.regressor = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        self.regressor.fit(tx[clean], y[clean])
        residual = y[clean] - self.regressor.predict(tx[clean])
        self.residual_center, self.residual_scale = robust_location_scale(residual)
        self.forest = IsolationForest(
            n_estimators=160, max_samples=256, random_state=self.cfg.seed, n_jobs=1
        )
        self.forest.fit(train.loc[clean, SENSORS + CONTEXT].to_numpy())
        context = train.loc[clean, CONTEXT].to_numpy(dtype=float)
        span = np.ptp(context, axis=0)
        self.context_low = context.min(axis=0) - 0.05 * span
        self.context_high = context.max(axis=0) + 0.05 * span
        self.fitted = True
        c = self.score(calibration)
        mask = c.eligible.to_numpy() & ~c.warmup.to_numpy()
        if mask.sum() < 100:
            raise ValueError("Too few in-scope calibration samples.")
        self.references = {m: np.sort(c.loc[mask, f"{m}_score"].to_numpy()) for m in METHODS}
        self.thresholds = {
            m: float(np.quantile(v, 1 - self.cfg.alpha, method="higher"))
            for m, v in self.references.items()
        }
        return self

    def score(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not self.fitted:
            raise RuntimeError("Fit on training and calibration episodes first.")
        validate_frame(frame)
        x = causal_features(frame)
        y = frame[SENSORS].to_numpy(dtype=float)
        q = quality_reasons(frame)
        context = frame[CONTEXT].to_numpy(dtype=float)
        inside = ((context >= self.context_low) & (context <= self.context_high)).all(axis=1)
        reasons = np.where(q != "", q, np.where(inside, "", "unsupported_context"))
        finite = np.isfinite(x).all(axis=1) & np.isfinite(y).all(axis=1) & np.isfinite(context).all(axis=1)
        expected = np.full(y.shape, np.nan)
        if finite.any():
            expected[finite] = self.regressor.predict(x[finite])
        residual_z = np.abs((y - expected - self.residual_center) / self.residual_scale)
        raw_z = np.abs((y - self.raw_center) / self.raw_scale)
        forest_score = np.full(len(frame), np.nan)
        if finite.any():
            forest_score[finite] = -self.forest.score_samples(
                frame.loc[finite, SENSORS + CONTEXT].to_numpy()
            )
        out = pd.DataFrame(index=frame.index)
        out["eligible"] = (reasons == "") & finite
        out["quality_reason"] = reasons
        out["warmup"] = warmup_mask(frame, self.cfg.warmup_steps)
        out["raw_limits_score"] = np.max(raw_z, axis=1)
        out["isolation_forest_score"] = forest_score
        out["contextual_residual_score"] = np.max(residual_z, axis=1)
        for j, sensor in enumerate(SENSORS):
            out[f"expected_{sensor}"] = expected[:, j] + self.residual_center[j]
            out[f"residual_z_{sensor}"] = residual_z[:, j]
        for method in METHODS:
            # Abstention has no displayed score, rather than a false reassurance.
            out.loc[~out.eligible, f"{method}_score"] = np.nan
        return out

    def predict(self, frame: pd.DataFrame, alpha: float | None = None) -> pd.DataFrame:
        if not hasattr(self, "thresholds"):
            raise RuntimeError("The model has not been calibrated.")
        out = self.score(frame)
        thresholds = self.thresholds if alpha is None else {
            m: float(np.quantile(v, 1 - alpha, method="higher"))
            for m, v in self.references.items()
        }
        for method in METHODS:
            out[f"{method}_tail_rank"] = empirical_tail(
                self.references[method], out[f"{method}_score"]
            )
            out[f"{method}_status"] = ""
            out[f"{method}_alarm_start"] = False
            for _, group in frame.groupby("run_id", sort=False):
                idx = group.index
                state, starts = alarm_states(
                    out.loc[idx, f"{method}_score"].to_numpy(), thresholds[method],
                    out.loc[idx, "eligible"].to_numpy(), out.loc[idx, "warmup"].to_numpy(),
                    self.cfg.alarm_on_steps, self.cfg.alarm_off_steps, self.cfg.release_ratio,
                )
                out.loc[idx, f"{method}_status"] = state
                out.loc[idx, f"{method}_alarm_start"] = starts
        return pd.concat([frame, out], axis=1)

    def model_card_values(self):
        return {
            "methods": METHODS,
            "training_runs": self.training_ids,
            "calibration_runs": self.calibration_ids,
            "thresholds": self.thresholds,
            "residual_scale": dict(zip(SENSORS, self.residual_scale.tolist())),
            "context_bounds": {
                c: [float(a), float(b)] for c, a, b in zip(CONTEXT, self.context_low, self.context_high)
            },
            "calibration_samples": {m: len(v) for m, v in self.references.items()},
            "tail_rank_is_failure_probability": False,
        }

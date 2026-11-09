"""Explicit experimental settings; no test-dependent hyperparameter selection."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Config:
    seed: int = 20261109
    steps: int = 600
    dt_seconds: int = 2
    warmup_steps: int = 30
    train_runs: int = 24
    calibration_runs: int = 12
    test_repetitions: int = 8
    shift_repetitions: int = 4
    alpha: float = 0.005
    alarm_on_steps: int = 3
    alarm_off_steps: int = 5
    release_ratio: float = 0.8
    bootstrap_repetitions: int = 400

    def __post_init__(self):
        if self.steps < 180 or not 1 <= self.warmup_steps < self.steps // 3:
            raise ValueError("Use >=180 steps and a warmup shorter than one third.")
        if self.dt_seconds != 2:
            raise ValueError("This simulator is discretised at 2 seconds.")
        if min(self.train_runs, self.calibration_runs, self.test_repetitions) < 2:
            raise ValueError("At least two independent runs are required per split.")
        if self.shift_repetitions < 1 or self.bootstrap_repetitions < 10:
            raise ValueError("At least one shift repetition and ten bootstraps required.")
        if not 0 < self.alpha < 0.5 or not 0 < self.release_ratio < 1:
            raise ValueError("Invalid threshold or hysteresis setting.")
        if min(self.alarm_on_steps, self.alarm_off_steps) < 1:
            raise ValueError("Alarm confirmation lengths must be positive.")

    @classmethod
    def read(cls, path: str | Path):
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))

    def to_dict(self):
        return asdict(self)

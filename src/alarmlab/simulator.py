"""A generic cooling-loop surrogate, NOT a nuclear plant or digital twin.

The simulator has no reactor parameters, controls or actuation interface.
Each episode owns its RNG stream and its entire train/calibration/test split.
"""

import numpy as np
import pandas as pd

from .config import Config

SENSORS = ["temperature_c", "flow_lpm", "pressure_bar", "vibration_mm_s"]
CONTEXT = ["heat_kw", "pump_pct", "ambient_c"]
SCENARIOS = [
    "normal", "load_step", "pump_wear", "cooling_loss",
    "sensor_bias", "dropout", "stuck_sensor",
]
PROCESS_FAULTS = {"pump_wear", "cooling_loss", "sensor_bias"}
QUALITY_FAULTS = {"dropout", "stuck_sensor"}


def simulate_run(
    cfg: Config, seed: int, run_id: str, scenario: str = "normal",
    split: str = "test", domain: str = "in_domain",
) -> pd.DataFrame:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if domain not in {"in_domain", "noise_shift", "context_shift"}:
        raise ValueError(f"Unknown domain: {domain}")
    rng = np.random.default_rng(seed)
    n = cfg.steps
    t = np.arange(n)
    phase = rng.uniform(0, 2 * np.pi)
    pump = rng.uniform(57, 81) + 5 * np.sin(t / 95 + phase)
    heat = rng.uniform(42, 68) + 4 * np.sin(t / 120 + phase / 2)
    ambient = rng.uniform(18, 25) + 0.4 * np.sin(t / 180 + phase)
    if domain == "context_shift":
        ambient = ambient + 12
    # Benign operating transitions also occur in training and calibration.
    step_at = int(rng.integers(n // 4, n // 2))
    pump[step_at:] += rng.uniform(-6, 6)
    heat[step_at:] += rng.uniform(-7, 7)
    onset = int(rng.integers(int(n * 0.38), int(n * 0.53)))
    if scenario == "load_step":
        heat[onset:] += 10
        pump[onset:] += 4
    ramp = np.clip((t - onset) / max(30, n * 0.12), 0, 1)
    severity = rng.uniform(0.17, 0.36)
    wear = severity * ramp if scenario == "pump_wear" else np.zeros(n)
    cooling = 1 - severity * ramp if scenario == "cooling_loss" else np.ones(n)
    flow = 1.18 * pump[0]
    temp = ambient[0] + heat[0] / (0.08 * flow)
    values = np.empty((n, 4))
    offset = rng.normal(0, [0.10, 0.12, 0.025, 0.012])
    noise = np.array([0.09, 0.25, 0.035, 0.02])
    if domain == "noise_shift":
        noise *= 3
    for i in range(n):
        flow += 0.25 * (1.18 * pump[i] * (1 - wear[i]) - flow)
        target = ambient[i] + heat[i] / (0.08 * max(flow, 10) * cooling[i])
        temp += 0.06 * (target - temp)
        pressure = 1.4 + 0.0005 * flow**2 + 0.002 * heat[i]
        vibration = 0.65 + 0.00009 * pump[i]**2 + 2.4 * wear[i]
        values[i] = [temp + 0.06 * np.sin(i / 35), flow, pressure, vibration]
    values += offset + rng.normal(size=(n, 4)) * noise
    if scenario == "sensor_bias":
        values[:, 0] += rng.uniform(1.2, 3.0) * ramp
    elif scenario == "dropout":
        values[onset:, 0] = np.nan
    elif scenario == "stuck_sensor":
        values[onset:, 1] = values[onset - 1, 1]
    result = pd.DataFrame(values, columns=SENSORS)
    result[CONTEXT] = np.column_stack([heat, pump, ambient])
    result["run_id"] = run_id
    result["seed"] = seed
    result["split"] = split
    result["domain"] = domain
    result["scenario"] = scenario
    result["time_s"] = t * cfg.dt_seconds
    result["fault_active"] = (t >= onset) & (scenario in PROCESS_FAULTS)
    result["quality_fault_active"] = (t >= onset) & (scenario in QUALITY_FAULTS)
    result["event_onset_s"] = onset * cfg.dt_seconds if scenario in PROCESS_FAULTS | QUALITY_FAULTS else -1
    return result


def make_dataset(cfg: Config) -> pd.DataFrame:
    specs = []
    for split, count in [("train", cfg.train_runs), ("calibration", cfg.calibration_runs)]:
        for j in range(count):
            specs.append((split, "in_domain", "load_step" if j % 2 else "normal"))
    for domain, count in [
        ("in_domain", cfg.test_repetitions),
        ("noise_shift", cfg.shift_repetitions),
        ("context_shift", cfg.shift_repetitions),
    ]:
        for scenario in SCENARIOS:
            specs.extend([("test", domain, scenario)] * count)
    streams = np.random.SeedSequence(cfg.seed).spawn(len(specs))
    episodes = []
    for i, ((split, domain, scenario), stream) in enumerate(zip(specs, streams)):
        seed = int(stream.generate_state(1)[0])
        episodes.append(simulate_run(cfg, seed, f"{split}-{i:04d}", scenario, split, domain))
    return pd.concat(episodes, ignore_index=True)

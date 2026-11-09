# Methods

This document defines what the code computes. The default settings are in [configs/default.json](../configs/default.json); observed results are in [artifacts/RESULTS.md](../artifacts/RESULTS.md).

## 1. Experimental units

The synthetic unit is a complete, independently seeded episode. Each contains 600 observations at a two-second interval, spanning timestamps 0–1198 seconds. For exposure calculations, each observation represents two seconds of monitored time. The first 30 observations are warmup.

The split contains:

| Partition | Episodes | Contents |
|---|---:|---|
| Training | 24 | Normal operation and legitimate load transitions |
| Calibration | 12 | Independently generated normal operation and load transitions |
| In-domain test | 56 | Seven scenarios, eight episodes each |
| Noise-shift test | 28 | Seven scenarios, four episodes each; measurement noise multiplied by three |
| Context-shift test | 28 | Seven scenarios, four episodes each; ambient temperature increased by 12 °C |

The seven test scenarios are normal operation, a legitimate load step, pump weakening, reduced cooling, a biased temperature sensor, missing temperature measurements, and a frozen flow sensor. The three continuous anomalies count towards event recall. Missing/frozen measurement events have a separate data-quality recall.

Seeds come from NumPy SeedSequence child streams. Entire episodes, including every feature history, belong to one partition. Labels are available for evaluation and for rejecting contaminated normal-only training data; they are excluded from model predictors.

## 2. Simulator

This is a low-order numerical surrogate for a generic cooling loop. It is not an engineering-validated digital twin.

With pump command u, heat load q, ambient temperature a, flow f, temperature T, pump loss w and cooling factor c, the main updates are:

```text
f[t] = f[t-1] + 0.25 × (1.18 × u[t] × (1 - w[t]) - f[t-1])
T_target[t] = a[t] + q[t] / (0.08 × max(f[t], 10) × c[t])
T[t] = T[t-1] + 0.06 × (T_target[t] - T[t-1])
p[t] = 1.4 + 0.0005 × f[t]^2 + 0.002 × q[t]
v[t] = 0.65 + 0.00009 × u[t]^2 + 2.4 × w[t]
```

Independent episode offsets and sample noise are added. Smooth operating variations and benign transitions prevent “normal” from being one fixed point. Fault onset occurs between 38% and 53% of an episode. Continuous faults ramp up and remain active through the end. A quality failure starts at onset and persists.

All constants are synthetic design choices. The use of named units makes the example readable; it does not establish physical fidelity.

## 3. Causal feature construction

Predictors for the residual model use known operating inputs, not future sensor values:

1. Exponentially smoothed pump command, alpha = 0.25.
2. Its square.
3. The current pump command squared.
4. Current heat load.
5. A smoothed thermal proxy: q / (0.08 × 1.18 × smoothed pump), alpha = 0.06.
6. Smoothed ambient temperature, alpha = 0.06.
7. Current ambient temperature.

Smoothing restarts at every episode boundary and uses adjust=False. There is no centred window, backward filling or cross-episode state. Tests change future values and verify that past predictions stay unchanged.

The feature design deliberately reflects the simulator's functional form. This gives a useful explanatory reference and also introduces simulator–model alignment. Its in-domain advantage is conditional on that alignment.

## 4. Three detectors

For a training distribution x, define median m and robust scale s = max(1.4826 × median(|x − m|), 10⁻⁶).

**Robust sensor limits.** Each of the four measured channels is standardized using its training median and robust scale. The score is the largest absolute standardized value. It ignores operating context.

**Isolation Forest.** A forest with 160 trees and at most 256 sampled points per tree is fitted to the four sensors and three context variables. The score is negative score_samples, so larger means more unusual. The library's default decision threshold is not used.

**Contextual residual.** A StandardScaler–Ridge pipeline with alpha = 1 predicts all four sensors from the causal features. Training residuals establish a median residual and robust residual scale for each sensor:

```text
r_j(t) = observed_j(t) − predicted_j(t)
z_j(t) = |r_j(t) − median_training_residual_j| / robust_training_residual_scale_j
score(t) = max_j z_j(t)
```

The displayed “expected” value includes the residual median offset. Residual bars are exact components of this score, not feature attribution for the forest, causal explanations or posterior failure probabilities.

## 5. Calibration and empirical rarity

Each model's threshold is the 99.5th percentile of clean, post-warmup calibration scores, using NumPy's higher quantile rule. The nominal alpha is 0.005 and is fixed in the configuration.

For score s and calibration scores c₁…cₙ, the empirical tail rank is:

```text
tail(s) = (1 + count(c_i >= s)) / (n + 1)
```

Ties use the conservative >= comparison. The smallest possible value is 1/(n+1).

The calculation resembles a conformal rank, but the samples within an episode are dependent and the stress tests change the distribution. **No conformal coverage guarantee, fault probability or guaranteed false-alarm rate is claimed.** Even under stable conditions, a pointwise threshold does not determine a sequential alarm-start rate.

## 6. Eligibility and abstention

The system checks the following without using scenario labels:

- Finite numeric sensor and context values.
- Explicit broad physical bounds in features.BOUNDS.
- Six identical consecutive readings on any sensor. This is a simple frozen-sensor heuristic.
- Operating context inside the training min–max envelope, expanded by 5% of the training span on each side.

A failed check gives REVIEW, no displayed model score and no process alarm. Missing/range/stuck reasons take precedence over unsupported context. Warmup gives WARMUP and also resets the alarm state. No missing sensor value is silently replaced with a normal reading.

These gates are incomplete. A frozen value with small jitter may evade equality testing; a legitimate quantized sensor may trigger it. Plausible but corrupted data can pass every check. An in-range measurement is not proof that its distribution is familiar.

## 7. Alarm state machine

NORMAL or WATCH becomes ALARM after three consecutive scores strictly above threshold. The start is recorded at the third observation; it is never backdated.

ALARM ends after five consecutive scores strictly below 0.8 × threshold. Scores between the release boundary and the alarm boundary can therefore maintain the alarm. REVIEW and WARMUP reset both the active alarm and the counters. State resets at every episode boundary.

The ablation removes persistence and hysteresis but uses the same score threshold. It counts rising edges of immediate threshold exceedance. A lower count is not automatically better: long alarm occupancy can also reduce the number of starts.

## 8. Evaluation

**New-event recall:** an event is detected only if a new alarm starts at or after its annotated onset, before the episode ends. A previously active alarm does not count. This is intentionally stricter than “any overlap with the anomalous interval”.

**Recall within 120 seconds:** the fraction of all annotated continuous anomalies with a new start within 120 seconds. The same denominator includes undetected and abstained events.

**Detection delay:** first eligible new alarm time minus fault onset. Median delay is reported only among detected events; it must be read with recall.

**False alarm rate:** new alarm starts during annotated normal time divided by monitored normal hours. Warmup, abstention and active quality-failure intervals are excluded from exposure.

**Normal alarm occupancy:** time spent in ALARM during monitored normal operation divided by that normal exposure. This reveals a detector that remains latched.

**Coverage:** the fraction of post-warmup time eligible for a model decision, including fault periods. The definition is identical across detectors.

**Data-quality recall:** whether a missing/range/stuck reason appears during an annotated quality failure. It does not count unsupported context as detecting a missing sensor.

**Average precision:** a secondary, point-level ranking measure, evaluated only where a score is available and no active quality-failure label applies. It is not point-adjusted and does not replace event recall.

Intervals: 95% Wilson intervals for event recall; 400 episode bootstrap replicates for false alarm rates. A zero-count bootstrap can collapse to [0,0]; the JSON also reports a Poisson reference upper bound of −log(0.05)/exposure when there are zero starts. This reference assumes a Poisson count process and is not a guarantee for dependent alarms.

## 9. Measured-data benchmark

UCI 447 is a separate supervised classification experiment. One row represents one completed 60-second rig cycle.

For each of TS1–TS4, FS1–FS2, VS1 and PS1–PS2, the extractor computes mean, population standard deviation, range, and linear slope over normalized cycle time. The slope is a change per cycle, not per second. This creates 36 predictors. Condition annotations, cycle number, the unstable flag and virtual CE/CP/SE channels are excluded from predictors.

The primary label is cooler <100. Pump leakage >0 is an exploratory secondary target introduced after seeing the easy cooler result.

The grouping key is the full (cooler, valve, pump leakage, accumulator) condition tuple. GroupShuffleSplit holds out 25% of groups for test, then 25% of the remaining groups for validation. The resulting sample fractions differ from the group fractions because group sizes vary. The validation split is named “calibration” in shared code, but no probability calibration is performed.

Models: prior-only DummyClassifier; standardized, class-balanced logistic regression (C=1); and class-balanced Random Forest (240 trees, depth 8, minimum leaf 5). The classification threshold is fixed at 0.5. Test metrics include balanced accuracy, macro F1, ROC AUC, average precision and confusion matrices. Bootstrap intervals resample entire condition groups 300 times.

All cycles come from one rig. Condition grouping does not recover unknown acquisition sessions. The task uses full-cycle summaries and cannot establish early-warning latency.

## 10. Interpretation boundaries

There is no parameter search over the test labels, no real-time control connection and no demonstrated improvement in human performance. The current test splits become development evidence if used to redesign the model. A revised detector needs fresh held-out runs, and a real deployment claim needs independently collected data.

See [sources](SOURCES.md) for primary references and [decision records](DESIGN_DECISIONS.md) for alternatives.

# Failure analysis

The most useful result is the disagreement between strong in-domain performance and weak behaviour under sensor noise.

## F01 — An alarm can conceal the start of another event

At three times the measurement noise, the contextual residual detector frequently crosses its normal-calibration threshold. Once active, the alarm requires five consecutive sufficiently low scores to clear. Noisy observations can prevent that release.

The result is 36 false alarm starts in approximately 5.08 monitored normal hours and 0/12 detected new fault events. The latter uses a strict new-start definition. It does not mean that the fault scores are low.

**Evidence:** compare event_metrics.csv, the normal_alarm_occupancy summary, and the noise-shift replay. Read score ranking and event signalling separately.

**Next experiment:** define a development set for choosing a residual-volatility gate or revised alarm acknowledgement/reset logic. Freeze the proposal, then generate new held-out episodes from fresh seeds. Report detection, false starts, occupancy and coverage together. An apparent reduction in false starts is insufficient if the system simply stays in alarm.

## F02 — Context gating protects interpretation at the cost of coverage

The +12 °C scenario lies outside the training envelope. The system returns REVIEW and no process score. Its zero monitored exposure produces an unavailable false-alarm rate, not a zero rate.

This is expected implementation behaviour. It does not solve the task of monitoring under that context.

**Next experiment:** define an extended operating envelope using independent normal data. Keep a held-out boundary region and report coverage versus missed events. Do not expand the gate using the existing stress labels and call that independent validation.

## F03 — The generator favours the residual model

The conditional features reflect the functional structure used in simulation. The model is therefore well specified for much of the in-domain experiment.

**Next experiment:** alter the data-generating dynamics independently: response delays, nonlinear cooling curves, changing process offsets and coupled failures. Develop the detector on one simulator family and evaluate on another. A truly external claim still requires measurements from independent equipment.

## F04 — Exact repetition is an incomplete frozen-sensor detector

The current gate detects six exactly equal consecutive values. It is easy to explain and test, but it does not model quantization or uncertainty.

**Possible errors:** legitimate plateaus may be flagged; a frozen value with tiny jitter may not be flagged. Slow sensors also require a different sampling-aware duration.

**Next experiment:** evaluate a variance-and-consistency rule across noise, quantization and benign steady states. Keep “data-quality detection” separate from physical fault recall.

## F05 — The real-data benchmark is unusually easy

The cooler and exploratory pump tasks are perfectly separated by the fitted classifiers on this grouped split. This may reflect strong physical relationships in the one-rig data and does not demonstrate broad generalization.

**Next experiment:** evaluate under independently acquired sessions or on another rig. If such metadata cannot be obtained, narrow the claim. Feature-family ablations can reveal which channels carry signal, but they cannot create external validation.

The random-row comparison also scores perfectly. It therefore illustrates different split exposure rather than providing empirical evidence that this particular random split inflated the score.

## F06 — Human-centred intent has not been measured

An explicit REVIEW state and visible residuals may help people, but may also cause overload or unwarranted trust. The current verification only proves that the interface displays the specified values.

**Next experiment:** run the bounded study in HUMAN_FACTORS_STUDY.md. Measure whether participants recognize unavailable evidence and avoid treating residuals as causal diagnoses.

## Reading the results without overclaiming

- “24/24 simulated anomalies were detected” is supported.
- “The system detects all equipment failures” is not supported.
- “The interface exposes the largest standardized residuals” is supported.
- “The interface improves operator decisions” has not been tested.
- “Both classifiers perfectly classified this one-rig holdout” is supported.
- “The classifier is validated for other rigs, clinical data or nuclear operation” is not supported.

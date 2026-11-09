# Model card

**Version:** 0.1.0  
**Purpose:** research and portfolio demonstration of anomaly monitoring and alarm evaluation.  
**Authoring:** substantial AI-assisted initial implementation; see [authorship note](../AI_ASSISTANCE.md).

## Inputs and outputs

The normal-only monitoring suite expects four sensor channels and three operating inputs sampled every two seconds, grouped into ordered episodes. It returns anomaly scores, empirical tail ranks, quality reasons, expected sensor values and causal alarm states.

The separate UCI classifiers consume 36 full-cycle summary features. They return class probabilities and binary classifications at a fixed threshold. Their probabilities have not been calibrated.

## Training

The anomaly models use 24 synthetic normal episodes. Thresholds use 12 separate normal episodes. The residual model's features and functional form reflect the simulator, which is a major limitation of external validity.

The supervised classifiers use one hydraulic rig's measured cycles. Full condition groups separate training, validation and test. There is no adaptation of the synthetic model to those measurements.

## What the outputs mean

| Output | Meaning | Unsupported interpretation |
|---|---|---|
| Residual z score | Difference from the fitted expectation, scaled by training residual variability | Number of standard deviations under a proven normal law |
| Empirical tail rank | Relative rarity against calibration scores | Probability of a physical fault |
| ALARM | The selected score satisfies the implemented state machine | Confirmed root cause or required control action |
| NORMAL | No active persistent alarm under this model and input | Proof of safe or fault-free operation |
| REVIEW | The model has insufficient input or unsupported context | An identified equipment fault |
| Coverage | Fraction of post-warmup time with eligible decisions | Accuracy on abstained observations |

## Observed behaviour

The contextual residual model detects 24/24 in-domain synthetic anomalies, with one false start in about 10.29 monitored normal hours. The same system detects 0/12 new events under threefold noise, because it can alarm before the event and remain latched.

The context-shift gate produces no scored exposure under the prescribed ambient shift. This is explicit abstention, not successful detection.

The real-data classifiers obtain perfect observed classification on the selected one-rig holdout. Neither this observation nor a [1,1] bootstrap interval establishes perfect future performance.

## Intended users

Students, interviewers and researchers reviewing methods, assumptions and evaluation design. The interface supports a recorded demonstration and formative human-factors research.

## Operational boundaries

There is no control API or actuation. The project is not validated for nuclear facilities, clinical care, equipment protection or safety certification. It does not prescribe corrective plant actions. Meaningful deployment evidence would require independent domain data, prospective testing, integration engineering and domain-specific validation.

## Failure modes to inspect

- A noise distribution change can cause sustained alarms.
- A frozen sensor with small jitter can evade the exact-equality gate.
- Legitimately repeated or quantized readings can trigger that gate.
- A normal context outside the training envelope reduces coverage.
- Plausible corrupted measurements can pass all gates.
- A high residual can come from misspecified context or model assumptions.
- Raw thresholds and Isolation Forest can miss faults whose absolute values remain familiar.

See [failure analysis](FAILURE_ANALYSIS.md) for proposed follow-up experiments and [study protocol](HUMAN_FACTORS_STUDY.md) for human evaluation.

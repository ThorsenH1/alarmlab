# Proposed formative study

**Status: protocol only. No participants have been recruited and no study results are claimed.**

## Question

Does showing data-quality state and residual evidence help people distinguish an interpretable process anomaly from an unavailable model assessment?

This is a small formative study of an interface and task. It cannot validate professional control-room performance.

## Participants and setting

Start with 6–8 consenting students who understand basic plots. Use a local copy of the demo. Collect a participant code rather than a name. Do not collect patient data or employer information.

For any later professional study, collaborate with qualified domain researchers and follow the host institution's study and data-handling procedures.

## Conditions

**A: trend-only.** Show sensor trends and current values.

**B: assisted.** Show the same trends plus model status, residual evidence and the data-quality message.

The current demo implements condition B. An experimental trend-only mode, automatic task timing and counterbalanced assignment must be implemented before this protocol is executed. The present interface is not described as an already completed experiment platform.

Use separate episodes of similar difficulty in the two conditions. Counterbalance order (AB/BA), scenario assignment and fault type. Do not let a participant see the same trace twice. A pilot should check comparable difficulty before formal comparisons.

## Tasks

Each participant reviews six short scenarios: normal drift, a legitimate load change, a continuous anomaly, missing measurements, a frozen sensor and unfamiliar context. Use newly generated episodes so the demonstrator does not inadvertently teach the exact test answers.

At a fixed review time, ask participants to:

1. Classify the available evidence as normal variation, plausible process anomaly, data-quality problem, or insufficient context.
2. Identify the observations supporting that classification.
3. Record whether further information is needed.
4. Rate confidence on a five-point scale.

Participants must not be asked to recommend real equipment actions.

## Measures

**Primary:** proportion of correct evidence-category judgments, according to a pre-specified scoring rubric.

**Secondary:** time to submit; correct recognition of REVIEW; unsupported causal claims in the written explanation; confidence on correct versus incorrect responses; a brief effort rating.

Avoid using button clicks or a high confidence score as a proxy for a good decision. A low-confidence “insufficient evidence” response can be the appropriate answer.

## Scoring rubric

| Scenario family | Expected evidence judgment | Error to examine |
|---|---|---|
| Normal / benign load change | No confirmed process anomaly from the available evidence | Treating a legitimate shift as a definite failure |
| Continuous fault | Investigate coherent deviation from expectation | Naming an exact root cause as proven |
| Missing or frozen measurements | Evaluate measurement quality | Treating unavailable assessment as normal |
| Unsupported context | Model applicability is insufficient | Reading an extrapolated value as validated evidence |

Because a user's reasonable inference can differ from the injected scenario label, have two reviewers score free-text explanations using the rubric. Resolve disagreements explicitly.

## Analysis

Report participant-level paired differences, task-level examples and the complete distribution of outcomes. Resample participants, not individual clicks, for exploratory uncertainty intervals. With a small convenience sample, emphasize observed patterns and usability problems instead of population-level superiority claims.

Document order effects, prior knowledge, practice and missing responses. The primary comparison and scoring rubric should be fixed before seeing results.

## Data and reproducibility

The existing local export includes run ID, simulated timestamp, model state, rationale, truth-visibility flag and prediction hash. It does not yet contain participant assignment or automated elapsed task time; add those explicitly for the study.

Keep ground truth hidden during tasks. Export to a study-specific directory with participant codes. Delete identifying content according to the agreed retention plan. Publish only genuinely consented, appropriately anonymized study outputs.

## Completion criteria

Before claiming a human-performance result: implement both conditions; verify assignment and timing; finish the pilot; freeze the analysis plan; collect consented data; apply the scoring rubric; report all planned outcomes and limitations.

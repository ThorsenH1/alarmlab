# Design decisions

These records summarize decisions, reasons and trade-offs. They document the implemented design rather than inventing an extended development history.

## D01 — Evaluate a new alarm, not only an unusual sample

**Decision:** A pre-existing alarm does not count as detecting a later event.

**Reason:** The project asks whether a person receives a new signal at the relevant time. Overlap-based detection can give a detector that is always alarming a misleadingly high recall.

**Alternative considered:** Count any alarm within the fault interval. That is meaningful for some monitoring tasks, but answers a different question.

**Cost:** Strict recall can be zero even when all anomalous samples have high scores. Alarm occupancy and traces are therefore reported alongside it.

## D02 — Use a simple conditional model

**Decision:** Ridge regression predicts sensors from causal, process-informed features.

**Reason:** Its residuals expose what the system expected and which measurements diverged. The model is light enough to reproduce on an ordinary laptop.

**Alternatives considered:** An LSTM, temporal autoencoder or transformer could learn richer dynamics. This dataset and research question do not establish that their added complexity is necessary.

**Cost:** Handcrafted features match the simulator well. This alignment must be stated when interpreting the comparison.

## D03 — Keep a context-ignorant reference and a non-linear reference

**Decision:** Compare robust sensor limits and Isolation Forest against the residual model.

**Reason:** The first tests whether modelling context adds value. The second tests against a recognizable non-linear anomaly detector.

**Cost:** The models have different inductive biases. This is a defined comparison, not an exhaustive search for the best detector.

## D04 — Split entire episodes

**Decision:** Assign independent simulated runs to training, calibration and test.

**Reason:** Adjacent measurements share operating conditions, offsets and dynamics. Random row splits would make unseen samples look more independent than they are.

**Medical parallel:** Repeated patient observations should not make the same patient appear on both sides of an intended new-patient test.

**Cost:** There are fewer independent units than rows. Intervals must respect that.

## D05 — Fix the threshold on normal calibration data

**Decision:** Use a fixed 99.5th-percentile threshold and report actual alarm behaviour.

**Reason:** Fault labels are not required to calibrate rarity, and test faults stay outside threshold choice.

**Alternative considered:** Optimize F1 or event recall directly on the labelled test set.

**Cost:** Alpha does not guarantee a false-alarm-per-hour target. It also cannot protect against distribution shift.

## D06 — Make unavailable evidence a visible state

**Decision:** Missing data and unsupported context lead to REVIEW rather than a normal score.

**Reason:** A reassuring output with no adequate input is difficult to interpret responsibly. Coverage makes the trade-off measurable.

**Cost:** Abstention can hide useful signal if the gate is too conservative. All abstained fault episodes remain misses in end-to-end recall.

## D07 — Separate sensor evidence from root-cause diagnosis

**Decision:** Show standardized sensor residuals and label their meaning.

**Reason:** A large temperature residual supports “temperature differs from this reference model”. It does not identify whether a real pump, sensor, load estimate or model assumption caused it.

**Cost:** The interface requires human interpretation. A validated diagnostic model would be a separate task.

## D08 — Keep the measured-data benchmark separate

**Decision:** Train supervised classifiers on UCI cycle summaries and report them independently.

**Reason:** The measured data have different sensors, targets and time structure. Combining the scores would create a false impression of external validation of the synthetic detector.

**Cost:** The project has two clearly bounded experiments rather than one claimed universal model.

## D09 — Group real data by full condition recipe

**Decision:** An identical cooler/valve/pump/accumulator combination cannot cross a split.

**Reason:** Repeated cycles under the same setup should not be treated as wholly new operating conditions.

**Alternatives considered:** Random cycles, chronological splits, or leave-one-rig-out. Random cycles are provided only as a diagnostic. A reliable chronological/session split is not inferred from undocumented row order. A second rig is unavailable.

**Cost:** Grouping by recipe cannot remove all dependence and may create different class proportions. The claims remain within one rig.

## D10 — Preserve the noisy-sensor failure

**Decision:** Keep the observed failure and explain the alarm latch.

**Reason:** Revising thresholds after observing the stress labels would turn those labels into development feedback. A mature experiment records what the original choice did.

**Next decision:** A noise monitor or revised reset policy can be developed using a declared development set and evaluated on a new untouched seed suite.

## D11 — Deliver an offline replay

**Decision:** Generate a single HTML file containing the traces and metrics.

**Reason:** A reviewer can inspect it without accounts, external APIs or package installation. Python remains the single source of model predictions and metrics.

**Cost:** Changing a model or data generator requires rebuilding the file. The demo is not live inference and cannot receive plant data.

## D12 — Plan human evaluation without fabricating it

**Decision:** Include a counterbalanced study protocol and an assessment log, with no claim that a study was run.

**Reason:** A readable interface is not sufficient evidence of improved decisions. Task correctness, timing and user understanding need measurement.

**Cost:** Human-centred intent is implemented; human-performance benefit remains unverified.

## D13 — Name the project independently

**Decision:** Use AlarmLab as the repository and product name.

**Reason:** The technical contribution should stand on its own. The IFE connection belongs in the application context and source mapping.

**Cost:** The name deliberately describes a research environment rather than a production safety system.

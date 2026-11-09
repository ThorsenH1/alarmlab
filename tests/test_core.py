import unittest
import numpy as np
import pandas as pd

from alarmlab.alarms import alarm_states
from alarmlab.benchmark import split_cycles
from alarmlab.config import Config
from alarmlab.evaluation import event_table, wilson_interval
from alarmlab.features import causal_features, quality_reasons, validate_frame
from alarmlab.models import DetectorSuite, METHODS, empirical_tail
from alarmlab.simulator import make_dataset, simulate_run, SENSORS, CONTEXT


class SimulatorTests(unittest.TestCase):
    def test_reproducible_and_disjoint_episodes(self):
        cfg = Config(steps=180, train_runs=4, calibration_runs=2, test_repetitions=2, shift_repetitions=1)
        a, b = make_dataset(cfg), make_dataset(cfg)
        pd.testing.assert_frame_equal(a, b)
        self.assertTrue(a.groupby("run_id").split.nunique().eq(1).all())
        self.assertEqual(a.groupby("run_id").seed.first().nunique(), a.run_id.nunique())
        self.assertFalse(a[a.split != "test"].fault_active.any())

    def test_causal_features_ignore_future(self):
        frame = simulate_run(Config(), 12, "a", "sensor_bias")
        original = causal_features(frame)
        changed = frame.copy()
        changed.loc[300:, "heat_kw"] += 20
        np.testing.assert_allclose(original[:300], causal_features(changed)[:300])

    def test_features_do_not_read_outcome_columns(self):
        frame = simulate_run(Config(), 12, "a")
        original = causal_features(frame)
        changed = frame[["run_id", "time_s", *SENSORS, *CONTEXT]].copy()
        np.testing.assert_allclose(original, causal_features(changed))

    def test_reject_duplicate_or_out_of_order_timestamps(self):
        frame = simulate_run(Config(), 12, "a")
        with self.assertRaises(ValueError):
            validate_frame(pd.concat([frame, frame.iloc[:1]], ignore_index=True))
        with self.assertRaises(ValueError):
            validate_frame(frame.iloc[::-1])
        frame.loc[100, "time_s"] += 1
        with self.assertRaises(ValueError):
            validate_frame(frame)

    def test_stuck_sensor_is_detected_causally(self):
        frame = simulate_run(Config(), 12, "a", "stuck_sensor")
        reason = quality_reasons(frame)
        start = int(frame.event_onset_s.iloc[0] / 2)
        self.assertFalse((reason[:start] == "stuck_sensor").any())
        self.assertTrue((reason[start + 4:] == "stuck_sensor").all())


class AlarmTests(unittest.TestCase):
    def test_persistence_and_hysteresis(self):
        scores = np.array([1, 3, 3, 3, 1.9, 1, 1, 1, 1, 1])
        states, starts = alarm_states(scores, 2, np.ones(10, bool), np.zeros(10, bool))
        self.assertEqual(states.tolist(), [
            "NORMAL", "WATCH", "WATCH", "ALARM", "ALARM",
            "ALARM", "ALARM", "ALARM", "ALARM", "NORMAL",
        ])
        self.assertEqual(np.flatnonzero(starts).tolist(), [3])

    def test_abstention_resets_alarm_evidence(self):
        states, starts = alarm_states(
            [3, 3, 3, 3, 3, 3], 2,
            [True, True, False, True, True, True], [False] * 6,
        )
        self.assertEqual(states[2], "REVIEW")
        self.assertEqual(np.flatnonzero(starts).tolist(), [5])

    def test_unequal_lengths_rejected(self):
        with self.assertRaises(ValueError):
            alarm_states([3, 3], 2, [True], [False, False])

    def test_no_backdated_detection(self):
        frame = simulate_run(Config(), 12, "a", "pump_wear")
        frame["eligible"], frame["warmup"] = True, False
        frame["quality_reason"] = ""
        for method in METHODS:
            frame[f"{method}_alarm_start"] = False
            frame.loc[0, f"{method}_alarm_start"] = True
            frame[f"{method}_status"] = "ALARM"
        events = event_table(frame, Config())
        self.assertTrue(events.detected_event.eq(0).all())
        self.assertTrue(events.false_starts.eq(1).all())

    def test_tail_rank_handles_ties_and_missing(self):
        values = empirical_tail([1, 2, 2, 4], [0, 2, 5, np.nan])
        np.testing.assert_allclose(values[:3], [1, 0.8, 0.2])
        self.assertTrue(np.isnan(values[3]))

    def test_wilson_does_not_claim_certainty_at_perfect_recall(self):
        low, high = wilson_interval(8, 8)
        self.assertLess(low, 0.8)
        self.assertAlmostEqual(high, 1)


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = Config(steps=240, train_runs=16, calibration_runs=8, test_repetitions=2, shift_repetitions=1)
        cls.data = make_dataset(cls.cfg)
        cls.train = cls.data[cls.data.split == "train"]
        cls.cal = cls.data[cls.data.split == "calibration"]
        cls.test = cls.data[cls.data.split == "test"]
        cls.suite = DetectorSuite(cls.cfg).fit(cls.train, cls.cal)

    def test_training_calibration_overlap_rejected(self):
        with self.assertRaises(ValueError):
            DetectorSuite(self.cfg).fit(self.train, self.train)

    def test_faults_rejected_during_normal_training(self):
        bad = self.train.copy()
        bad.loc[bad.index[90], "fault_active"] = True
        with self.assertRaises(ValueError):
            DetectorSuite(self.cfg).fit(bad, self.cal)

    def test_test_labels_do_not_affect_predictions(self):
        first = self.suite.predict(self.test)
        changed = self.test.copy()
        changed["fault_active"] = ~changed.fault_active
        changed["scenario"] = "changed_truth"
        second = self.suite.predict(changed)
        for method in METHODS:
            np.testing.assert_allclose(
                first[f"{method}_score"], second[f"{method}_score"], equal_nan=True
            )
            self.assertEqual(first[f"{method}_status"].tolist(), second[f"{method}_status"].tolist())

    def test_all_missing_is_review_not_normal(self):
        frame = self.test.iloc[:240].copy()
        frame[SENSORS] = np.nan
        pred = self.suite.predict(frame)
        self.assertTrue(pred.iloc[30:].contextual_residual_status.eq("REVIEW").all())
        self.assertTrue(pred.contextual_residual_score.isna().all())

    def test_unsupported_context_is_review(self):
        frame = self.test.iloc[:240].copy()
        frame["ambient_c"] = 45
        pred = self.suite.predict(frame)
        self.assertTrue(pred.iloc[30:].contextual_residual_status.eq("REVIEW").all())
        self.assertTrue(pred.contextual_residual_score.isna().all())

    def test_predict_has_no_future_dependency(self):
        frame = self.test.iloc[:240].copy()
        prefix = self.suite.predict(frame.iloc[:160])
        full = self.suite.predict(frame)
        for method in METHODS:
            pd.testing.assert_series_equal(
                prefix[f"{method}_status"], full.iloc[:160][f"{method}_status"]
            )


class BenchmarkSplitTests(unittest.TestCase):
    def test_condition_groups_never_cross_splits(self):
        rows = []
        for cooler in [3, 20, 100]:
            for valve in [73, 80, 90, 100]:
                for pump in [0, 1, 2]:
                    for accumulator in [90, 100, 115, 130]:
                        rows.extend([{
                            "cooler": cooler, "valve": valve,
                            "pump_leakage": pump, "accumulator": accumulator,
                        }] * 3)
        data = pd.DataFrame(rows)
        splits, groups = split_cycles(data, 42)
        sets = {name: set(groups.iloc[index]) for name, index in splits.items()}
        self.assertFalse(sets["train"] & sets["test"])
        self.assertFalse(sets["train"] & sets["calibration"])
        self.assertFalse(sets["calibration"] & sets["test"])
        self.assertEqual(sum(len(x) for x in splits.values()), len(data))


if __name__ == "__main__":
    unittest.main()

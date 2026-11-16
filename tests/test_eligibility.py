"""Protect the patient sets and denominators used in the rule comparison."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from data_preprocess import FEATURES, MEASURES, load_view, preprocess
from eligibility import compare_rules, select_records


class EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        preprocess(ROOT / "data/raw/ckd.csv", Path(cls.tmp.name))
        cls.observed = load_view(Path(cls.tmp.name), "observed")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_rule_counts_and_observed_denominators(self):
        self.assertIsNotNone(compare_rules, "Implement the eligibility comparison")
        table = compare_rules(self.observed).set_index(["rule", "group"])
        for rule, counts in {"all24": (158, 43, 115), "core5": (300, 165, 135),
                             "renal_pair": (380, 236, 144), "glucose": (356, 212, 144)}.items():
            for group, n in zip(("all", "ckd", "notckd"), counts):
                self.assertEqual(table.loc[(rule, group), "n_retained"], n)
        self.assertEqual(table.loc[("core5", "ckd"), "n_glucose_high"], 61)
        self.assertEqual(table.loc[("core5", "ckd"), "n_glucose_measured"], 165)
        self.assertEqual(table.loc[("all24", "ckd"), "n_glucose_high"], 20)
        self.assertEqual(table.loc[("glucose", "ckd"), "n_glucose_high"], 72)

    def test_record_43_is_retained_when_only_core_measurements_are_needed(self):
        self.assertIsNotNone(select_records, "Implement patient eligibility selection")
        self.assertNotIn(43, select_records(self.observed, FEATURES).index)
        core = select_records(self.observed, MEASURES)
        self.assertIn(43, core.index)
        pd.testing.assert_series_equal(core.loc[43], self.observed.loc[43])

    def test_unknown_or_empty_required_fields_are_rejected(self):
        self.assertIsNotNone(select_records, "Implement patient eligibility selection")
        for fields in [[], ["class"], ["unknown"]]:
            with self.assertRaises(ValueError):
                select_records(self.observed, fields)


if __name__ == "__main__":
    unittest.main()

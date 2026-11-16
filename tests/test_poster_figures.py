"""Check the source patients and denominators behind the poster's case entry."""
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/poster"))
import poster_figures as poster


class PosterSourceTests(unittest.TestCase):
    def test_case_panel_uses_record_43_measurements(self):
        text = poster.case_summary_text()
        for value in ("204", "9.7", "1.0", "Grade 0", "Yes", "No"):
            self.assertIn(value, text)

    def test_glucose_scatter_keeps_every_measured_patient(self):
        points, summary = poster.glucose_history_data()
        source = pd.read_csv(ROOT / "docs/reanalysis/clinical_tables/patient_measurements.csv")
        source = source.dropna(subset=["bgr"]).set_index("row_id").bgr.sort_index()
        actual = points.set_index("row_id").bgr.sort_index()
        pd.testing.assert_series_equal(actual, source)
        self.assertEqual(len(points), 212)
        self.assertEqual(points.loc[points.row_id.eq(43), "bgr"].item(), 204)
        self.assertEqual(points.loc[points.row_id.eq(43), "dm"].item(), "no")
        self.assertTrue(points.row_id.is_unique)
        self.assertEqual(summary.set_index("dm").loc["no", ["n_measured", "n_high", "n_missing"]].tolist(), [87, 11, 26])
        self.assertEqual(summary.set_index("dm").loc["yes", ["n_measured", "n_high", "n_missing"]].tolist(), [125, 61, 12])

    def test_glucose_bounds_keep_the_original_cohort_and_each_view_denominator(self):
        totals, views = poster.glucose_bounds_data()
        self.assertEqual([totals[key] for key in ("n_total", "n_high", "n_missing", "n_below")],
                         [250, 72, 38, 140])
        self.assertAlmostEqual(totals["lower"], 72 / 250)
        self.assertAlmostEqual(totals["upper"], 110 / 250)
        views = views.set_index("view")
        for key, expected in (("observed", [212, 72]), ("complete_case", [43, 20]),
                              ("imputed", [250, 72])):
            self.assertEqual(views.loc[key, ["n", "n_high"]].tolist(), expected)
            self.assertAlmostEqual(views.loc[key, "share"], expected[1] / expected[0])
        self.assertGreater(views.loc["complete_case", "share"], totals["upper"])

    def test_grade_zero_matrix_keeps_patient_identity_and_shows_all_16_exclusions(self):
        grade = poster.grade_zero_data()
        source = pd.read_csv(ROOT / "docs/reanalysis/clinical_tables/patient_measurements.csv")
        expected_ids = source.loc[source.al.eq(0) & source.anemia.notna() & source.bgr.notna(), "row_id"]
        self.assertEqual(set(grade.row_id), set(expected_ids))
        self.assertTrue(grade.row_id.is_unique)
        self.assertEqual(len(grade), 45)
        self.assertEqual(int(grade.finding.sum()), 16)
        self.assertEqual(int(grade.complete_case.sum()), 1)
        self.assertEqual(int((grade.complete_case & grade.finding).sum()), 0)
        case = grade.set_index("row_id").loc[43]
        self.assertEqual(case.bgr, 204)
        self.assertTrue(case.finding)
        self.assertFalse(case.complete_case)


if __name__ == "__main__":
    unittest.main()

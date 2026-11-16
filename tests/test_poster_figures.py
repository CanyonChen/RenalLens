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


if __name__ == "__main__":
    unittest.main()

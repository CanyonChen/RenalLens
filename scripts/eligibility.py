"""Compare explicitly named observed-record eligibility rules."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from data_preprocess import FEATURES, MEASURES, load_view

RULES = {
    "all24": FEATURES,
    "core5": MEASURES,
    "renal_pair": ("sc", "bu"),
    "glucose": ("bgr",),
}


def select_records(observed, required):
    """Return original measurements for records complete in the named features."""
    required = tuple(required)
    if not required or not set(required).issubset(FEATURES):
        raise ValueError("Specify at least one documented explanatory feature.")
    return observed.dropna(subset=list(required))


def compare_rules(observed):
    rows = []
    for rule, fields in RULES.items():
        retained = select_records(observed, fields)
        for group in ("all", "ckd", "notckd"):
            original = observed if group == "all" else observed[observed["class"].eq(group)]
            frame = retained if group == "all" else retained[retained["class"].eq(group)]
            glucose = frame.bgr.dropna()
            paired = frame[["sc", "bu"]].dropna()
            rows.append({
                "rule": rule, "required_fields": ",".join(fields), "group": group,
                "n_original_group": len(original), "n_retained": len(frame),
                "retention": len(frame) / len(original) if len(original) else np.nan,
                "share_of_retained": len(frame) / len(retained) if len(retained) else np.nan,
                "n_creatinine_measured": frame.sc.count(), "median_creatinine": frame.sc.median(),
                "n_glucose_measured": len(glucose), "n_glucose_high": int(glucose.ge(200).sum()),
                "glucose_high_share": glucose.ge(200).mean(),
                "n_renal_pairs": len(paired),
                "renal_pearson": paired.sc.corr(paired.bu) if len(paired) > 1 else np.nan,
                "renal_spearman": paired.sc.corr(paired.bu, method="spearman") if len(paired) > 1 else np.nan,
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("docs/reanalysis/tables"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    compare_rules(load_view(args.processed_dir, "observed")).to_csv(args.output_dir / "eligibility_rules.csv", index=False)

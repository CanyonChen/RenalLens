"""Describe measured distributions and single-record influence in the CKD study."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from scipy import stats

from data_preprocess import MEASURES, UNITS, load_view, preprocess


ROOT = Path(__file__).resolve().parents[1]


def distribution_diagnostics(observed: pd.DataFrame) -> pd.DataFrame:
    """Compute distributional screens before any deletion or imputation.

    The natural-log comparison follows the project's pooled positivity/skew rule,
    keeping the transformation fixed across diagnostic groups. Shapiro-Wilk and
    median-centered Levene p-values describe model diagnostics only.
    """
    rows = []
    groups = list(observed.groupby("class", sort=True, dropna=False))
    for feature in MEASURES:
        all_measured = observed[feature].dropna()
        use_log = all_measured.min() > 0 and all_measured.skew() > 0
        group_arrays = [group[feature].dropna() for _, group in groups]
        levene = stats.levene(*group_arrays, center="median")
        for label, frame in [("all", observed), *groups]:
            values = frame[feature].dropna()
            q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            normality = stats.shapiro(values)
            rows.append({
                "feature": feature, "unit": UNITS[feature], "group": label,
                "n_records": len(frame), "n_measured": len(values),
                "n_missing": len(frame) - len(values),
                "mean": values.mean(), "sd": values.std(ddof=1),
                "minimum": values.min(), "q1": q1, "median": median,
                "q3": q3, "maximum": values.max(),
                "iqr_lower_fence": lower, "iqr_upper_fence": upper,
                "n_below_fence": (values < lower).sum(),
                "n_above_fence": (values > upper).sum(),
                "raw_skewness": values.skew(),
                "n_log_pairs": len(values) if use_log else 0,
                "ln_skewness": np.log(values).skew() if use_log else np.nan,
                "shapiro_w": normality.statistic, "shapiro_p": normality.pvalue,
                "levene_between_groups_f": levene.statistic if label == "all" else np.nan,
                "levene_between_groups_p": levene.pvalue if label == "all" else np.nan,
            })
    return pd.DataFrame(rows)


def renal_influence(observed: pd.DataFrame) -> pd.DataFrame:
    """Omit each measured pair once, retaining all pairs in the primary estimate."""
    measured = observed[["class", "sc", "bu"]].dropna(subset=["sc", "bu"])
    creatinine = measured["sc"].to_numpy()
    urea = measured["bu"].to_numpy()
    pearson_all = stats.pearsonr(creatinine, urea).statistic
    spearman_all = stats.spearmanr(creatinine, urea).statistic
    positions = np.arange(len(measured))
    rows = []
    for pos, (row_id, group, sc, bu) in enumerate(measured.itertuples(name=None)):
        keep = positions != pos
        pearson = stats.pearsonr(creatinine[keep], urea[keep]).statistic
        spearman = stats.spearmanr(creatinine[keep], urea[keep]).statistic
        rows.append({
            "omitted_row_id": row_id, "group": group, "sc_mg_dl": sc, "bu_mg_dl": bu,
            "n_all": len(measured), "n_after_omission": len(measured) - 1,
            "pearson_all": pearson_all, "pearson_after_omission": pearson,
            "pearson_change": pearson - pearson_all,
            "spearman_all": spearman_all, "spearman_after_omission": spearman,
            "spearman_change": spearman - spearman_all,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/raw/ckd.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reanalysis/tables")
    args = parser.parse_args()
    with TemporaryDirectory() as processed:
        preprocess(args.source, Path(processed))
        observed = load_view(Path(processed), "observed")
    distribution = distribution_diagnostics(observed)
    influence = renal_influence(observed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    distribution.to_csv(args.output_dir / "diagnostics.csv", index=False)
    influence.to_csv(args.output_dir / "diagnostics_renal_influence.csv", index=False)
    print(f"{len(distribution)} distribution summaries; {len(influence)} single-record omissions.")


if __name__ == "__main__":
    main()

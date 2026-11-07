"""Compare the three prespecified CKD data views on descriptive EDA outcomes."""

import argparse
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from data_preprocess import CATEGORIES, FEATURES, MEASURES, UNITS, load_view, patient_records, write_report


VIEWS = ("observed", "complete_case", "imputed")
GROUPS = ("ckd", "notckd")
CLINICAL_PAIRS = (("sc", "al"), ("bu", "al"), ("hemo", "ane"), ("bgr", "dm"), ("bp", "htn"))


def missing_rates(mask):
    counts = mask[list(FEATURES)].sum().astype(int)
    return pd.DataFrame({
        "feature": counts.index, "n_records": len(mask),
        "n_missing": counts.to_numpy(), "missing_rate": counts.to_numpy() / len(mask),
    }).sort_values("missing_rate", ascending=False, kind="stable")


def group_composition(views):
    # Use an explicit reporting category for an unlabeled record. Keep the label in the data intact.
    original_counts = views["observed"]["class"].fillna("unknown").value_counts()
    groups = (*GROUPS, "unknown") if "unknown" in original_counts else GROUPS
    rows = []
    for view, frame in views.items():
        counts = frame["class"].fillna("unknown").value_counts()
        for group in groups:
            original = int(original_counts.get(group, 0))
            retained = int(counts.get(group, 0))
            rows.append({
                "view": view, "group": group, "n_view": len(frame),
                "n_original_group": original, "n_group": retained,
                "n_lost": original - retained,
                "share_of_view": retained / len(frame) if len(frame) else np.nan,
                "within_group_retention": retained / original if original else np.nan,
            })
    return pd.DataFrame(rows)


def distribution_summary(views, mask):
    medians = views["observed"][list(MEASURES)].median()
    rows = []
    for view, frame in views.items():
        for group in ("all", *GROUPS):
            subset = frame if group == "all" else frame[frame["class"] == group]
            for feature in MEASURES:
                values = subset[feature].dropna()
                n = len(values)
                q1, q3 = values.quantile([0.25, 0.75])
                filled = mask.loc[values.index, feature].eq(1)
                n_imputed = int(filled.sum())
                # Filled cells equal the global median by construction, including midpoints
                # whose decimal representation may round differently when reloading CSV.
                at_median = n_imputed + int(values[~filled].eq(medians[feature]).sum())
                rows.append({
                    "view": view, "group": group, "feature": feature, "unit": UNITS[feature],
                    "n_records": len(subset), "n": n,
                    "n_imputed": n_imputed,
                    "mean": values.mean(), "median": values.median(),
                    "sample_sd": values.std(ddof=1), "q1": q1, "q3": q3, "iqr": q3 - q1,
                    "skewness": values.skew(), "observed_global_median": medians[feature],
                    "n_at_observed_global_median": at_median,
                    "share_at_observed_global_median": at_median / n if n else np.nan,
                })
    return pd.DataFrame(rows)


def clinical_strata(views, mask):
    """Summarize each view's readings within the originally recorded clinical strata."""
    observed = views["observed"]
    rows = []
    for view, frame in views.items():
        source = observed.loc[frame.index]
        for group in GROUPS:
            group_source = source.loc[source["class"].eq(group)]
            for feature, context in CLINICAL_PAIRS:
                levels = group_source[context].fillna("unrecorded")
                for level in (*CATEGORIES[context], "unrecorded"):
                    ids = levels.index[levels.eq(level)]
                    values = frame.loc[ids, feature].dropna()
                    n_imputed = int(mask.loc[values.index, feature].sum())
                    q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
                    rows.append({
                        "view": view, "group": group, "feature": feature, "context": context,
                        "level": level, "unit": UNITS[feature], "n_group": len(group_source),
                        "n_stratum": len(ids), "n_measured": len(values) - n_imputed,
                        "n_imputed": n_imputed, "n_used": len(values),
                        "q1": q1, "median": median, "q3": q3,
                    })
    return pd.DataFrame(rows)


def extreme_observations(views, mask):
    """Apply each view's pooled Tukey fences; report only originally measured values."""
    columns = ("view", "feature", "unit", "row_id", "group", "value",
               "n_reference", "lower_fence", "upper_fence")
    rows = []
    for view, frame in views.items():
        for feature in MEASURES:
            values = frame[feature].dropna()
            q1, q3 = values.quantile([0.25, 0.75])
            lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
            measured = mask.loc[values.index, feature].eq(0)
            outside = (values.lt(lower) | values.gt(upper)) & measured
            for row_id, value in values[outside].items():
                rows.append((view, feature, UNITS[feature], row_id, frame.at[row_id, "class"],
                             value, len(values), lower, upper))
    return pd.DataFrame(rows, columns=columns)


def pairwise_correlations(views):
    rows = []
    for view, frame in views.items():
        for x, y in combinations(MEASURES, 2):
            paired = frame[[x, y]].dropna()
            defined = len(paired) >= 2 and paired[x].nunique() > 1 and paired[y].nunique() > 1
            rows.append({
                "view": view, "feature_x": x, "feature_y": y, "n_pairs": len(paired),
                "pearson": paired[x].corr(paired[y]) if defined else np.nan,
                "spearman": paired[x].corr(paired[y], method="spearman") if defined else np.nan,
            })
    return pd.DataFrame(rows)


def write_cohort_report(views, mask, tables, output_dir):
    measures = list(MEASURES)
    patients = patient_records(views["observed"], mask)
    for view in ("observed", "imputed"):
        by_patient = views[view][measures].to_dict(orient="index")
        for patient in patients:
            patient[view] = by_patient[patient["id"]]

    write_report("cohort", {
        "features": list(FEATURES), "measures": measures,
        "units": {feature: UNITS[feature] for feature in measures},
        "patients": patients,
        "summary": tables["distribution_summary"].to_dict(orient="records"),
        "clinical_strata": tables["clinical_strata"].to_dict(orient="records"),
        "extremes": tables["extreme_observations"].to_dict(orient="records"),
        "correlations": tables["correlations"].to_dict(orient="records"),
        "missing_rates": tables["missing_rates"].to_dict(orient="records"),
    }, output_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--plots", action="store_true", help="Write the offline interactive cohort report.")
    args = parser.parse_args()

    views = {view: load_view(args.processed_dir, view) for view in VIEWS}
    mask = load_view(args.processed_dir, "missing_mask")
    tables = {
        "missing_rates": missing_rates(mask), "group_composition": group_composition(views),
        "distribution_summary": distribution_summary(views, mask),
        "clinical_strata": clinical_strata(views, mask),
        "extreme_observations": extreme_observations(views, mask),
        "correlations": pairwise_correlations(views),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.output_dir / f"{name}.csv", index=False)
    if args.plots:
        write_cohort_report(views, mask, tables, args.output_dir)


if __name__ == "__main__":
    main()

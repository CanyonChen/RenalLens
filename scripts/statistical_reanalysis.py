"""Re-estimate the CKD missing-data contrasts from the original UCI CSV.

One source row is the sampling unit. Uncertainty for the descriptive changes
is conditional on the two observed diagnosis totals; all views in a bootstrap
draw reuse the same patients. Imputed measurements are descriptive only.
"""

import argparse
import hashlib
from pathlib import Path
import platform
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import scipy
from scipy import stats
import sklearn

from data_preprocess import MEASURES, UNITS, load_view, preprocess
from test import (
    GROUPS, VIEWS, clinical_strata, distribution_summary, extreme_observations,
    missing_rates, pairwise_correlations,
)
from train import compare_logs, compare_pca, compare_scales


ROOT = Path(__file__).resolve().parents[1]
GROUP_LABELS = ("all", *GROUPS)
METHODS = ("pearson", "spearman")


def measurement_values(views):
    observed = views["observed"]
    pieces = []
    for feature in MEASURES:
        pieces.append(pd.DataFrame({
            "group": observed["class"],
            "complete_case": observed.index.isin(views["complete_case"].index),
            "feature": feature,
            "observed": observed[feature],
            "imputed": views["imputed"][feature],
        }).reset_index())
    return pd.concat(pieces, ignore_index=True)


def retention_tables(observed, complete):
    rows = []
    for group in GROUPS:
        group_rows = observed["class"].eq(group)
        total = int(group_rows.sum())
        retained = int(complete[group_rows].sum())
        interval = stats.binomtest(retained, total).proportion_ci(method="wilson")
        rows.append({
            "group": group, "n_total": total, "n_complete": retained,
            "retention": retained / total, "ci_low": interval.low, "ci_high": interval.high,
        })
    ckd, other = rows
    difference = ckd["retention"] - other["retention"]
    # Newcombe's hybrid score interval (method 10), using Wilson bounds.
    lower = difference - np.hypot(ckd["retention"] - ckd["ci_low"], other["ci_high"] - other["retention"])
    upper = difference + np.hypot(ckd["ci_high"] - ckd["retention"], other["retention"] - other["ci_low"])
    cells = [[r["n_complete"], r["n_total"] - r["n_complete"]] for r in rows]
    fisher = stats.fisher_exact(cells, alternative="two-sided")
    contrast = {
        "contrast": "ckd_minus_notckd", "delta": difference, "ci_low": lower, "ci_high": upper,
        "ci_method": "Newcombe hybrid score 95%", "sample_odds_ratio": fisher.statistic,
        "fisher_two_sided_p": fisher.pvalue,
    }
    return pd.DataFrame(rows), pd.DataFrame([contrast])


def subgroup(frame, group):
    return frame if group == "all" else frame.loc[frame["class"].eq(group)]


def renal_points(views):
    rows = []
    for view, frame in views.items():
        for group in GROUP_LABELS:
            paired = subgroup(frame, group)[["sc", "bu"]].dropna()
            rows.append({
                "group": group, "view": view, "n_pairs": len(paired),
                **{m: paired.sc.corr(paired.bu, method=m) for m in METHODS},
            })
    return pd.DataFrame(rows)


def row_correlations(x, y):
    """Pearson and average-rank Spearman for each row of paired samples."""
    valid = np.isfinite(x) & np.isfinite(y)
    x = np.where(valid, x, np.nan)
    y = np.where(valid, y, np.nan)

    def pearson(a, b):
        a_centered = a - np.nanmean(a, axis=1, keepdims=True)
        b_centered = b - np.nanmean(b, axis=1, keepdims=True)
        numerator = np.nansum(a_centered * b_centered, axis=1)
        denom = np.sqrt(np.nansum(a_centered**2, axis=1) * np.nansum(b_centered**2, axis=1))
        return np.divide(numerator, denom, out=np.full_like(numerator, np.nan), where=denom > 0)

    rank_x = stats.rankdata(x, axis=1, method="average", nan_policy="omit")
    rank_y = stats.rankdata(y, axis=1, method="average", nan_policy="omit")
    return np.column_stack([pearson(x, y), pearson(rank_x, rank_y)])


def bootstrap_statistics(observed, complete, repetitions, seed):
    """Return bootstrap arrays for the same observed/complete contrasts."""
    rng = np.random.default_rng(seed)
    strata = {g: np.flatnonzero(observed["class"].eq(g).to_numpy(bool)) for g in GROUPS}
    values = observed[list(MEASURES)].to_numpy()
    renal_cols = [MEASURES.index(name) for name in ("sc", "bu")]
    batches = {group: [] for group in GROUP_LABELS}
    for start in range(0, repetitions, 200):
        batch = min(200, repetitions - start)
        draws = {g: rng.choice(ids, size=(batch, len(ids)), replace=True) for g, ids in strata.items()}
        draws["all"] = np.concatenate([draws[g] for g in GROUPS], axis=1)
        for group, ids in draws.items():
            sampled = values[ids]
            kept = np.where(complete[ids, None], sampled, np.nan)
            by_view = []
            for matrix in (sampled, kept):
                medians = np.nanmedian(matrix, axis=1)
                correlations = row_correlations(matrix[:, :, renal_cols[0]], matrix[:, :, renal_cols[1]])
                by_view.append(np.column_stack([medians, correlations]))
            batches[group].append(np.stack(by_view, axis=1))
    # Dimensions: replicate, view (available then complete), statistic.
    return {group: np.concatenate(parts, axis=0) for group, parts in batches.items()}


def interval(values):
    defined = values[np.isfinite(values)]
    if len(defined) == 0:
        return np.nan, np.nan, 0
    lo, hi = np.quantile(defined, [0.025, 0.975])
    return lo, hi, len(defined)


def format_contrasts(distributions, renal, bootstrap):
    distributions = distributions.set_index(["group", "feature", "view"])
    renal = renal.set_index(["group", "view"])
    medians, correlations = [], []
    for group, draws in bootstrap.items():
        shifts = draws[:, 1] - draws[:, 0]
        for j, feature in enumerate(MEASURES):
            observed = distributions.loc[(group, feature, "observed")]
            complete = distributions.loc[(group, feature, "complete_case")]
            lo, hi, valid = interval(shifts[:, j])
            medians.append({
                "group": group, "feature": feature, "unit": UNITS[feature],
                "n_observed": observed["n"], "n_complete": complete["n"],
                "median_observed": observed["median"], "median_complete": complete["median"],
                "delta": complete["median"] - observed["median"], "ci_low": lo, "ci_high": hi,
                "valid_replicates": valid,
            })
        for j, method in enumerate(METHODS, start=len(MEASURES)):
            observed = renal.loc[(group, "observed")]
            complete = renal.loc[(group, "complete_case")]
            lo, hi, valid = interval(shifts[:, j])
            correlations.append({
                "group": group, "method": method, "n_observed": int(observed["n_pairs"]),
                "n_complete": int(complete["n_pairs"]), "observed": observed[method],
                "complete_case": complete[method], "delta": complete[method] - observed[method],
                "ci_low": lo, "ci_high": hi, "valid_replicates": valid,
            })
            for v, view in enumerate(("observed", "complete_case")):
                lo, hi, valid = interval(draws[:, v, j])
                renal.loc[(group, view), f"{method}_ci_low"] = lo
                renal.loc[(group, view), f"{method}_ci_high"] = hi
                renal.loc[(group, view), f"{method}_valid_replicates"] = valid
    return pd.DataFrame(medians), renal.reset_index(), pd.DataFrame(correlations)


def run(source, output, repetitions, seed):
    if repetitions < 2:
        raise ValueError("At least two bootstrap replicates are required.")
    output.mkdir(parents=True, exist_ok=True)
    # Use the same cleaning, units, and PCA code as the original project.
    # Publish finished tables only after preprocessing and estimation succeed.
    with TemporaryDirectory(dir=output.parent) as tmp:
        staging = Path(tmp)
        processed = staging / "processed"
        preprocess(source, processed)
        views = {name: load_view(processed, name) for name in VIEWS}
        observed = views["observed"]
        if observed["class"].isna().any() or set(observed["class"]) != set(GROUPS):
            raise ValueError("The planned two-stratum analysis requires both recorded diagnosis groups.")
        complete = observed.index.isin(views["complete_case"].index)
        mask = load_view(processed, "missing_mask")

        tables = {"measurement_values": measurement_values(views)}
        tables["missingness"] = pd.concat([
            missing_rates(mask.loc[subgroup(observed, group).index]).assign(group=group)
            for group in GROUP_LABELS
        ], ignore_index=True)
        tables["distribution_summary"] = distribution_summary(views, mask)
        tables["clinical_strata"] = clinical_strata(views, mask)
        tables["extreme_observations"] = extreme_observations(views, mask)
        tables["pairwise_correlations"] = pairwise_correlations(views)
        tables["retention"], tables["retention_contrast"] = retention_tables(observed, complete)
        draws = bootstrap_statistics(observed, complete, repetitions, seed)
        tables["median_shifts"], tables["renal_correlations"], tables["renal_correlation_shifts"] = (
            format_contrasts(tables["distribution_summary"], renal_points(views), draws)
        )

        compare_logs(observed, staging)
        matrices = compare_scales(views["imputed"], staging)
        _, tables["pca_variance"], tables["pca_loadings"] = compare_pca(matrices, staging)
        tables["analysis_metadata"] = pd.DataFrame([{
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "n_patients": len(observed), "n_complete": complete.sum(),
            "bootstrap_replicates": repetitions, "seed": seed, "generator": "NumPy default_rng (PCG64)",
            "bootstrap_sampling": "records resampled within diagnosis, fixed stratum sizes, shared row IDs across views",
            "bootstrap_ci": "pointwise 95% percentile (linear quantile), finite replicates",
            "retention_ci": "Wilson score by group; Newcombe hybrid score for CKD minus non-CKD",
            "retention_test": "two-sided Fisher exact; only inferential p-value",
            "imputed_view": "descriptive, full-sample medians/modes, no imputed-data inference",
            "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__, "scikit_learn": sklearn.__version__,
        }])
        for name, frame in tables.items():
            frame.to_csv(staging / f"{name}.csv", index=False)
        for name in [*tables, "log_comparison", "scale_parameters"]:
            (staging / f"{name}.csv").replace(output / f"{name}.csv")
    print(f"Analyzed {len(observed)} patients ({complete.sum()} complete); tables in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/ckd.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reanalysis/tables")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261115)
    options = parser.parse_args()
    run(options.input, options.output_dir, options.bootstrap, options.seed)

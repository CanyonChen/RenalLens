"""Compare diagnostic mixtures and validate simple imputation on held-out readings."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from data_preprocess import MEASURES, UNITS


TABLES = Path(__file__).resolve().parents[1] / "docs" / "reanalysis" / "tables"
GROUPS = ("ckd", "notckd")


def weighted_medians(readings, weights):
    """Weights are integer masses on ascending readings, one row per resample."""
    cumulative = 2 * weights.cumsum(axis=1)
    total = weights.sum(axis=1)
    valid = total > 0
    left = (cumulative[valid] < total[valid, None]).sum(axis=1)
    right = (cumulative[valid] <= total[valid, None]).sum(axis=1)
    result = np.full(len(weights), np.nan)
    result[valid] = (readings[left] + readings[right]) / 2
    return result


def standardized_medians(values, seed, n_boot):
    """Compare empirical medians along one explicit change of cohort and mixture."""
    patients = values[["row_id", "group"]].drop_duplicates().sort_values("row_id")
    if not patients["row_id"].is_unique or not patients["group"].isin(GROUPS).all():
        raise ValueError("Mixture standardization needs one recorded diagnosis per patient.")
    rng = np.random.default_rng(seed)
    patient_weights = np.ones((1 + n_boot, len(patients)), dtype=np.int32)
    for _, group in patients.groupby("group"):
        positions = patients["row_id"].searchsorted(group["row_id"])
        n = len(group)
        patient_weights[1:, positions] = rng.multinomial(n, np.full(n, 1 / n), size=n_boot)

    results = []
    for feature, frame in values.groupby("feature", sort=False):
        measured = frame.dropna(subset=["observed"]).sort_values("observed")
        readings = measured["observed"].to_numpy()
        ckd = measured["group"].eq("ckd").to_numpy()
        observed = patient_weights[:, patients["row_id"].searchsorted(measured["row_id"])]
        complete = observed * measured["complete_case"].to_numpy()
        measured_counts = [observed[:, g].sum(axis=1) for g in (ckd, ~ckd)]
        complete_counts = [complete[:, g].sum(axis=1) for g in (ckd, ~ckd)]
        if min(count[0] for count in complete_counts) == 0:
            raise ValueError(f"{feature}: both groups need complete cases")
        # Within each group weights are proportional to n_measured / n_complete.
        # Cross-multiplying gives integer masses and exact half-mass tie handling.
        weights = np.where(ckd, (measured_counts[0] * complete_counts[1])[:, None],
                           (measured_counts[1] * complete_counts[0])[:, None])
        reweighted = weighted_medians(readings, complete * weights)
        initial = weighted_medians(readings, observed)
        selected = weighted_medians(readings, complete)
        row = {
            "feature": feature, "unit": UNITS[feature], "n_observed": len(measured),
            "n_complete": int(complete[0].sum()), "ckd_share_observed": ckd.mean(),
            "ckd_share_complete": complete_counts[0][0] / complete[0].sum(),
            "median_observed": initial[0], "median_complete": selected[0],
            "valid_bootstrap": np.isfinite(reweighted[1:]).sum(),
        }
        for key, series in (("median_reweighted_complete", reweighted),
                            ("delta_at_observed_mix", reweighted - initial),
                            ("delta_changing_mix", selected - reweighted)):
            row[key] = series[0]
            row[f"{key}_low"], row[f"{key}_high"] = np.nanquantile(series[1:], [0.025, 0.975])
        results.append(row)
    return pd.DataFrame(results)


def validate_imputation(values, seed):
    patients = values[["row_id", "group"]].drop_duplicates().sort_values("row_id")
    if patients["row_id"].duplicated().any() or not patients["group"].isin(GROUPS).all():
        raise ValueError("Each patient must have one recorded CKD or non-CKD group.")
    wide = values.pivot(index="row_id", columns="feature", values="observed").loc[
        patients["row_id"], list(MEASURES)
    ]
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    predictions, fits = [], []
    for fold, (train, test) in enumerate(splitter.split(wide, patients["group"]), start=1):
        training, held_out = wide.iloc[train], wide.iloc[test]
        for feature in MEASURES:
            reference = training[feature].dropna()
            if reference.empty:
                raise ValueError(f"{feature}: fold {fold} has no observed training values")
            fill = reference.median()
            iqr = reference.quantile(0.75) - reference.quantile(0.25)
            truth = held_out[feature].dropna()
            error = fill - truth
            predictions.append(pd.DataFrame({
                "row_id": truth.index, "feature": feature, "error": error,
                "error_training_iqr": error / iqr if iqr > 0 else np.nan,
            }).reset_index(drop=True))
            fits.append({
                "fold": fold, "feature": feature, "n_train_measured": len(reference),
                "n_test_measured": len(truth), "training_median": fill, "training_iqr": iqr,
            })
    errors = pd.concat(predictions, ignore_index=True).merge(patients, validate="many_to_one")
    results = []
    for group in ("all", *GROUPS):
        subset = errors if group == "all" else errors.loc[errors["group"] == group]
        for feature, frame in subset.groupby("feature", sort=False):
            results.append({
                "group": group, "feature": feature, "unit": UNITS[feature], "n": len(frame),
                "median_error": frame["error"].median(), "mae": frame["error"].abs().mean(),
                "median_error_training_iqr": frame["error_training_iqr"].median(),
                "n_iqr_scaled": frame["error_training_iqr"].count(),
            })
    return pd.DataFrame(results), pd.DataFrame(fits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=TABLES)
    parser.add_argument("--seed", type=int, default=20261115)
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()
    if args.bootstrap < 2:
        parser.error("--bootstrap must be at least 2")
    values = pd.read_csv(args.tables_dir / "measurement_values.csv")
    mixture = standardized_medians(values, args.seed, args.bootstrap)
    validation, folds = validate_imputation(values, args.seed)
    for name, frame in (("mixture_standardization", mixture),
                        ("imputation_validation", validation), ("imputation_folds", folds)):
        frame.to_csv(args.tables_dir / f"{name}.csv", index=False)


if __name__ == "__main__":
    main()

"""Four exploratory clinical questions in records carrying the UCI CKD label.

Use observed measurement pairs for each question and redo each analysis in the
subset complete on all 24 explanatory variables. Serum creatinine and glucose
are in mg/dL. Hemoglobin uses the units given by UCI ("gms").
"""

import argparse
import hashlib
from itertools import product
from pathlib import Path
import platform
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
import scipy
from scipy import stats

from data_preprocess import FEATURES, load_view, preprocess


ROOT = Path(__file__).resolve().parents[1]
PATIENT_FIELDS = ("al", "sc", "hemo", "dm", "bgr", "age", "ane")


def bootstrap_spearman(x, y, rng, repetitions):
    """Pointwise percentile interval; pairs resampled together, ties averaged."""
    x, y = np.asarray(x), np.asarray(y)
    rho = stats.spearmanr(x, y).statistic
    estimates = []
    for start in range(0, repetitions, 250):
        ids = rng.integers(len(x), size=(min(250, repetitions - start), len(x)))
        rx = stats.rankdata(x[ids], method="average", axis=1)
        ry = stats.rankdata(y[ids], method="average", axis=1)
        rx -= rx.mean(axis=1, keepdims=True)
        ry -= ry.mean(axis=1, keepdims=True)
        denom = np.sqrt(np.sum(rx**2, axis=1) * np.sum(ry**2, axis=1))
        valid = denom > 0
        estimates.extend((np.sum(rx * ry, axis=1)[valid] / denom[valid]).tolist())
    lo, hi = np.quantile(estimates, [0.025, 0.975])
    return rho, lo, hi, len(estimates)


def albumin_analysis(view, frame, rng, repetitions):
    pairs = frame[["al", "sc"]].dropna()
    by_grade = []
    for grade in range(6):
        stratum = frame.loc[frame.al.eq(grade), "sc"]
        measurements = stratum.dropna()
        q1, median, q3 = measurements.quantile([0.25, 0.5, 0.75])
        by_grade.append({
            "view": view, "grade": grade, "n_grade": len(stratum), "n_pairs": len(measurements),
            "median": median, "q1": q1, "q3": q3, "min": measurements.min(), "max": measurements.max(),
        })
    associations = []
    for name, sample in [("all_grades", pairs), ("exclude_grade_5", pairs.loc[pairs.al.lt(5)])]:
        if name == "all_grades" or len(sample) != len(pairs):
            rho, lo, hi, valid = bootstrap_spearman(sample.al, sample.sc, rng, repetitions)
        associations.append({
            "view": view, "sample": name, "n": len(sample), "rho": rho,
            "ci_low": lo, "ci_high": hi, "valid_replicates": valid,
        })
    return by_grade, associations


def fit_hc3(design, y):
    """OLS with a sandwich covariance and HC3 leverage adjustment."""
    coef, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != design.shape[1] or len(y) <= rank:
        raise ValueError("Hemoglobin regression requires full column rank and positive residual df.")
    bread = np.linalg.inv(design.T @ design)
    leverage = np.sum((design @ bread) * design, axis=1)
    residual = y - design @ coef
    adjusted = design * (residual / (1 - leverage))[:, None]
    cov = bread @ (adjusted.T @ adjusted) @ bread
    df = len(y) - rank
    critical = stats.t.ppf(0.975, df)
    se = np.sqrt(cov[1, 1])
    fit = {
        "n": len(y), "intercept": coef[0], "slope": coef[1], "se_hc3": se,
        "ci_low": coef[1] - critical * se, "ci_high": coef[1] + critical * se,
        "t_hc3": coef[1] / se, "df": df,
        "r_squared": 1 - np.sum(residual**2) / np.sum((y - y.mean())**2),
        "max_leverage": leverage.max(),
    }
    return fit, coef, cov, residual


def hemoglobin_model(sample):
    x = np.log2(sample.sc.to_numpy())
    y = sample.hemo.to_numpy()
    design = np.column_stack([np.ones(len(x)), x])
    fit, coef, cov, residual = fit_hc3(design, y)
    critical = stats.t.ppf(0.975, fit["df"])
    grid = np.linspace(x.min(), x.max(), 101)
    new_design = np.column_stack([np.ones(len(grid)), grid])
    mean = new_design @ coef
    margin = critical * np.sqrt(np.sum((new_design @ cov) * new_design, axis=1))
    prediction = pd.DataFrame({
        "sc": 2**grid, "mean_hemo": mean, "ci_low": mean - margin, "ci_high": mean + margin,
    })
    # Equal-frequency bins make curvature and changing residual spread inspectable.
    details = sample.assign(predicted=design @ coef, residual=residual).groupby(
        pd.qcut(sample.sc, q=4, duplicates="drop"), observed=True
    ).agg(n=("sc", "size"), min_sc=("sc", "min"), max_sc=("sc", "max"),
          mean_hemo=("hemo", "mean"), mean_predicted=("predicted", "mean"),
          mean_residual=("residual", "mean"), sd_residual=("residual", "std")).reset_index(drop=True)
    return fit, prediction, details


def age_sensitivity(view, frame):
    """Compare the two nested slope estimates in identical age-complete records."""
    pairs = frame[["sc", "hemo", "age"]].dropna()
    design = np.column_stack([np.ones(len(pairs)), np.log2(pairs.sc), pairs.age / 10])
    rows = []
    for model, columns in [("crude_same_records", 2), ("age_adjusted", 3)]:
        fit, coef, _, _ = fit_hc3(design[:, :columns], pairs.hemo.to_numpy())
        fit.update(view=view, model=model, age_coef_per_decade=coef[2] if columns == 3 else np.nan)
        rows.append(fit)
    return rows


def anemia_analysis(view, frame, rng, repetitions):
    pairs = frame[["sc", "hemo"]].dropna()
    if pairs.sc.le(0).any():
        raise ValueError("The log2 creatinine model needs strictly positive measured creatinine.")
    max_row = pairs.sc.idxmax()
    results = []
    for label, sample in [("all_pairs", pairs), ("exclude_max_sc", pairs.drop(max_row))]:
        fit, prediction, diagnostic = hemoglobin_model(sample)
        rho, lo, hi, valid = bootstrap_spearman(sample.sc, sample.hemo, rng, repetitions)
        fit.update(
            view=view, sample=label, omitted_row_id=max_row if label == "exclude_max_sc" else None,
            spearman=rho, spearman_ci_low=lo, spearman_ci_high=hi, valid_replicates=valid,
            p_raw=np.nan,
        )
        if label == "all_pairs":
            full_prediction, full_diagnostic = prediction, diagnostic
            if view == "observed":
                # The only reported p-value across the exploratory questions.
                fit["p_raw"] = 2 * stats.t.sf(abs(fit["t_hc3"]), fit["df"])
        results.append(fit)
    return results, full_prediction, full_diagnostic


def glucose_analysis(view, frame):
    rows = []
    for group in ("no", "yes", "unknown"):
        glucose = frame.loc[frame.dm.fillna("unknown").eq(group), "bgr"]
        measured = glucose.dropna()
        total, n = len(glucose), len(measured)
        high = int(measured.ge(200).sum())
        lo = hi = proportion = np.nan
        if n:
            proportion = high / n
            lo, hi = stats.binomtest(high, n).proportion_ci(method="wilson")
        rows.append({
            "view": view, "dm": group, "n_group": total, "n_measured": n,
            "n_missing": total - n, "n_high": high, "proportion": proportion,
            "ci_low": lo, "ci_high": hi, "bound_low": high / total if total else np.nan,
            "bound_high": (high + total - n) / total if total else np.nan,
        })
    no, yes = rows[:2]
    diff = yes["proportion"] - no["proportion"]
    contrast = {
        "view": view, "contrast": "yes_minus_no", "difference": diff,
        "ci_low": diff - np.hypot(yes["proportion"] - yes["ci_low"], no["ci_high"] - no["proportion"]),
        "ci_high": diff + np.hypot(yes["ci_high"] - yes["proportion"], no["proportion"] - no["ci_low"]),
    }
    return rows, contrast


def availability(view, frame):
    rows = []
    for name, x, y in [("albumin_creatinine", "al", "sc"),
                       ("creatinine_hemoglobin", "sc", "hemo"), ("diabetes_glucose", "dm", "bgr")]:
        mx, my = frame[x].isna(), frame[y].isna()
        rows.append({
            "view": view, "question": name, "x": x, "y": y, "n_cohort": len(frame),
            "n_both_measured": (~mx & ~my).sum(), "n_x_missing_only": (mx & ~my).sum(),
            "n_y_missing_only": (~mx & my).sum(), "n_both_missing": (mx & my).sum(),
        })
    return rows


def overlap_analysis(ckd):
    # Nullable integers keep a missing grade, history, or glucose distinct from zero.
    signals = pd.DataFrame({
        "al_positive": ckd.al.ge(1).where(ckd.al.notna()),
        "anemia": ckd.ane.eq("yes").where(ckd.ane.notna()),
        "high_glucose": ckd.bgr.ge(200).where(ckd.bgr.notna()),
    }).astype("Int64")
    complete = signals.dropna()
    n = len(complete)
    combinations = pd.MultiIndex.from_tuples(product((0, 1), repeat=3), names=signals.columns)
    patterns = complete.value_counts(sort=False).reindex(combinations, fill_value=0).rename("n").reset_index()
    patterns["signal_count"] = patterns[list(signals)].sum(axis=1)
    patterns["n_complete_signals"] = n
    patterns["proportion"] = patterns.n / n
    counts = patterns.groupby("signal_count", as_index=False).n.sum()
    counts["n_complete_signals"] = n
    counts["proportion"] = counts.n / n
    # Observed positives determine the minimum. Each unknown could be positive
    # for the maximum; no distribution of the unobserved states is assumed.
    signals["min_signals"] = signals.sum(axis=1, skipna=True)
    signals["max_signals"] = signals.min_signals + signals.iloc[:, :3].isna().sum(axis=1)
    zero_grade = complete.al_positive.eq(0)
    other_signals = complete.anemia.eq(1) | complete.high_glucose.eq(1)
    summary = {
        "n_ckd": len(ckd), "n_complete_signals": n, "n_missing_any": len(ckd) - n,
        "n_missing_grade": signals.al_positive.isna().sum(), "n_missing_anemia": signals.anemia.isna().sum(),
        "n_missing_glucose": signals.high_glucose.isna().sum(),
        "n_at_least_two_complete": complete.sum(axis=1).ge(2).sum(),
        "n_no_albumin_other_complete": (zero_grade & other_signals).sum(),
        "n_grade0_complete": zero_grade.sum(),
        "n_definite_at_least_two": signals.min_signals.ge(2).sum(),
        "n_possible_at_least_two": signals.max_signals.ge(2).sum(),
    }
    return signals, patterns, counts, summary


def run(source, output_dir, repetitions=5000, seed=20261115):
    if repetitions < 2:
        raise ValueError("At least two bootstrap replicates are required.")
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output_dir.parent) as tmp:
        staging = Path(tmp)
        processed = staging / "processed"
        preprocess(source, processed)
        observed = load_view(processed, "observed")
        ckd = observed.loc[observed["class"].eq("ckd")].copy()
        ckd["complete_case"] = ckd[list(FEATURES)].notna().all(axis=1)
        ckd["al"] = pd.to_numeric(ckd["al"]).astype("Int64")
        tables = {name: [] for name in (
            "albumin_grades", "albumin_association", "anemia_association", "anemia_diagnostics",
            "glucose_threshold", "glucose_contrast", "availability", "anemia_age_sensitivity",
        )}
        for view, frame in [("observed", ckd), ("complete_case", ckd[ckd.complete_case])]:
            grades, associations = albumin_analysis(view, frame, rng, repetitions)
            tables["albumin_grades"].extend(grades)
            tables["albumin_association"].extend(associations)
            models, predictions, diagnostic = anemia_analysis(view, frame, rng, repetitions)
            tables["anemia_association"].extend(models)
            tables["anemia_age_sensitivity"].extend(age_sensitivity(view, frame))
            tables["anemia_diagnostics"].extend(diagnostic.assign(view=view).to_dict("records"))
            if view == "observed":
                tables["anemia_fit"] = predictions
            groups, contrast = glucose_analysis(view, frame)
            tables["glucose_threshold"].extend(groups)
            tables["glucose_contrast"].append(contrast)
            tables["availability"].extend(availability(view, frame))
        signals, patterns, counts, summary = overlap_analysis(ckd)
        tables["overlap_patterns"] = patterns
        tables["overlap_counts"] = counts
        tables["overlap_summary"] = [summary]
        tables["patient_measurements"] = ckd[[*PATIENT_FIELDS, "complete_case"]].join(signals).reset_index()
        tables["clinical_metadata"] = [{
            "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "n_input": len(observed), "n_ckd": len(ckd), "n_complete_ckd": ckd.complete_case.sum(),
            "n_duplicate_ckd_rows_all_source_fields": ckd[list(FEATURES)].duplicated().sum(),
            "patient_id": "1-based original row position; no source patient identifier",
            "primary": "measured pairs within CKD, one source record per patient assumed",
            "sensitivity": "all 24 explanatory fields observed within CKD",
            "bootstrap": "ordinary paired-patient percentile CI conditional on available pairs; average ties",
            "bootstrap_repetitions": repetitions, "seed": seed,
            "p_values": "one exploratory two-sided HC3 slope t test on measured pairs; no multiple-testing adjustment",
            "intervals": "pointwise 95%; Wilson for proportions, Newcombe score difference of proportions",
            "glucose_rule": "random glucose at least 200 mg/dL; sensitivity bounds include missing glucose in denominator",
            "overlap_rule": "albumin grade >=1, anemia history yes, random glucose >=200; all eight complete-signal patterns; recordwise lower and upper logical limits in all CKD rows",
            "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scipy": scipy.__version__,
        }]
        for name, rows in tables.items():
            pd.DataFrame(rows).to_csv(staging / f"{name}.csv", index=False)
        for name in tables:
            (staging / f"{name}.csv").replace(output_dir / f"{name}.csv")
    print(f"Four clinical questions: {len(ckd)} CKD records, {ckd.complete_case.sum()} complete; {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/ckd.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reanalysis/clinical_tables")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261115)
    args = parser.parse_args()
    run(args.input, args.output_dir, args.bootstrap, args.seed)

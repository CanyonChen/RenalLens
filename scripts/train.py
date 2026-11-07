"""Compare measurement scales on matched patients and fit descriptive PCA on both scales."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data_preprocess import MEASURES, UNITS, load_view, patient_records, write_report


def compare_logs(observed, output):
    """Compare x and ln(x / one original unit) using available observations only."""
    summary, pairs = [], []
    for feature in MEASURES:
        raw = observed[feature].dropna()
        skew = raw.skew()
        if len(raw) < 3:
            status = "fewer_than_three_observations"
        elif raw.min() <= 0:
            status = "nonpositive_observation"
        elif not skew > 0:
            status = "no_positive_skew"
        else:
            status = "compared"

        log_skew = np.nan
        if status == "compared":
            logged = np.log(raw)
            log_skew = logged.skew()
            pairs.append(pd.DataFrame({"feature": feature, "raw": raw, "ln": logged}).reset_index())
        summary.append({
            "feature": feature, "unit": UNITS[feature], "view": "observed",
            "observed_n": len(raw), "paired_n": len(raw) if status == "compared" else 0,
            "status": status, "raw_skewness": skew, "ln_skewness": log_skew,
        })

    columns = ["row_id", "feature", "raw", "ln"]
    paired = pd.concat(pairs, ignore_index=True) if pairs else pd.DataFrame(columns=columns)
    paired.to_csv(output / "log_pairs.csv", index=False, columns=columns)
    pd.DataFrame(summary).to_csv(output / "log_comparison.csv", index=False)
    return paired


def compare_scales(imputed, output):
    raw = imputed.loc[:, list(MEASURES)]
    scaler = StandardScaler()
    zscore = pd.DataFrame(scaler.fit_transform(raw), columns=raw.columns, index=raw.index)
    pd.DataFrame({
        "feature": raw.columns, "unit": [UNITS[f] for f in raw.columns],
        "view": "imputed", "n": len(raw), "mean": scaler.mean_,
        "sd_ddof0": np.sqrt(scaler.var_), "divisor": scaler.scale_,
    }).to_csv(output / "scale_parameters.csv", index=False)

    matrices = {"raw": raw, "zscore": zscore}
    for scale, frame in matrices.items():
        frame.to_csv(output / f"patient_features_{scale}.csv")
    return matrices


def compare_pca(matrices, output):
    """Loadings are eigenvectors times sqrt(eigenvalue), in the fitted feature units."""
    scores, variance, loadings = [], [], []
    for scale, frame in matrices.items():
        if len(frame) < 2 or (frame.nunique() <= 1).all():
            raise ValueError("PCA needs at least two patients and one varying feature.")
        pca = PCA(svd_solver="full")
        values = pca.fit_transform(frame)
        pcs = [f"PC{i + 1}" for i in range(values.shape[1])]
        scores.append(pd.DataFrame(values, columns=pcs, index=frame.index).assign(scale=scale))
        variance.append(pd.DataFrame({
            "scale": scale, "n": len(frame), "component": pcs,
            "eigenvalue": pca.explained_variance_, "explained_fraction": pca.explained_variance_ratio_,
            "cumulative_fraction": np.cumsum(pca.explained_variance_ratio_),
        }))
        for pc, weights, eigenvalue in zip(pcs, pca.components_, pca.explained_variance_, strict=True):
            loadings.append(pd.DataFrame({
                "scale": scale, "component": pc, "feature": frame.columns,
                "eigenvector_weight": weights, "loading": weights * np.sqrt(eigenvalue),
            }))

    scores = pd.concat(scores).reset_index()
    variance = pd.concat(variance, ignore_index=True)
    loadings = pd.concat(loadings, ignore_index=True)
    scores.to_csv(output / "pca_scores.csv", index=False)
    variance.to_csv(output / "pca_variance.csv", index=False)
    loadings.to_csv(output / "pca_loadings.csv", index=False)
    return scores, variance, loadings


def write_scale_report(observed, mask, matrices, scores, variance, loadings, pairs, output_dir):
    patients = patient_records(observed, mask)
    raw = matrices["raw"].to_dict(orient="index")
    zscores = matrices["zscore"].to_dict(orient="index")
    coordinates = scores.set_index(["row_id", "scale"])[["PC1", "PC2"]]
    for patient in patients:
        row_id = patient["id"]
        patient["raw"] = raw[row_id]
        patient["z"] = zscores[row_id]
        patient["scores"] = {
            scale: coordinates.loc[(row_id, scale), :].tolist() for scale in matrices
        }

    write_report("scales", {
        "measures": list(MEASURES), "units": {f: UNITS[f] for f in MEASURES},
        "patients": patients,
        "variance": variance.to_dict(orient="records"),
        "loadings": loadings.to_dict(orient="records"),
        "log_pairs": pairs.to_dict(orient="records"),
    }, output_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--pca", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--plots", action="store_true", help="Write the offline interactive scale and PCA report.")
    args = parser.parse_args()

    observed = load_view(args.processed_dir, "observed")
    imputed = load_view(args.processed_dir, "imputed")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pairs = compare_logs(observed, args.output_dir)
    matrices = compare_scales(imputed, args.output_dir)
    scores, variance, loadings = compare_pca(matrices, args.output_dir)
    if args.plots:
        mask = load_view(args.processed_dir, "missing_mask")
        write_scale_report(observed, mask, matrices, scores, variance, loadings, pairs, args.output_dir)


if __name__ == "__main__":
    main()

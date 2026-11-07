"""Export the clinical study figures and a creatinine–urea sensitivity analysis."""

import argparse
import base64
import json
import os
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.ticker import MaxNLocator, PercentFormatter
import numpy as np
import pandas as pd

from data_preprocess import MEASURES, load_view


TEAL, RUST, INK = "#176c67", "#a74929", "#1e3537"
VIEWS = {"observed": "Available observations", "complete_case": "Complete cases", "imputed": "Imputed"}
NAMES = {"hemo": "Hb", "sc": "Creatinine", "bu": "Urea", "bgr": "Glucose", "bp": "BP"}
GROUPS = {"ckd": "CKD", "notckd": "Non-CKD", "unknown": "Unlabelled"}


def selection(summary):
    fig, axes = plt.subplots(1, 2, figsize=(10.3, 3), layout="constrained")
    groups = [("all", "All"), ("ckd", "CKD"), ("notckd", "Non-CKD")]
    for ax, (feature, title) in zip(axes, [("sc", "Serum creatinine (mg/dL)"),
                                          ("hemo", "Hemoglobin (UCI: gms)")], strict=True):
        values = summary.loc[summary.feature == feature].set_index(["group", "view"])
        labels = []
        for y, (group, name) in enumerate(groups):
            before = values.loc[(group, "observed")]
            after = values.loc[(group, "complete_case")]
            labels.append(f"{name}   {before.n} → {after.n}")
            if not (np.isfinite(before["median"]) and np.isfinite(after["median"])):
                continue
            a, b = before["median"], after["median"]
            ax.plot([a, b], [y, y], lw=2, color="#92a9a5")
            ax.plot(a, y, marker="o", ms=10, mfc="white", mec=INK, mew=1.5)
            ax.plot(b, y, marker="D", ms=5, color=RUST)
            for val, offset in [(a, 9), (b, -15)]:
                ax.annotate(f"{val:.2f}", (val, y), xytext=(0, offset), textcoords="offset points",
                            ha="center", fontsize=9, color=INK if offset>0 else RUST)
        ax.set_yticks(range(len(groups)), labels)
        ax.set_ylim(len(groups)-.5, -.55)
        ax.margins(x=.16)
        ax.set_xlabel(title)
        ax.xaxis.set_major_locator(MaxNLocator(5))
    return fig


def missingness(observed, mask):
    columns = mask.mean().sort_values(ascending=False, kind="stable").index
    order = observed["class"].fillna("unknown").sort_values(kind="stable")
    data = mask.loc[order.index, columns]
    fig, (ax, rates) = plt.subplots(1, 2, figsize=(10, 5.8), width_ratios=(3.3, 1.2),
                                   layout="constrained", sharey=True)
    ax.imshow(data.T, aspect="auto", interpolation="nearest", cmap=ListedColormap(["#edf2ee", TEAL]),
              vmin=0, vmax=1, extent=(-.5, len(data)-.5, len(columns)-.5, -.5))
    ax.set_yticks(range(len(columns)), columns)
    centers, group_labels = [], []
    start = 0
    for group, count in order.value_counts(sort=False).items():
        centers.append(start + (count-1)/2)
        group_labels.append(f"{GROUPS[group]}  (n = {count})")
        if start:
            ax.axvline(start-.5, color=RUST, lw=1.6)
        start += count
    ax.set_xticks(centers, group_labels)
    ax.set_title("Missing cells by patient", loc="left")
    pct = data.mean() * 100
    bars = rates.barh(range(len(columns)), pct, color=TEAL, height=.65)
    rates.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
    rates.set_xlim(0, max(8, pct.max()*1.32))
    rates.set_xticks([])
    rates.set_title("Missing / all patients", loc="left")
    return fig


def hemoglobin(views):
    fig, (hist, ecdf) = plt.subplots(1, 2, figsize=(10.5, 3.6), layout="constrained")
    series = {v: frame["hemo"].dropna().sort_values() for v, frame in views.items()}
    values = series["observed"]
    bins = np.arange(np.floor(values.min()), np.ceil(values.max()) + .51, .5)
    for (view, data), color, line in zip(series.items(), (TEAL, RUST, INK), ("-", "--", ":"), strict=True):
        if data.empty:
            continue
        label = f"{VIEWS[view]} (n={len(data)})"
        hist.hist(data, bins=bins, weights=np.full(len(data), 100/len(data)), histtype="step",
                  color=color, linestyle=line, lw=1.8, label=label)
        ecdf.ecdf(data, color=color, linestyle=line, lw=1.8)
    ecdf.axvline(values.median(), lw=1, ls="--", color="#657676", alpha=.75)
    hist.legend(loc="upper left", fontsize=8)
    hist.set_ylabel("Share in each 0.5-unit bin")
    ecdf.set_ylabel("Cumulative share")
    hist.yaxis.set_major_formatter(PercentFormatter(100))
    ecdf.yaxis.set_major_formatter(PercentFormatter(1))
    for ax in (hist, ecdf):
        ax.set_xlim(bins[0], bins[-1])
        ax.set_xlabel("Hemoglobin (UCI: gms)")
    return fig


def albumin_grades(strata):
    rows = strata[(strata["view"] == "observed") & (strata["group"] == "ckd") & (strata["context"] == "al")]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8), layout="constrained")
    for ax, (feature, title) in zip(axes, [("sc", "Serum creatinine"), ("bu", "Blood urea")], strict=True):
        panel = rows[rows["feature"] == feature]
        for y, row in enumerate(panel.itertuples()):
            if row.n_used:
                ax.plot([row.q1, row.q3], [y, y], lw=4, color="#99bcb5", solid_capstyle="round")
                ax.plot(row.median, y, marker="D" if row.n_used == 1 else "o", color=TEAL, ms=6)
        labels = ["Unknown" if tag == "unrecorded" else f"Grade {tag}" for tag in panel.level]
        ax.set_yticks(range(len(panel)), [f"{label}   {n}/{total}" for label, n, total in
                                        zip(labels, panel.n_used, panel.n_stratum, strict=True)])
        ax.invert_yaxis()
        ax.set_title(title, loc="left")
        ax.set_xlabel(f"{title} (mg/dL)")
        ax.set_xlim(left=0)
    return fig


def comorbidities(observed):
    cohort = observed.loc[observed["class"] == "ckd"]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), layout="constrained")
    questions = [("hemo", "ane", "Anemia", "Hemoglobin (UCI: gms)"),
                 ("bgr", "dm", "Diabetes", "Random glucose (mg/dL)"),
                 ("bp", "htn", "Hypertension", "Blood pressure (mmHg)")]
    for ax, (feature, context, title, unit) in zip(axes, questions, strict=True):
        groups = [cohort.loc[cohort[context] == level, feature] for level in ("yes", "no")]
        labels = [f"{level}\n{s.count()}/{len(s)}" for level, s in zip(("Yes", "No"), groups, strict=True)]
        ax.boxplot([s.dropna() for s in groups], tick_labels=labels, widths=.53, patch_artist=True,
                   boxprops={"facecolor": "#cee2db", "edgecolor": TEAL},
                   medianprops={"color": INK, "linewidth": 2.1}, whiskerprops={"color": TEAL},
                   capprops={"color": TEAL}, flierprops={"marker": "o", "markersize": 3.5,
                   "markerfacecolor": "white", "markeredgecolor": RUST})
        ax.set_title(f"Recorded {title.lower()}", loc="left")
        ax.set_ylabel(unit)
    return fig


def correlations(table):
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.6), layout="constrained")
    cmap = LinearSegmentedColormap.from_list("association", ["#963d25", "#fbfaf5", "#176963"])
    measure_names = [NAMES[f] for f in MEASURES]
    for ax, (view, title) in zip(axes, VIEWS.items(), strict=True):
        matrix = np.full((len(MEASURES), len(MEASURES)), np.nan)
        for row in table.loc[table.view == view].itertuples():
            x, y = MEASURES.index(row.feature_x), MEASURES.index(row.feature_y)
            matrix[x, y], matrix[y, x] = row.spearman, row.pearson
        ax.imshow(matrix, cmap=cmap, vmin=-1, vmax=1, interpolation="nearest")
        for (i, j), value in np.ndenumerate(matrix):
            if np.isfinite(value):
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=9,
                        color="white" if abs(value) > .64 else INK)
        ax.set_xticks(range(len(MEASURES)), measure_names, rotation=30, ha="right")
        ax.set_yticks(range(len(MEASURES)), measure_names)
        ax.set_title(title, loc="left")
    return fig


def renal_sensitivity(observed):
    pairs = observed[["class", "sc", "bu"]].dropna(subset=["sc", "bu"])
    grouped = list(pairs.groupby(pairs["class"].fillna("unknown"), sort=True))
    samples = [("all", pairs), *grouped]
    omitted = None
    if len(pairs) > 1:
        omitted = pairs["sc"].idxmax()
        samples.append(("all_except_one_max_sc", pairs.drop(index=omitted)))
    rows = []
    for label, subset in samples:
        matrix = subset[["sc", "bu"]]
        rows.append({"sample": label, "n_pairs": len(subset),
                     "omitted_row_id": omitted if label == "all_except_one_max_sc" else None,
                     "pearson": matrix.corr().at["sc", "bu"],
                     "spearman": matrix.corr(method="spearman").at["sc", "bu"]})
    results = pd.DataFrame(rows).astype({"omitted_row_id": "Int64"})
    fig, ax = plt.subplots(figsize=(8.2, 3.8), layout="constrained")
    markers = {"ckd": ("o", TEAL), "notckd": ("^", RUST), "unknown": ("s", INK)}
    for group, frame in grouped:
        marker, color = markers[group]
        ax.scatter(frame.sc, frame.bu, s=20, marker=marker, facecolors="none", edgecolors=color,
                   lw=.85, alpha=.75, label=f"{GROUPS[group]}  n = {len(frame)}")
    if omitted is not None:
        point = pairs.loc[omitted]
        ax.annotate(f"Source row {omitted}", (point.sc, point.bu), xytext=(-8, 14),
                    textcoords="offset points", ha="right", color=INK,
                    arrowprops={"arrowstyle": "-", "color": INK})
    ax.set(xlabel="Serum creatinine (mg/dL)", ylabel="Blood urea (mg/dL)")
    ax.legend()
    return fig, results


def pc1(loadings, variance):
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.2), layout="constrained", sharey=True)
    for ax, (scale, label) in zip(axes, [("raw", "Original units"), ("zscore", "Standardized")], strict=True):
        rows = loadings.loc[(loadings.scale == scale) & (loadings.component == "PC1")].set_index("feature")
        v = rows.loc[list(MEASURES), "eigenvector_weight"]
        fraction = variance.loc[(variance.scale == scale) & (variance.component == "PC1"), "explained_fraction"].item()
        ax.axvline(0, color="#758b86", lw=1)
        bars = ax.barh(range(len(v)), v, color=[TEAL if w >= 0 else RUST for w in v], height=.55)
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)
        ax.set_yticks(range(len(v)), [NAMES[f] for f in MEASURES])
        ax.set(xlim=(-1.18, 1.22), xlabel="PC1 direction coefficient")
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.set_title(f"{label}  ·  PC1 explains {fraction:.1%}", loc="left")
    axes[0].invert_yaxis()
    return fig


def export_report(processed_dir, figure_dir, target):
    """Publish the authored UCI case study with its eight figures embedded."""
    template = Path(__file__).resolve().parents[1] / "docs" / "clinical_report.src.html"
    page = template.read_text(encoding="utf-8")
    audit = json.loads((processed_dir / "preprocessing_audit.json").read_text(encoding="utf-8"))
    if f'<code>{audit["input_sha256"]}</code>' not in page:
        raise ValueError("This report interprets a specific UCI dataset. Its source checksum differs from this run.")

    def embed(match):
        name = match.group(1)
        encoded = base64.b64encode((figure_dir / name).read_bytes()).decode("ascii")
        return f'data-filename="{name}" src="data:image/svg+xml;base64,{encoded}"'

    page = re.sub(r'src="results/figures/clinical/([\w-]+\.svg)"', embed, page)
    page = page.replace('<link rel="stylesheet" href="kit.css" data-ve-kit>', "")
    for name in ["cohort.html", "scales.html"]:
        companion = figure_dir.parent / name
        path = Path(os.path.relpath(companion.resolve(), target.parent.resolve())).as_posix()
        page = page.replace(f'href="results/figures/{name}"', f'href="{path}"')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--report", type=Path, help="Also export the standalone report for the audited UCI input.")
    args = parser.parse_args()
    dest = args.output_dir / "figures" / "clinical"
    dest.mkdir(exist_ok=True, parents=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK, "axes.edgecolor": "#abbdb7", "axes.titleweight": "bold",
                         "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                         "xtick.color": INK, "ytick.color": INK, "svg.fonttype": "none",
                         "svg.hashsalt": "renallens-clinical"})
    views = {key: load_view(args.processed_dir, key) for key in VIEWS}
    observed = views["observed"]
    scatter, sensitivity = renal_sensitivity(observed)
    sensitivity.to_csv(args.output_dir / "renal_sensitivity.csv", index=False)
    figures = {
        "selection": selection(pd.read_csv(args.output_dir / "distribution_summary.csv")),
        "missingness": missingness(observed, load_view(args.processed_dir, "missing_mask")),
        "hemoglobin_distribution": hemoglobin(views),
        "albumin_grades": albumin_grades(pd.read_csv(args.output_dir / "clinical_strata.csv", dtype={"level": "string"})),
        "comorbidities": comorbidities(observed),
        "correlations": correlations(pd.read_csv(args.output_dir / "correlations.csv")),
        "creatinine_urea": scatter,
        "pc1_weights": pc1(pd.read_csv(args.output_dir / "pca_loadings.csv"),
                           pd.read_csv(args.output_dir / "pca_variance.csv")),
    }
    for name, fig in figures.items():
        fig.savefig(dest / f"{name}.svg", metadata={"Date": None})
        plt.close(fig)
    if args.report:
        export_report(args.processed_dir, dest, args.report)


if __name__ == "__main__":
    main()

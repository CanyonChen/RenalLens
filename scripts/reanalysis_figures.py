"""Render the RenalLens reanalysis figures from the newly computed statistical tables."""

import argparse
import json
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INK = "#182B35"
MUTED = "#405460"
BLUE = "#186385"
RUST = "#A8431F"
TEAL = "#007264"
GRID = "#D5DCE0"
DPI = 360
FEATURES = {
    "hemo": ("Hemoglobin", "g, UCI"),
    "sc": ("Serum creatinine", "mg/dL"),
    "bu": ("Blood urea", "mg/dL"),
    "bgr": ("Random blood glucose", "mg/dL"),
    "bp": ("Blood pressure", "mmHg"),
}
GROUPS = {"all": "All patients", "ckd": "CKD", "notckd": "Non-CKD"}
VIEW_STYLE = {
    "observed": ("Available measurements", INK, "-"),
    "complete_case": ("Complete cases", RUST, (0, (5, 2))),
    "imputed": ("Median-imputed", TEAL, (0, (1, 1.7))),
}
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 9.5, "svg.fonttype": "none",
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.labelsize": 9.5, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False, "legend.fontsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 9, "axes.axisbelow": True,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "svg.hashsalt": "RenalLens-reanalysis",
}


def heading(fig, title, subtitle):
    fig.text(.025, .968, title, va="top", fontsize=18, weight="bold")
    fig.text(.025, .887, subtitle, va="top", fontsize=10.5, color=MUTED)


def panel(ax, title, grid="x"):
    ax.set_title(title, loc="left", pad=10)
    ax.grid(axis=grid, color=GRID, linewidth=.65)
    ax.tick_params(length=3)


def interval(ax, x, low, high, y, color=INK, marker="o"):
    ax.hlines(y, low, high, color=color, lw=2.2, zorder=2)
    ax.plot([low, high], [y, y], linestyle="none", marker="|", ms=7, color=color)
    ax.plot(x, y, marker=marker, color=color, ms=6.5, zorder=3)


def note(title, alt, caption, tables):
    return {"title": title, "alt": alt, "caption": caption,
            "sources": [f"../tables/{table}.csv" for table in tables]}


def retention(tables):
    retain = pd.read_csv(tables / "retention.csv").set_index("group")
    shifts = pd.read_csv(tables / "median_shifts.csv").query("feature == 'sc'").set_index("group")
    mix = pd.read_csv(tables / "mixture_standardization.csv").set_index("feature").loc["sc"]
    fig = plt.figure(figsize=(10.0, 5.0))
    title = "Complete-case selection changes the diagnosis mix"
    heading(fig, title, "A complete record has all 24 explanatory variables observed.")
    gs = fig.add_gridspec(1, 2, left=.102, right=.966, bottom=.31, top=.71,
                          wspace=.70, width_ratios=[1, 1.22])
    ax = fig.add_subplot(gs[0])
    panel(ax, "A   Patients retained")
    for y, group in zip([1, 0], ["ckd", "notckd"], strict=True):
        r = retain.loc[group]
        interval(ax, r.retention, r.ci_low, r.ci_high, y, BLUE)
        ax.annotate(f"{r.retention:.1%}   ({int(r.n_complete)}/{int(r.n_total)})",
                    (r.retention, y), xytext=(0, 12), textcoords="offset points", ha="center",
                    fontsize=8.5)
    ax.set(xlim=(0, 1), ylim=(-.52, 1.60), yticks=[1, 0], yticklabels=["CKD", "Non-CKD"],
           xlabel="Retained within diagnosis (95% Wilson CI)")
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xticks([0, .25, .5, .75, 1])
    ax = fig.add_subplot(gs[1])
    panel(ax, "B   Shift in median creatinine")
    row_labels = []
    for y, group in zip([2, 1, 0], GROUPS, strict=True):
        r = shifts.loc[group]
        row_labels.append(f"{GROUPS[group]}\n{r.median_observed:.2f} → {r.median_complete:.2f}")
        interval(ax, r.delta, r.ci_low, r.ci_high, y, RUST, marker="D")
    ax.axvline(0, color=MUTED, ls="--", lw=1)
    ax.set(yticks=[2, 1, 0], yticklabels=row_labels, ylim=(-.5, 2.5),
           xlabel="Complete − available median (mg/dL; 95% CI)")
    fig.text(.025, .142, "Pooled creatinine medians (mg/dL)", fontsize=10, weight="bold")
    fig.text(.025, .083, f"Available  {mix.median_observed:.2f}     ·     Complete  "
             f"{mix.median_complete:.2f}     ·     Complete, reweighted to the available diagnosis mix  "
             f"{mix.median_reweighted_complete:.2f}", fontsize=9.5)
    caption = ("A shows complete records divided by all records in each diagnosis and Wilson 95% "
               "intervals. B compares the complete-case median with the median among patients with "
               "a creatinine measurement. Bars are pointwise 95% percentile intervals from a "
               "patient bootstrap stratified by diagnosis, using the same draws for both views. "
               "The three pooled medians examine how much the diagnosis mix alone changes the result.")
    alt = (f"Complete records were retained in {retain.loc['ckd','retention']:.1%} of CKD and "
           f"{retain.loc['notckd','retention']:.1%} of non-CKD patients. Median creatinine changed "
           f"by {shifts.loc['all','delta']:+.2f} mg/dL overall and {shifts.loc['ckd','delta']:+.2f} "
           f"within CKD. The reweighted complete-case median was {mix.median_reweighted_complete:.2f} mg/dL.")
    return fig, note(title, alt, caption, ["retention", "median_shifts", "mixture_standardization"])


def distributions(tables):
    values = pd.read_csv(tables / "measurement_values.csv")
    fig = plt.figure(figsize=(10.0, 6.7))
    title = "Five clinical measurements across three data views"
    fig.text(.025, .975, title, fontsize=18, weight="bold", va="top")
    fig.text(.025, .921, "Each step counts the share at or below a measured value. Steeper jumps mean more patients share that value.",
             fontsize=10.1, color=MUTED, va="top")
    gs = fig.add_gridspec(2, 3, left=.081, right=.978, bottom=.10, top=.795, hspace=.67, wspace=.30)
    for i, (feature, (label, unit)) in enumerate(FEATURES.items()):
        frame = values[values.feature == feature]
        series = {"observed": frame.observed.dropna(), "complete_case": frame.loc[frame.complete_case, "observed"],
                  "imputed": frame.imputed}
        ax = fig.add_subplot(gs[i // 3, i % 3])
        panel(ax, f"{'ABCDE'[i]}   {label}", grid="y")
        for key, numbers in series.items():
            label_view, color, ls = VIEW_STYLE[key]
            unique, counts = np.unique(numbers, return_counts=True)
            # Duplicating the first coordinate preserves the jump at the minimum.
            ax.step(np.r_[unique[0], unique], np.r_[0, counts.cumsum() / len(numbers)], where="post",
                    color=color, ls=ls, lw=1.7 if key != "observed" else 2.25, label=label_view)
        ax.text(.985, .055, "n = " + " / ".join(str(len(v)) for v in series.values()),
                transform=ax.transAxes, ha="right", va="bottom", fontsize=7.9, color=MUTED,
                bbox={"fc":"white", "ec":"none", "pad":1})
        ax.set(ylim=(-.015, 1.03), yticks=[0, .5, 1], xlabel=unit)
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        if i % 3 == 0:
            ax.set_ylabel("Cumulative share")
        if feature in ("sc", "bu"):
            ticks = [.5, 1, 3, 10, 30, 75] if feature == "sc" else [2, 5, 10, 30, 100, 300]
            ax.set_xscale("log", base=10)
            ax.set_xticks(ticks, [str(x) for x in ticks])
            ax.set_xlabel(f"{unit} · log₁₀ axis")
    key = fig.add_subplot(gs[1, 2])
    key.set_axis_off()
    key.text(.01, .99, "Reading the curves", fontsize=11, weight="bold", va="top", transform=key.transAxes)
    for j, (label, color, ls) in enumerate(VIEW_STYLE.values()):
        y = .77 - j * .135
        key.plot([.015, .17], [y, y], transform=key.transAxes, color=color, ls=ls, lw=2.3)
        key.text(.21, y, label, transform=key.transAxes, va="center", fontsize=9)
    hemo = values[values.feature == "hemo"]
    m = hemo.observed.isna().sum()
    key.text(.01, .30, f"Hemoglobin: {m} missing values\nwere set to the observed median\n"
             f"({hemo.observed.median():.2f} in UCI units).", transform=key.transAxes, fontsize=9,
             va="top", color=MUTED, linespacing=1.45)
    caption = ("Each panel plots a right-continuous empirical cumulative distribution in the three views, "
               "using all observed values in that view as its denominator. Counts follow legend order. "
               "Creatinine and blood urea use base-10 axes with native-unit labels; all values were "
               "positive and the full ranges are shown. Hemoglobin uses the UCI source unit, recorded as g.")
    alt = (f"Five empirical distribution plots compare available, complete and imputed measurements. "
           f"Hemoglobin has a visible imputation step because {m} missing values receive "
           f"{hemo.observed.median():.2f}. Creatinine and blood urea show long right tails.")
    return fig, note(title, alt, caption, ["measurement_values", "distribution_summary"])


def renal_association(tables):
    values = pd.read_csv(tables / "measurement_values.csv")
    pairs = values[values.feature.isin(["sc", "bu"])].pivot(index=["row_id", "group"],
        columns="feature", values="observed").dropna().reset_index()
    corr = pd.read_csv(tables / "renal_correlations.csv").query("group == 'all'").set_index("view")
    shifts = pd.read_csv(tables / "renal_correlation_shifts.csv").query("group == 'all'").set_index("method")
    fig = plt.figure(figsize=(10, 5.5))
    title = "Creatinine and urea under different missing-data rules"
    heading(fig, title, "Coefficients use the original units. Lines show patient-level 95% bootstrap intervals where estimated.")
    gs = fig.add_gridspec(2, 2, left=.091, right=.974, bottom=.14, top=.733,
                          width_ratios=[1.22, 1], height_ratios=[1.25, 1], wspace=.60, hspace=1.02)
    ax = fig.add_subplot(gs[:, 0])
    panel(ax, f"A   All {len(pairs)} observed pairs", grid="both")
    for group, color, marker in [("ckd", BLUE, "o"), ("notckd", RUST, "^")]:
        s = pairs[pairs.group == group]
        ax.scatter(s.sc, s.bu, s=19, marker=marker, linewidths=.8,
                   facecolors="none", edgecolors=color, label=f"{GROUPS[group]}  ({len(s)})")
    ax.set(xscale="log", yscale="log", xlabel="Serum creatinine (mg/dL, log₁₀)",
           ylabel="Blood urea (mg/dL, log₁₀)")
    ax.set_xticks([.5, 1, 3, 10, 30, 75], ["0.5", "1", "3", "10", "30", "75"])
    ax.set_yticks([2, 5, 10, 30, 100, 300], ["2", "5", "10", "30", "100", "300"])
    ax.legend(loc="lower right", borderpad=.25, handletextpad=.2)
    high_sc = pairs.loc[pairs.sc.idxmax()]
    ax.annotate(f"row {int(high_sc.row_id)}", (high_sc.sc, high_sc.bu), xytext=(-6, -13),
                textcoords="offset points", fontsize=8, ha="right", color=INK)
    ax = fig.add_subplot(gs[0, 1])
    panel(ax, "B   Correlation across views")
    codes = ["observed", "complete_case", "imputed"]
    for i, (method, color, marker) in enumerate([("pearson", INK, "o"), ("spearman", TEAL, "D")]):
        ys = np.array([2, 1, 0]) + (.135 if i == 0 else -.135)
        for y, view in zip(ys[:2], codes[:2], strict=True):
            r = corr.loc[view]
            ax.hlines(y, r[f"{method}_ci_low"], r[f"{method}_ci_high"], color=color, lw=1.6)
        ax.scatter(corr.loc[codes, method], ys, color=color, marker=marker, s=33,
                   label="Pearson r" if i == 0 else "Spearman ρ")
    ax.set(ylim=(-.45, 2.45), xlim=(0, 1.04), yticks=[2, 1, 0], xticks=[0, .25, .5, .75, 1],
           yticklabels=[f"{v}  ({int(corr.loc[k, 'n_pairs'])})"
                        for v, k in zip(["Available", "Complete", "Imputed"], codes, strict=True)])
    ax.legend(loc="upper left", bbox_to_anchor=(0, -.24), borderaxespad=0, ncol=2,
              handletextpad=.2, columnspacing=1.0, fontsize=8.4)
    ax = fig.add_subplot(gs[1, 1])
    panel(ax, "C   Change after deletion")
    for i, (method, color, marker) in enumerate([("pearson", INK, "o"), ("spearman", TEAL, "D")]):
        s = shifts.loc[method]
        interval(ax, s.delta, s.ci_low, s.ci_high, 1-i, color, marker)
    ax.axvline(0, color=MUTED, ls="--", lw=1)
    ax.set(ylim=(-.55, 1.55), yticks=[1, 0], yticklabels=["Pearson r", "Spearman ρ"],
           xlabel="Complete − available (95% bootstrap CI)")
    caption = ("A shows every jointly observed pair with no jitter or exclusions. Axes use base-10 "
               "scales and native-unit tick labels; coincident records can overlap. B displays native-unit "
               "coefficients with pointwise bootstrap 95% intervals for observed and complete pairs. "
               "The single-imputed estimates are descriptive, with no uncertainty bars. "
               "C shows pointwise 95% percentile intervals "
               "for complete-minus-available changes, resampling patients within diagnosis and "
               "applying both rules to each bootstrap draw.")
    alt = (f"{len(pairs)} paired measurements show a long upper tail, including row "
           f"{int(high_sc.row_id)} at creatinine {high_sc.sc:g} and urea {high_sc.bu:g} mg/dL. "
           f"After complete-case selection, Pearson r changes by {shifts.loc['pearson','delta']:+.2f} "
           f"and Spearman rho by {shifts.loc['spearman','delta']:+.2f}.")
    return fig, note(title, alt, caption, ["measurement_values", "renal_correlations", "renal_correlation_shifts"])


def pca(tables):
    load = pd.read_csv(tables / "pca_loadings.csv").query("component == 'PC1'")
    var = pd.read_csv(tables / "pca_variance.csv").set_index(["scale", "component"])
    n = int(var.loc[("raw", "PC1"), "n"])
    fig = plt.figure(figsize=(10, 4.6))
    title = "Standardization changes the first principal component"
    heading(fig, title, f"Both fits use the same {n} median-imputed records and the same five measurements.")
    gs = fig.add_gridspec(1, 2, left=.18, right=.973, bottom=.215, top=.70, wspace=.46,
                          width_ratios=[1.17, 1])
    a, b = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    panel(a, "A   Signed PC1 coefficients")
    panel(b, "B   Variance per component", grid="y")
    weights = load.pivot(index="feature", columns="scale", values="eigenvector_weight").loc[list(FEATURES)]
    scales = [("raw", "Original units", RUST, "o", "-"), ("zscore", "Standardized", TEAL, "D", "--")]
    locations = np.arange(len(weights))[::-1]
    for i, (scale, name, color, marker, style) in enumerate(scales):
        y = locations + (.10 if i == 0 else -.10)
        a.scatter(weights[scale], y, marker=marker, color=color, s=37)
        variance = var.loc[scale]
        b.plot(np.arange(1, len(variance)+1), variance.explained_fraction, label=name,
               marker=marker, color=color, ls=style, lw=1.8, ms=5)
        b.annotate(f"{variance.iloc[0].explained_fraction:.1%}", (1, variance.iloc[0].explained_fraction),
                   xytext=(7, 1), textcoords="offset points", fontsize=8.5, color=color)
    a.axvline(0, color=MUTED, ls="--", lw=1)
    a.set(yticks=locations, yticklabels=[v[0] for v in FEATURES.values()], ylim=(-.55, 4.55),
          xlim=(-1.07, 1.07), xticks=[-1, -.5, 0, .5, 1], xlabel="Eigenvector coefficient")
    b.set(xlim=(.85, 5.13), xticks=np.arange(1, 6), xlabel="Principal component", ylim=(0, .82))
    b.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    b.legend(loc="upper right", handlelength=2.4)
    fig.text(.025, .052, "Standardization divides each centered measurement by its standard deviation. "
             "The sign of a whole PCA axis can be reversed.", color=MUTED, fontsize=9)
    caption = ("A shows signed unit-length PC1 eigenvector coordinates (a whole eigenvector can "
               "be sign-flipped). B gives the fraction of within-fit variance explained by each "
               "component. Both fits center their five columns. Standardization additionally "
               "divides by the population standard deviation (ddof=0).")
    alt = (f"PC1 explains {var.loc[('raw','PC1'),'explained_fraction']:.1%} of variance in original "
           f"units and {var.loc[('zscore','PC1'),'explained_fraction']:.1%} after standardization. "
           "Random blood glucose dominates the original-unit axis; urea, hemoglobin and creatinine "
           "have the largest absolute standardized coefficients.")
    return fig, note(title, alt, caption, ["pca_variance", "pca_loadings"])


def imputation_validation(tables):
    df = pd.read_csv(tables / "imputation_validation.csv").set_index(["feature", "group"])
    fig = plt.figure(figsize=(10, 5.1))
    title = "How far does a median fill miss a held-out value?"
    heading(fig, title, "Each observed value was withheld once. Predictions use the pooled training-fold median.")
    gs = fig.add_gridspec(1, 2, left=.19, right=.975, bottom=.245, top=.70, wspace=.30,
                          width_ratios=[1.12, 1.0])
    ax = fig.add_subplot(gs[0])
    panel(ax, "A   Direction of error")
    y = np.arange(len(FEATURES))[::-1]
    groups = [("ckd", BLUE, "o"), ("notckd", RUST, "^")]
    for i, (group, color, marker) in enumerate(groups):
        sub = df.xs(group, level="group").loc[list(FEATURES)]
        ax.scatter(sub.median_error_training_iqr, y + (.095 if i == 0 else -.095),
                   color=color, s=41, marker=marker, label=GROUPS[group])
    ax.axvline(0, color=MUTED, lw=1.1, ls="--")
    ax.set(yticks=y, yticklabels=[v[0] for v in FEATURES.values()], ylim=(-.55, 4.55),
           xlabel="Median signed error (training IQRs)")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.28), ncol=2, columnspacing=1,
              borderaxespad=0, handletextpad=.25)
    b = fig.add_subplot(gs[1])
    b.set_title("B   Mean absolute error", loc="left", pad=10)
    b.set(xlim=(0, 1), ylim=(-.55, 4.55))
    b.set_axis_off()
    for pos, item in [(0, "Unit"), (.50, "CKD"), (.98, "Non-CKD")]:
        b.text(pos, 4.48, item, ha="left" if pos == 0 else "right", fontsize=9, weight="bold")
    for pos, (feature, (_, unit)) in zip(y, FEATURES.items(), strict=True):
        b.axhline(pos-.42, lw=.65, color=GRID)
        b.text(0, pos, unit, va="center", fontsize=9, color=MUTED)
        for x, group in [(.50, "ckd"), (.98, "notckd")]:
            b.text(x, pos, f"{df.loc[(feature, group),'mae']:.2f}", ha="right", va="center")
    fig.text(.025, .038, "Negative signed errors indicate underestimation. Error for truly missing records remains unknown.",
             fontsize=9, color=MUTED)
    caption = ("Five-fold validation masks observed entries. A uses the held-out prediction minus "
               "the measured value, divided by the training interquartile range in that fold, then "
               "takes the diagnosis-specific median. B gives mean absolute error in original units. "
               "The plotted point estimates describe measured records. Missing records have no observed "
               "target for validating their imputed value.")
    alt = ("Five rows contrast diagnosis-specific signed validation errors on a common training-IQR "
           "scale and mean absolute errors in original units. For creatinine, the median standardized "
           f"signed error is {df.loc[('sc','ckd'),'median_error_training_iqr']:+.2f} in CKD and "
           f"{df.loc[('sc','notckd'),'median_error_training_iqr']:+.2f} in non-CKD.")
    return fig, note(title, alt, caption, ["imputation_validation"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "docs/reanalysis/tables")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reanalysis/figures")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    notes = {}
    with mpl.rc_context(STYLE):
        for make_figure in (retention, distributions, renal_association, pca, imputation_validation):
            name = make_figure.__name__
            fig, info = make_figure(args.tables_dir)
            width, height = fig.get_size_inches() * 25.4
            info.update(width_mm=round(width, 2), height_mm=round(height, 2), dpi=DPI)
            # Plain SVG text stays editable; the opaque canvas preserves contrast in both exports.
            for ext in ("svg", "png"):
                metadata = {"Title": info["title"], "Description": info["alt"]}
                if ext == "svg":
                    metadata["Date"] = None
                fig.savefig(args.output_dir / f"{name}.{ext}", dpi=DPI, transparent=False, metadata=metadata)
            plt.close(fig)
            notes[name] = info
    (args.output_dir / "figure_notes.json").write_text(
        json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""Export the poster figures from the published RenalLens result tables.

Run from any directory with the project's Python environment. Each original record
has a one-based row_id. Complete cases have all 24 explanatory fields observed.
No random placement or sampling is used.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "reanalysis" / "tables"
CLINICAL = HERE.parent / "reanalysis" / "clinical_tables"
PATIENTS = CLINICAL / "patient_measurements.csv"
FIGURES = HERE / "figures"
INK = "#26232C"
BURGUNDY = "#8B1949"
TEAL = "#00675F"
GRAY = "#665F69"
LIGHT = "#E1DDE1"
GLUCOSE_ORANGE = "#984607"
DATA_VIEWS = (
    ("observed", "Measured", INK, "o"),
    ("complete_case", "Complete case", BURGUNDY, "s"),
    ("imputed", "Single imputation", TEAL, "D"),
)


def save(fig, filename, description):
    fig.savefig(FIGURES / filename, facecolor=fig.get_facecolor(),
                metadata={"Creator": "RenalLens", "Subject": description, "CreationDate": None})
    plt.close(fig)


def measured_grade_zero(patients):
    grade = patients.loc[patients.al.eq(0)].dropna(subset=["anemia", "high_glucose"])
    return grade.assign(finding=grade.anemia.eq(1) | grade.high_glucose.eq(1))


def flow_box(ax, x, y, width, height, edge):
    ax.add_patch(FancyBboxPatch(
        (x, y), width, height, boxstyle="round,pad=0,rounding_size=0.07",
        facecolor="white", edgecolor=edge, linewidth=1.25))


def flow_arrow(ax, start, end):
    ax.annotate("", xy=end, xytext=start,
                arrowprops={"arrowstyle": "-|>", "color": GRAY, "lw": 1.55,
                            "mutation_scale": 14, "shrinkA": 0, "shrinkB": 0})


def missing_data_paths():
    """Follow the same source records through three missing-data rules."""
    values = pd.read_csv(TABLES / "measurement_values.csv")
    glucose = values.loc[values.feature.eq("bgr")].set_index("row_id")
    ckd = glucose.loc[glucose.group.eq("ckd")]
    complete = glucose.loc[glucose.complete_case]
    n_complete_ckd = complete.group.eq("ckd").sum()
    case = glucose.loc[43]

    # Use the same view colors as the hemoglobin figure. Every path also has
    # a method name and an explicit patient disposition for monochrome prints.
    paths = [
        ("Available case", INK, "Use the measured fields\neach question needs.",
         f"Glucose measured in\n{ckd.observed.count()}/{len(ckd)} CKD records",
         "Record 43 retained", f"{case.observed:.0f} mg/dL measured"),
        ("Complete case", BURGUNDY, "Require all 24 fields\nto be present.",
         f"{len(complete)} retained\n{n_complete_ckd} CKD + {len(complete) - n_complete_ckd} non-CKD",
         "Record 43 excluded", f"{case.observed:.0f} mg/dL omitted"),
        ("Single imputation", TEAL, "Pooled median for numbers,\npooled mode for categories.",
         f"{len(glucose)} retained\n{len(ckd)} CKD + {len(glucose) - len(ckd)} non-CKD",
         "Record 43 retained", f"{case.imputed:.0f} mg/dL measured"),
    ]
    pink = "#F6E5EA"  # Gemini alert-block background
    fig = plt.figure(figsize=(14, 5.0), facecolor=pink)
    ax = fig.add_axes((0, 0, 1, 1), xlim=(0, 14), ylim=(0, 5.0))
    ax.axis("off")

    centers = (2.37, 7, 11.63)
    flow_box(ax, 4.14, 4.18, 5.72, .75, BURGUNDY)
    ax.text(7, 4.68, f"{len(glucose)} UCI patient records", ha="center", va="center",
            fontsize=23, weight="bold", color=INK)
    ax.text(7, 4.33, f"{len(ckd)} CKD + {len(glucose) - len(ckd)} non-CKD",
            ha="center", va="center", fontsize=18, color=INK)
    ax.plot([7, 7], [4.18, 3.96], color=GRAY, lw=1.6)
    ax.plot([centers[0], centers[-1]], [3.96, 3.96], color=GRAY, lw=1.6)

    for x, (method, color, rule, sample, disposition, reading) in zip(centers, paths, strict=True):
        flow_box(ax, x - 2.23, 1.55, 4.46, 2.16, color)
        flow_arrow(ax, (x, 3.96), (x, 3.72))
        ax.text(x, 3.39, method, ha="center", va="center", fontsize=22,
                weight="bold", color=color)
        ax.text(x, 2.79, rule, ha="center", va="center", fontsize=18, linespacing=1.15, color=INK)
        ax.text(x, 1.99, sample, ha="center", va="center", fontsize=16.3, color=INK,
                linespacing=1.16)
        flow_arrow(ax, (x, 1.55), (x, 1.27))
        flow_box(ax, x - 2.23, .12, 4.46, 1.14, color)
        ax.text(x, .89, disposition, ha="center", va="center", fontsize=20,
                weight="bold", color=color)
        ax.text(x, .45, reading, ha="center", va="center", fontsize=18, color=INK)

    save(fig, "missing_data_paths.pdf",
         "Three missing-data rules applied to the same 400 records, followed by their "
         "consequences for Record 43's measured glucose of 204 mg/dL.")


def cohort():
    rates = pd.read_csv(TABLES / "missingness.csv")
    top = rates.loc[rates.group.eq("all")].nlargest(5, "n_missing")
    labels = {"rbc": "Red cell assessment", "rbcc": "Red cell count",
              "wbcc": "White cell count", "pot": "Potassium", "sod": "Sodium"}
    eligibility = pd.read_csv(TABLES / "eligibility_rules.csv").set_index(["rule", "group"])
    shifts = pd.read_csv(TABLES / "median_shifts.csv").query("feature == 'sc'").set_index("group")
    fig, (fields, mix, medians) = plt.subplots(
        1, 3, figsize=(15.2, 6.25), layout="constrained",
        gridspec_kw={"width_ratios": [1.20, 1.28, 1.03], "wspace": .045})
    fields.set_title("Most often missing", loc="left")
    y = np.arange(len(top))
    counts = top.n_missing.to_numpy()
    fields.barh(y, counts, .56, color=GRAY)
    for pos, row in enumerate(top.itertuples()):
        fields.text(row.n_missing + 4, pos, f"{row.n_missing}  ({row.missing_rate:.1%})",
                    va="center", fontsize=12)
    fields.set(yticks=y, yticklabels=[labels[f] for f in top.feature], xticks=[0, 50, 100, 150],
               xlim=(0, 245), xlabel="Missing records (of 400)")
    fields.invert_yaxis()

    mix.set_title("Eligibility changes the cohort", loc="left")
    strategies = [(None, "All records"), ("core5", "5 markers"), ("all24", "24 fields")]
    for pos, (rule, _) in enumerate(strategies):
        left = 0
        for group, color, hatch in [("ckd", BURGUNDY, ""), ("notckd", TEAL, "///")]:
            n = eligibility.loc[("all24", group), "n_original_group"] if rule is None else eligibility.loc[(rule, group), "n_retained"]
            mix.barh(pos, n, .55, left=left, facecolor=color, edgecolor="white", hatch=hatch, lw=1)
            mix.text(left + n / 2, pos, str(int(n)), ha="center", va="center", color="white",
                     fontsize=13, weight="bold", bbox={"fc": color, "ec": "none", "pad": 1})
            left += n
        share = 250 / 400 if rule is None else eligibility.loc[(rule, "ckd"), "share_of_retained"]
        mix.text(left + 7, pos, f"{share:.1%}", va="center", fontsize=11.8, color=BURGUNDY,
                 weight="bold")
    mix.set(yticks=[0, 1, 2], yticklabels=[x[1] for x in strategies], xlim=(0, 510),
            xticks=[0, 200, 400], xlabel="Patient records")
    mix.set_ylim(2.55, -.95)
    mix.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=BURGUNDY, label="CKD"),
                        plt.Rectangle((0, 0), 1, 1, fc=TEAL, hatch="///", ec="white", label="Non-CKD")],
               loc="upper right", bbox_to_anchor=(1, 1.04), ncol=2, handlelength=1.2, fontsize=11.5)
    for ax in (fields, mix):
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    medians.set_title("Median creatinine (mg/dL)", loc="left")
    for group, label, color, marker, line in [
            ("all", "All", INK, "o", "--"), ("ckd", "CKD", BURGUNDY, "s", "-")]:
        measured = shifts.loc[group, "median_observed"]
        complete = shifts.loc[group, "median_complete"]
        medians.plot([0, 1], [measured, complete], color=color, marker=marker, ls=line, lw=2)
        medians.annotate(f"{measured:.2f}", (0, measured), xytext=(0, 8),
                         textcoords="offset points", ha="center", color=color, fontsize=12.8)
        medians.annotate(f"{complete:.2f}  {label}", (1, complete), xytext=(5, 0),
                         textcoords="offset points", va="center", color=color, fontsize=12.8,
                         weight="bold")
    medians.set(xlim=(-.22, 1.69), ylim=(0, 4.9), yticks=[0, 2, 4],
                xticks=[0, 1], xticklabels=["Measured", "Complete"])
    medians.grid(axis="y", color=LIGHT, lw=.8)
    save(fig, "cohort_selection.pdf", "Missingness, eligibility by diagnosis for all records, "
         "five-marker complete cases and all-24-field complete cases, plus the opposite "
         "changes in median creatinine overall and within CKD under the all-24 rule.")


def hemoglobin():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    hb = values.loc[values.feature.eq("hemo")]
    series = [
        ("Available", hb.observed.dropna(), INK, "-"),
        ("Complete", hb.loc[hb.complete_case, "observed"], BURGUNDY, (0, (5, 2))),
        ("Imputed", hb.imputed, TEAL, (0, (1, 1.35))),
    ]
    fig, (ax, middle_half) = plt.subplots(
        2, 1, sharex=True, figsize=(8.4, 5.95), layout="constrained",
        gridspec_kw={"height_ratios": [3.65, 1.05], "hspace": .04})
    for name, v, color, ls in series:
        unique, counts = np.unique(v, return_counts=True)
        ax.step(np.r_[unique[0], unique], np.r_[0, counts.cumsum() / len(v)], where="post",
                color=color, ls=ls, lw=2.6, label=f"{name}  (n = {len(v)})")
    filled_at = hb.observed.median()
    n_filled = hb.observed.isna().sum()
    midpoint = ((hb.imputed < filled_at).sum() + n_filled / 2) / len(hb)
    ax.annotate(f"{n_filled} filled at {filled_at:.2f}", (filled_at, midpoint),
                xytext=(.965, .18), textcoords="axes fraction", color=TEAL, weight="bold",
                ha="right", fontsize=13.5, arrowprops={"arrowstyle": "-|>", "color": TEAL, "lw": 1.5},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    ax.set(ylim=(-.025, 1.03), yticks=[0, .25, .5, .75, 1], ylabel="Share at or below value")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color=LIGHT, lw=.8)
    ax.legend(loc="upper left", fontsize=12)
    for pos, (label, v, color, pattern) in zip([2, 1, 0], series, strict=True):
        q1, median, q3 = v.quantile([.25, .50, .75])
        middle_half.plot([q1, q3], [pos, pos], color=color, lw=3, linestyle=pattern)
        middle_half.vlines([q1, q3], pos - .16, pos + .16, color=color, lw=1.5)
        middle_half.scatter(median, pos, facecolor="white", edgecolor=color, s=36, lw=1.6, zorder=3)
        middle_half.annotate(f"{q3 - q1:.2f}", (q3, pos), xytext=(7, 0), textcoords="offset points",
                             va="center", color=color, fontsize=12.5, weight="bold")
    middle_half.set(yticks=[2, 1, 0], yticklabels=[entry[0] for entry in series],
                    ylim=(-.43, 2.47), xlabel="Hemoglobin (UCI source units)")
    middle_half.tick_params(axis="y", length=0, labelsize=12.4)
    middle_half.spines["left"].set_visible(False)
    save(fig, "hemoglobin_views.pdf", "Cumulative distributions on a common hemoglobin axis. "
         "The lower intervals span the 25th to 75th percentiles, dots mark medians, and labels "
         "give interquartile widths in the source units.")


def renal_coefficients():
    results = pd.read_csv(TABLES / "renal_correlations.csv").query("group == 'all'").set_index("view")
    influence = pd.read_csv(TABLES / "diagnostics_renal_influence.csv")
    extreme = influence.loc[influence.sc_mg_dl.idxmax()]
    fig, axes = plt.subplots(1, 2, figsize=(8.9, 4.22), sharey=True)
    fig.subplots_adjust(left=.247, right=.975, bottom=.13, top=.86, wspace=.20)
    y = [3, 2, 1]
    for ax, metric, title in zip(axes, ("pearson", "spearman"),
                                 ("Pearson r  ·  linear", "Spearman ρ  ·  ranks"), strict=True):
        ax.set_title(title, fontsize=15, loc="left", pad=4)
        ax.set(xlim=(0, 1), ylim=(-.72, 3.70), xticks=[0, .5, 1],
               xticklabels=["0", "0.5", "1"])
        ax.grid(axis="x", color=LIGHT, lw=.8)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0, pad=8)
        for pos, (key, _, color, marker) in zip(y, DATA_VIEWS, strict=True):
            row = results.loc[key]
            value = row[metric]
            lower, upper = row[[f"{metric}_ci_low", f"{metric}_ci_high"]]
            if pd.notna(lower) and pd.notna(upper):
                ax.hlines(pos, lower, upper, color=color, lw=1.7)
                ax.vlines([lower, upper], pos - .09, pos + .09, color=color, lw=1.3)
            face = "white" if key == "imputed" else color
            ax.scatter(value, pos, s=66, marker=marker, facecolor=face,
                       edgecolor=color, lw=1.6, zorder=3)
            ax.annotate(f"{value:.3f}", (value, pos), xytext=(0, 6),
                        textcoords="offset points", ha="center", va="bottom", color=color,
                        fontsize=12.5, weight="bold")
        ax.axhline(.44, color=GRAY, lw=.8, ls=(0, (3, 3)))
        omitted = extreme[f"{metric}_after_omission"]
        ax.scatter(omitted, -.26, marker="^", s=66, facecolor="white",
                   edgecolor=GRAY, linewidth=1.6, zorder=3)
        ax.annotate(f"{omitted:.3f}", (omitted, -.26), xytext=(0, 6),
                    textcoords="offset points", ha="center", va="bottom", fontsize=12.5,
                    weight="bold", color=GRAY)
    labels = [f"{name}\nn = {int(results.loc[key, 'n_pairs'])}" for key, name, _, _ in DATA_VIEWS]
    labels.append(f"Omit {extreme.sc_mg_dl:g} mg/dL\nn = {int(extreme.n_after_omission)}")
    axes[0].set_yticks([*y, -.26], labels, fontsize=13.2)
    save(fig, "renal_coefficients.pdf",
         "Creatinine and urea across all records. Both panels use the same coefficient scale. "
         "Whiskers are diagnosis-stratified 95% percentile bootstrap intervals for measured "
         "and complete cases. The last row is a separate sensitivity check omitting the single "
         "highest creatinine from the measured pairs.")


def glucose_bounds():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    ckd = values.loc[values.group.eq("ckd") & values.feature.eq("bgr")]
    measured = ckd.observed.dropna()
    views = (measured, ckd.loc[ckd.complete_case, "observed"], ckd.imputed)
    n = len(ckd)
    high, missing = int(measured.ge(200).sum()), int(ckd.observed.isna().sum())
    lower, upper = high / n, (high + missing) / n
    fig, ax = plt.subplots(figsize=(8.9, 3.90))
    fig.subplots_adjust(left=.246, right=.952, bottom=.17, top=.976)
    ax.set(xlim=(0, 1), ylim=(-.43, 4.18), xticks=[0, .25, .5, .75, 1])
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.fill_betweenx([-.37, 3.24], lower, upper, color="#F9EDDE", zorder=0)
    ax.vlines([lower, upper], -.37, 3.28, color=GLUCOSE_ORANGE, lw=1, linestyles="--")

    left = 0
    for count, label, fill, edge, hatch, ink in [
            (high, "high", GLUCOSE_ORANGE, "white", None, "white"),
            (missing, "missing", "#FFFAEF", "#986E45", "///", INK),
            (n - high - missing, "below 200", "#E7E4E8", "white", None, INK)]:
        width = count / n
        ax.barh(3.65, width, left=left, height=.68, color=fill, edgecolor=edge, hatch=hatch, lw=.9)
        ax.text(left + width / 2, 3.65, f"{count}\n{label}", ha="center", va="center",
                fontsize=11.7, weight="bold", color=ink, linespacing=.94,
                bbox={"fc": fill, "ec": "none", "pad": .55} if hatch else None)
        left += width
    ax.annotate(f"{lower:.1%}–{upper:.1%} possible in all {n}",
                xy=((lower + upper) / 2, 2.83), xytext=(.53, 2.83),
                ha="left", va="center", fontsize=12.6, weight="bold", color=GLUCOSE_ORANGE,
                arrowprops={"arrowstyle": "-", "color": GLUCOSE_ORANGE, "lw": 1})
    labels = [f"All CKD records\n(n = {n})"]
    for pos, series, (key, name, color, marker) in zip([2, 1, 0], views, DATA_VIEWS, strict=True):
        high_in_view = int(series.ge(200).sum())
        share = high_in_view / len(series)
        labels.append(f"{name}\n{high_in_view}/{len(series)} high")
        ax.scatter(share, pos, marker=marker, s=85, edgecolor=color, lw=1.7,
                   facecolor="white" if key == "imputed" else color, zorder=3)
        alignment, offset = {"observed": ("center", (0, 11)), "complete_case": ("left", (8, 1)),
                             "imputed": ("right", (-8, 1))}[key]
        ax.annotate(f"{share:.1%}", (share, pos), xytext=offset, textcoords="offset points",
                    va="center", ha=alignment, fontsize=13.5, color=color, weight="bold")
    ax.set_yticks([3.65, 2, 1, 0], labels, fontsize=12.3)
    ax.set_xlabel("Share of records", fontsize=13, labelpad=1)
    save(fig, "glucose_bounds.pdf",
         "Random glucose at least 200 mg/dL. Among 250 CKD records, 72 were known high and "
         "38 had missing glucose. The band is the range permitted by those missing outcomes "
         "in all 250. The three points use their own labeled denominators.")


def pca_scale():
    pc1 = pd.read_csv(TABLES / "pca_variance.csv").query("component == 'PC1'").set_index("scale")
    weights = pd.read_csv(TABLES / "pca_loadings.csv").query("component == 'PC1'").set_index(["scale", "feature"])
    features = ["hemo", "sc", "bu", "bgr", "bp"]
    labels = ["Hemoglobin", "Creatinine", "Blood urea", "Glucose", "Blood pressure"]
    fig, axes = plt.subplots(1, 2, figsize=(8.9, 2.70), sharey=True)
    fig.subplots_adjust(left=.19, right=.975, bottom=.20, top=.81, wspace=.25)
    for ax, key, name in zip(axes, ["raw", "zscore"], ["Original units", "Unit variance"], strict=True):
        share = pc1.loc[key, "explained_fraction"]
        coefficients = np.array([weights.loc[(key, feature), "eigenvector_weight"] for feature in features])
        ax.axvline(0, color=GRAY, lw=.9)
        ax.barh(np.arange(5), coefficients, height=.55, color="#634E78")
        for y, coefficient in enumerate(coefficients):
            ax.annotate(f"{coefficient:+.2f}", (coefficient, y),
                        xytext=(4 if coefficient >= 0 else -4, 0), textcoords="offset points",
                        ha="left" if coefficient >= 0 else "right", va="center", fontsize=11.1)
        ax.set_title(f"{name}\nPC1: {share:.1%} of variance", fontsize=12.6, pad=8)
        ax.set(xlim=(-.78, 1.25), ylim=(4.6, -.6), xticks=[-.5, 0, .5, 1],
               xticklabels=["−0.5", "0", "0.5", "1.0"])
        ax.grid(axis="x", color=LIGHT, lw=.6)
        ax.spines[["left", "top", "right"]].set_visible(False)
        ax.tick_params(axis="y", length=0, pad=7, labelsize=11.6)
        ax.tick_params(axis="x", labelsize=10.8, length=3)
    axes[0].set_yticks(np.arange(5), labels)
    fig.text(.59, .025, "Signed PC1 eigenvector coefficient", ha="center", fontsize=11.8)
    save(fig, "pca_scale.pdf",
         "Signed PC1 eigenvector coefficients for five markers in the same 400 imputed "
         "records. Original-unit PC1 explains 68.8% of variance; unit-variance PC1 explains 43.3%.")


def grade_zero():
    patients = pd.read_csv(PATIENTS)
    grade = measured_grade_zero(patients)
    # Within each result category the cells follow source row order in both panels.
    grade = grade.sort_values(["finding", "row_id"], ascending=[False, True]).reset_index(drop=True)
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.55))
    fig.subplots_adjust(left=.03, right=.97, bottom=.222, top=.865, wspace=.16)
    for ax, complete_only in zip(axes, (False, True), strict=True):
        included = grade.complete_case if complete_only else pd.Series(True, index=grade.index)
        for selected, symbol, face, edge in [
            (included & ~grade.finding, "o", "white", INK),
            (included & grade.finding, "s", BURGUNDY, BURGUNDY),
            (~included, "x", GRAY, GRAY),
        ]:
            idx = grade.index[selected]
            kw = {"color": edge} if symbol == "x" else {"edgecolors": edge, "facecolors": face}
            ax.scatter(idx % 9, idx // 9, s=60 if symbol == "x" else 100, marker=symbol, lw=1.4, **kw)
        case_index = grade.index[grade.row_id.eq(43)].item()
        ax.scatter(case_index % 9, case_index // 9, marker="o", s=260, facecolors="none",
                   edgecolors=INK, lw=1.2, zorder=4)
        label = "24 fields required" if complete_only else "Three fields required"
        ax.set_title(label, loc="left", fontsize=14, pad=11)
        n_finding = (included & grade.finding).sum()
        ax.text(.5, -.16, f"{n_finding} of {included.sum()} with a finding",
                transform=ax.transAxes, fontsize=13, weight="bold", ha="center")
        ax.set(xlim=(-.7, 8.7), ylim=(4.65, -.65), aspect="equal")
        ax.axis("off")
    handles = [Line2D([], [], marker=m, ls="none", markersize=7, markerfacecolor=f,
                      markeredgecolor=e, label=t) for m, f, e, t in [
                          ("s", BURGUNDY, BURGUNDY, "Anemia or high glucose"),
                          ("o", "white", INK, "Neither"), ("x", GRAY, GRAY, "Excluded")]]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, -.005), ncol=3,
               columnspacing=1.1, handletextpad=.4, fontsize=11.5)
    save(fig, "grade_zero_selection.pdf",
         "Each position identifies the same grade-zero CKD patient under two eligibility rules.")


if __name__ == "__main__":
    FIGURES.mkdir(exist_ok=True)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 13.5, "axes.titlesize": 15,
                         "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": INK, "axes.edgecolor": GRAY, "text.color": INK,
                         "xtick.color": INK, "ytick.color": INK, "axes.axisbelow": True,
                         "legend.frameon": False, "hatch.linewidth": .65, "pdf.fonttype": 42}):
        missing_data_paths()
        cohort()
        hemoglobin()
        grade_zero()
        renal_coefficients()
        glucose_bounds()
        pca_scale()

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


def case_summary_text():
    """Render the selected patient's observed clinical values as a native table."""
    case = pd.read_csv(PATIENTS).set_index("row_id").loc[43]
    rows = [
        ("Urine albumin", f"Grade {case.al:.0f}"),
        ("Diabetes history", "Yes" if case.dm == "yes" else "No"),
        ("Creatinine", f"{case.sc:.1f} mg/dL"),
        ("Hemoglobin", f"{case.hemo:g} (UCI units)"),
        ("Recorded anemia", "Yes" if case.anemia == 1 else "No"),
        ("Random glucose", rf"\color{{maroon}}{case.bgr:.0f} mg/dL"),
    ]
    paired_rows = [left + right for left, right in zip(rows[::2], rows[1::2], strict=True)]
    return (r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrlr@{}}" + "\n"
            + "\n".join(left_label + r" & \textbf{" + left_value + "} & "
                        + right_label + r" & \textbf{" + right_value + r"} \\[0.3ex]"
                        for left_label, left_value, right_label, right_value in paired_rows)
            + "\n" + r"\end{tabular*}" + "\n")


def glucose_history_data():
    """Keep the exact measured x values and source identity of each CKD patient."""
    patients = pd.read_csv(PATIENTS)
    points = patients.dropna(subset=["bgr"]).copy()
    summary = []
    for group in ("no", "yes"):
        subset = patients.loc[patients.dm.eq(group)]
        summary.append({"dm": group, "n_total": len(subset),
                        "n_measured": int(subset.bgr.count()),
                        "n_high": int(subset.bgr.ge(200).sum()),
                        "n_missing": int(subset.bgr.isna().sum())})
    return points, pd.DataFrame(summary)


def glucose_history():
    points, summary = glucose_history_data()
    summary = summary.set_index("dm")
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    fig.subplots_adjust(left=.24, right=.97, top=.88, bottom=.18)
    labels = []
    for group, y, name in (("no", 1, "No history"), ("yes", 0, "Recorded history")):
        subset = points.loc[points.dm.eq(group)].sort_values(["bgr", "row_id"]).copy()
        # Vertical offsets separate nearby marks; the measured x values stay fixed.
        bins = (subset.bgr / 8).round()
        within = subset.groupby(bins).cumcount()
        counts = subset.groupby(bins).bgr.transform("size")
        offsets = (within - (counts - 1) / 2) * .062
        subset["plot_y"] = y + offsets
        for high, color in ((False, GRAY), (True, GLUCOSE_ORANGE)):
            selected = subset.loc[subset.bgr.ge(200).eq(high)]
            ax.scatter(selected.bgr, selected.plot_y, color=color, s=20, lw=0, alpha=.85)
        record = subset.loc[subset.row_id.eq(43)]
        if not record.empty:
            py = record.plot_y.item()
            ax.scatter([record.bgr.item()], [py], marker="D", s=75, facecolor="white",
                       edgecolor=BURGUNDY, linewidth=2, zorder=4)
            ax.annotate("Record 43: 204", (record.bgr.item(), py), xytext=(325, 1.53),
                        fontsize=14, color=BURGUNDY, weight="bold", ha="center",
                        arrowprops={"arrowstyle": "-", "color": BURGUNDY, "lw": 1.3},
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
        row = summary.loc[group]
        labels.append(f"{name}\n{row.n_high}/{row.n_measured} high ({row.n_high/row.n_measured:.1%})")
    ax.axvline(200, color=GLUCOSE_ORANGE, lw=1.4, ls=(0, (4, 3)), zorder=0)
    ax.text(195, 1.53, "200", color=GLUCOSE_ORANGE, fontsize=13, ha="right", va="center")
    ax.set(xlim=(0, 515), ylim=(-.52, 1.78), yticks=[1, 0], yticklabels=labels,
           xticks=[0, 100, 200, 300, 400, 500], xlabel="Random glucose (mg/dL)")
    ax.tick_params(axis="y", length=0, pad=9, labelsize=13.5)
    ax.tick_params(axis="x", labelsize=13)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.grid(axis="x", color=LIGHT, lw=.6, zorder=0)
    fig.text(.24, .975, f"{len(points)} measured CKD records", ha="left", va="top",
             fontsize=14, weight="bold")
    save(fig, "glucose_history.pdf", "Exact measured random glucose for 212 CKD records, "
         "separated by recorded diabetes history. Vertical offsets only separate marks. "
         "The 200 mg/dL threshold and source Record 43 at 204 mg/dL are marked.")


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
    eligibility = pd.read_csv(TABLES / "eligibility_rules.csv").set_index(["rule", "group"])
    fig, ax = plt.subplots(figsize=(8.9, 4.1))
    fig.subplots_adjust(left=.21, right=.82, top=.88, bottom=.20)
    strategies = [(None, "All records"), ("core5", "Five markers"), ("all24", "All 24 fields")]
    labels = []
    for pos, (rule, label) in enumerate(strategies):
        total = eligibility.loc[("all24", "all"), "n_original_group"] if rule is None else eligibility.loc[(rule, "all"), "n_retained"]
        labels.append(f"{label}\nn = {total}")
        left = 0
        for group, color, hatch in [("ckd", BURGUNDY, ""), ("notckd", TEAL, "///")]:
            n = eligibility.loc[("all24", group), "n_original_group"] if rule is None else eligibility.loc[(rule, group), "n_retained"]
            ax.barh(pos, n, .59, left=left, facecolor=color, edgecolor="white", hatch=hatch, lw=1)
            ax.text(left + n / 2, pos, str(int(n)), ha="center", va="center", color="white", fontsize=15,
                    weight="bold", bbox={"fc": color, "ec": "none", "pad": 1})
            left += n
        ckd = eligibility.loc[("all24", "ckd"), "n_original_group"] if rule is None else eligibility.loc[(rule, "ckd"), "n_retained"]
        ax.text(430, pos, f"{ckd/total:.1%}", va="center", fontsize=15, color=BURGUNDY, weight="bold")
    ax.text(430, -.63, "CKD share", fontsize=13, color=GRAY, ha="left")
    ax.set(yticks=[0, 1, 2], yticklabels=labels, xlim=(0, 410), ylim=(2.5, -.75),
           xticks=[0, 100, 200, 300, 400], xlabel="Patient records retained")
    ax.tick_params(axis="y", length=0, pad=11, labelsize=14)
    ax.tick_params(axis="x", labelsize=13)
    ax.spines["left"].set_visible(False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=BURGUNDY, label="CKD"),
                       plt.Rectangle((0, 0), 1, 1, fc=TEAL, hatch="///", ec="white", label="Non-CKD")],
              loc="lower left", bbox_to_anchor=(0, 1.01), ncol=2, handlelength=1.3, fontsize=14)
    save(fig, "cohort_selection.pdf", "Counts and CKD share for all records, five-marker "
         "complete cases and all-24-field complete cases. Bars share a zero-based count axis.")


def hemoglobin():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    hb = values.loc[values.feature.eq("hemo")]
    series = [("Available", hb.observed.dropna(), INK, "-"),
              ("Complete", hb.loc[hb.complete_case, "observed"], BURGUNDY, (0, (5, 2))),
              ("Imputed", hb.imputed, TEAL, (0, (1, 1.35)))]
    fig, ax = plt.subplots(figsize=(8.9, 4.7))
    fig.subplots_adjust(left=.13, right=.97, top=.96, bottom=.17)
    for name, values, color, line in series:
        unique, counts = np.unique(values, return_counts=True)
        ax.step(np.r_[unique[0], unique], np.r_[0, counts.cumsum()/len(values)], where="post",
                color=color, ls=line, lw=2.6, label=f"{name}  (n = {len(values)})")
    median = hb.observed.median()
    n_filled = hb.observed.isna().sum()
    midpoint = ((hb.imputed < median).sum() + n_filled/2)/len(hb)
    ax.annotate(f"{n_filled} filled at {median:.2f}", (median, midpoint), xytext=(.97, .18),
                textcoords="axes fraction", color=TEAL, weight="bold", ha="right", fontsize=14.5,
                arrowprops={"arrowstyle": "-|>", "color": TEAL, "lw": 1.5},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5})
    ax.set(ylim=(-.025, 1.03), yticks=[0, .25, .5, .75, 1],
           ylabel="Share at or below value", xlabel="Hemoglobin (UCI source units)")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color=LIGHT, lw=.8)
    ax.legend(loc="upper left", fontsize=14)
    ax.tick_params(axis="both", labelsize=13)
    save(fig, "hemoglobin_views.pdf", "Three empirical cumulative distributions on one "
         "hemoglobin axis. Fifty-two imputed values create a 13% step at 12.65 source units.")


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


def glucose_bounds_data():
    """Separate finite-cohort missing-value bounds from each analysis denominator."""
    values = pd.read_csv(TABLES / "measurement_values.csv")
    ckd = values.loc[values.group.eq("ckd") & values.feature.eq("bgr")]
    measured = ckd.observed.dropna()
    n = len(ckd)
    high, missing = int(measured.ge(200).sum()), int(ckd.observed.isna().sum())
    totals = {"n_total": n, "n_high": high, "n_missing": missing,
              "n_below": n - high - missing, "lower": high / n,
              "upper": (high + missing) / n}
    samples = (measured, ckd.loc[ckd.complete_case, "observed"], ckd.imputed)
    views = []
    for series, (key, _, _, _) in zip(samples, DATA_VIEWS, strict=True):
        n_high = int(series.ge(200).sum())
        views.append({"view": key, "n": len(series), "n_high": n_high,
                      "share": n_high / len(series)})
    return totals, pd.DataFrame(views)


def glucose_bounds():
    totals, views = glucose_bounds_data()
    n, high, missing = (totals[key] for key in ("n_total", "n_high", "n_missing"))
    lower, upper = totals["lower"], totals["upper"]
    views = views.set_index("view")
    fig, ax = plt.subplots(figsize=(8.9, 4.20))
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
                fontsize=12.4, weight="bold", color=ink, linespacing=.94,
                bbox={"fc": fill, "ec": "none", "pad": .55} if hatch else None)
        left += width
    ax.annotate(f"{lower:.1%}–{upper:.1%} possible in all {n}",
                xy=((lower + upper) / 2, 2.83), xytext=(.53, 2.83),
                ha="left", va="center", fontsize=12.6, weight="bold", color=GLUCOSE_ORANGE,
                arrowprops={"arrowstyle": "-", "color": GLUCOSE_ORANGE, "lw": 1})
    labels = [f"All CKD records\n(n = {n})"]
    for pos, (key, name, color, marker) in zip([2, 1, 0], DATA_VIEWS, strict=True):
        row = views.loc[key]
        high_in_view, sample_n, share = int(row.n_high), int(row.n), row.share
        labels.append(f"{name}\n{high_in_view}/{sample_n} high")
        ax.scatter(share, pos, marker=marker, s=85, edgecolor=color, lw=1.7,
                   facecolor="white" if key == "imputed" else color, zorder=3)
        alignment, offset = {"observed": ("center", (0, 11)), "complete_case": ("left", (8, 1)),
                             "imputed": ("right", (-8, 1))}[key]
        ax.annotate(f"{share:.1%}", (share, pos), xytext=offset, textcoords="offset points",
                    va="center", ha=alignment, fontsize=13.5, color=color, weight="bold")
    ax.set_yticks([3.65, 2, 1, 0], labels, fontsize=13)
    ax.tick_params(axis="x", labelsize=13)
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
    fig, axes = plt.subplots(1, 2, figsize=(8.9, 4.05), sharey=True)
    fig.subplots_adjust(left=.21, right=.97, bottom=.19, top=.79, wspace=.23)
    for ax, key, name in zip(axes, ["raw", "zscore"], ["Original units", "Unit variance"], strict=True):
        share = pc1.loc[key, "explained_fraction"]
        coefficients = np.array([weights.loc[(key, feature), "eigenvector_weight"] for feature in features])
        ax.axvline(0, color=GRAY, lw=.9)
        ax.barh(np.arange(5), coefficients, height=.55, color="#634E78")
        for y, coefficient in enumerate(coefficients):
            ax.annotate(f"{coefficient:+.2f}", (coefficient, y),
                        xytext=(4 if coefficient >= 0 else -4, 0), textcoords="offset points",
                        ha="left" if coefficient >= 0 else "right", va="center", fontsize=12.5)
        ax.set_title(f"{name}\nPC1: {share:.1%} of variance", fontsize=14, pad=10)
        ax.set(xlim=(-.78, 1.25), ylim=(4.6, -.6), xticks=[-.5, 0, .5, 1],
               xticklabels=["−0.5", "0", "0.5", "1.0"])
        ax.grid(axis="x", color=LIGHT, lw=.6)
        ax.spines[["left", "top", "right"]].set_visible(False)
        ax.tick_params(axis="y", length=0, pad=7, labelsize=13)
        ax.tick_params(axis="x", labelsize=12.5, length=3)
    axes[0].set_yticks(np.arange(5), labels)
    fig.text(.59, .035, "Signed PC1 eigenvector coefficient", ha="center", fontsize=13)
    save(fig, "pca_scale.pdf",
         "Signed PC1 eigenvector coefficients for five markers in the same 400 imputed "
         "records. Original-unit PC1 explains 68.8% of variance; unit-variance PC1 explains 43.3%.")


def grade_zero_data():
    """Fix one source-patient ordering for both sides of the selection matrix."""
    patients = pd.read_csv(PATIENTS)
    grade = measured_grade_zero(patients)
    return grade.sort_values(["finding", "row_id"], ascending=[False, True]).reset_index(drop=True)


def grade_zero():
    grade = grade_zero_data()
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.60))
    fig.subplots_adjust(left=.03, right=.97, bottom=.29, top=.84, wspace=.16)
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
        retained = int(included.sum())
        finding_label = (f"{n_finding}/{int(grade.finding.sum())} with a finding retained"
                         if complete_only else f"{n_finding} with a finding")
        ax.text(.5, -.13, f"{retained}/{len(grade)} retained\n{finding_label}",
                transform=ax.transAxes, fontsize=12.5, weight="bold", ha="center", va="top")
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
    (HERE / "case_record43.tex").write_text(case_summary_text(), encoding="utf-8")
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 13.5, "axes.titlesize": 15,
                         "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": INK, "axes.edgecolor": GRAY, "text.color": INK,
                         "xtick.color": INK, "ytick.color": INK, "axes.axisbelow": True,
                         "legend.frameon": False, "hatch.linewidth": .65, "pdf.fonttype": 42}):
        glucose_history()
        cohort()
        grade_zero()
        hemoglobin()
        glucose_bounds()
        renal_coefficients()
        pca_scale()

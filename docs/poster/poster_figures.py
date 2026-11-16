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
from matplotlib.patches import FancyBboxPatch, Rectangle
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


def measured_pair_plots(ax, patients):
    """Reproduce the three available-case clinical questions in JH's Figure 1."""
    albumin = pd.read_csv(CLINICAL / "albumin_grades.csv").query("view == 'observed'")
    rank = pd.read_csv(CLINICAL / "albumin_association.csv").query(
        "view == 'observed' and sample == 'all_grades'").iloc[0]
    pairs = patients.dropna(subset=["sc", "hemo"])
    fit = pd.read_csv(CLINICAL / "anemia_fit.csv")
    model = pd.read_csv(CLINICAL / "anemia_association.csv").query(
        "view == 'observed' and sample == 'all_pairs'").iloc[0]
    slope = f"{model.slope:.2f}".replace("-", "−")
    risk = pd.read_csv(CLINICAL / "glucose_threshold.csv").query(
        "view == 'observed'").set_index("dm").loc[["no", "yes"]]

    flow_box(ax, .69, 2.33, 13.20, 3.46, GRAY)
    centers = (2.89, 7.29, 11.69)
    for divider in (5.09, 9.49):
        ax.plot([divider, divider], [2.47, 5.64], color=LIGHT, lw=1)
    subtitles = (
        ("Urine albumin and creatinine", int(rank.n), "Creatinine (mg/dL, log scale)",
         f"Spearman ρ = {rank.rho:.2f}", "Thin range, thick IQR, dot median"),
        ("Creatinine and hemoglobin", len(pairs), "Hemoglobin (source units)",
         f"{slope} Hb units per doubling", "Band shows 95% CI for mean Hb"),
        ("Diabetes history and glucose", int(risk.n_measured.sum()), "Random glucose ≥200 mg/dL",
         f"{risk.proportion.iloc[0]:.1%} vs {risk.proportion.iloc[1]:.1%} high glucose",
         "Whiskers show 95% Wilson intervals"),
    )
    plots = []
    for x, (title, n, unit, result, guide) in zip(centers, subtitles, strict=True):
        ax.text(x, 5.52, title, fontsize=16.8, ha="center", va="center", weight="bold", color=INK)
        ax.text(x, 5.20, f"{n} measured pairs", fontsize=15.5, ha="center", va="center", color=INK)
        p = ax.inset_axes([x - 1.49, 3.60, 3.22, 1.10], transform=ax.transData)
        p.tick_params(axis="both", labelsize=13.8, pad=2, length=3.5)
        p.spines[["top", "right"]].set_visible(False)
        p.set_axisbelow(True)
        p.grid(axis="y", color=LIGHT, lw=.7)
        p.text(0, 1.10, unit, transform=p.transAxes, fontsize=14, ha="left", va="bottom")
        ax.text(x, 2.89, result, fontsize=15.6, ha="center", va="center", color=INK, weight="bold")
        ax.text(x, 2.55, guide, fontsize=14, ha="center", va="center", color=GRAY)
        plots.append(p)

    kidneys, blood, sugar = plots
    kidneys.vlines(albumin.grade, albumin["min"], albumin["max"], color=GRAY, lw=1.1)
    kidneys.vlines(albumin.grade, albumin.q1, albumin.q3, color=GRAY, lw=5)
    kidneys.scatter(albumin.grade, albumin["median"], color=INK, edgecolor="white",
                    s=30, linewidth=.6, zorder=3)
    for row in albumin.loc[albumin.n_pairs.eq(1)].itertuples():
        kidneys.annotate("n = 1", (row.grade, row.median), xytext=(0, 6),
                         textcoords="offset points", ha="center", fontsize=13.5, color=GRAY)
    kidneys.set_yscale("log")
    kidneys.set(xlim=(-.45, 5.45), ylim=(.4, 42), xticks=range(6))
    kidneys.set_yticks([.5, 2, 8, 32], ["0.5", "2", "8", "32"])
    kidneys.set_xlabel("Urine albumin grade", fontsize=14, labelpad=2)

    blood.scatter(pairs.sc, pairs.hemo, s=8, color="#8F8991", linewidth=0)
    blood.fill_between(fit.sc, fit.ci_low, fit.ci_high, color="#C6C0C8", alpha=.65)
    blood.plot(fit.sc, fit.mean_hemo, color=INK, lw=1.8)
    blood.set_xscale("log", base=2)
    blood.set(xlim=(.48, 90), ylim=(2, 18), yticks=[4, 10, 16])
    blood.set_xticks([1, 4, 16, 64], ["1", "4", "16", "64"])
    blood.set_xlabel("Creatinine (mg/dL, log₂ scale)", fontsize=14, labelpad=2)

    sugar.errorbar([0, 1], risk.proportion,
                   yerr=[risk.proportion - risk.ci_low, risk.ci_high - risk.proportion],
                   fmt="o", color=INK, lw=1.45, capsize=4, markersize=5)
    for pos, row in enumerate(risk.itertuples()):
        sugar.annotate(f"{row.n_high}/{row.n_measured}", (pos, row.proportion),
                       xytext=(6, 0), textcoords="offset points", fontsize=13.8, va="center")
    sugar.set(xlim=(-.36, 1.68), ylim=(0, .68))
    sugar.set_yticks([0, .25, .50], ["0%", "25%", "50%"])
    sugar.set_xticks([0, 1], ["No history", "History"])
    sugar.set_xlabel("Recorded diabetes history", fontsize=14, labelpad=2)


def grade_zero_branch(ax, patients):
    """Count overlapping findings on the same jointly observed patient records."""
    grade = measured_grade_zero(patients)
    counts = pd.crosstab(grade.anemia, grade.high_glucose).reindex(
        index=[1, 0], columns=[0, 1], fill_value=0)
    retained = grade.loc[grade.complete_case]
    n_joint = len(patients.dropna(subset=["al", "anemia", "high_glucose"]))

    flow_box(ax, .69, .08, 13.20, 2.00, GRAY)
    ax.text(1.00, 1.79, "Urine albumin grade 0", fontsize=17.3, weight="bold", va="center")
    ax.text(1.00, 1.21, f"{n_joint} had urine albumin, anemia\nstatus and glucose recorded.",
            fontsize=14.6, va="center", linespacing=1.2)
    ax.text(1.00, .49, f"{len(grade)} of these had grade 0.", fontsize=15.1,
            va="center", weight="bold")

    ax.text(7.47, 1.79, "Random glucose (mg/dL)", ha="center", va="center",
            fontsize=14.7, weight="bold")
    for x, label in [(6.98, "<200"), (8.00, "≥200")]:
        ax.text(x, 1.42, label, ha="center", va="center", fontsize=14)
    for row_index, (flag, label, y) in enumerate([(1, "Anemia", .99), (0, "No anemia", .48)]):
        ax.text(6.32, y, label, ha="right", va="center", fontsize=14.1)
        for column, x in enumerate([6.98, 8.00]):
            finding = bool(flag or column)
            ax.add_patch(Rectangle((x - .49, y - .235), .98, .47,
                                   facecolor="#F2DFE7" if finding else "#F0EEF0",
                                   edgecolor="white", lw=1))
            ax.text(x, y, str(counts.iat[row_index, column]), fontsize=16.3, weight="bold",
                    ha="center", va="center", color=BURGUNDY if finding else INK)
    flow_arrow(ax, (8.70, 1.02), (9.10, 1.02))
    ax.text(9.28, 1.65, f"{grade.finding.sum()} of {len(grade)} had a finding",
            fontsize=16.5, weight="bold", color=BURGUNDY, va="center")
    ax.text(9.28, 1.23, "Anemia, high glucose or both.", fontsize=14.2, va="center")
    ax.text(9.28, .62, f"All 24 fields present in {len(retained)} of {len(grade)}.\n"
            f"Of the {grade.finding.sum()} with a finding, {retained.finding.sum()} remained.",
            va="center", fontsize=14.2, linespacing=1.22)


def missing_data_paths():
    """Nest the clinical analyses in RenalLensPoster/figures/Figure_1.svg under available cases."""
    values = pd.read_csv(TABLES / "measurement_values.csv")
    glucose = values.loc[values.feature.eq("bgr")].set_index("row_id")
    ckd = glucose.loc[glucose.group.eq("ckd")]
    complete = glucose.loc[glucose.complete_case]
    n_complete_ckd = complete.group.eq("ckd").sum()
    case = glucose.loc[43]
    patients = pd.read_csv(PATIENTS)

    # Use the same view colors as the hemoglobin figure. Every path also has
    # a method name and an explicit patient disposition for monochrome prints.
    paths = [
        ("Available case", INK, "Use the measured fields\neach question needs.",
         f"Glucose tests in {ckd.observed.count()}/{len(ckd)} CKD records",
         "Record 43 retained", f"{case.observed:.0f} mg/dL measured"),
        ("Complete case", BURGUNDY, "Require all 24 fields\nto be present.",
         f"{len(complete)} retained ({n_complete_ckd} CKD, {len(complete) - n_complete_ckd} non-CKD)",
         "Record 43 excluded", f"{case.observed:.0f} mg/dL omitted"),
        ("Single imputation", TEAL, "Pooled median for numbers,\npooled mode for categories.",
         f"{len(glucose)} retained ({len(ckd)} CKD, {len(glucose) - len(ckd)} non-CKD)",
         "Record 43 retained", f"{case.imputed:.0f} mg/dL measured"),
    ]
    pink = "#F6E5EA"  # Gemini alert-block background
    fig = plt.figure(figsize=(14, 9.75), facecolor=pink)
    ax = fig.add_axes((0, 0, 1, 1), xlim=(0, 14), ylim=(0, 9.75))
    ax.axis("off")

    centers = (2.37, 7, 11.63)
    flow_box(ax, 4.14, 9.01, 5.72, .66, BURGUNDY)
    ax.text(7, 9.46, f"{len(glucose)} UCI patient records", ha="center", va="center",
            fontsize=20, weight="bold", color=INK)
    ax.text(7, 9.16, f"{len(ckd)} CKD + {len(glucose) - len(ckd)} non-CKD",
            ha="center", va="center", fontsize=16, color=INK)
    ax.plot([7, 7], [9.01, 8.88], color=GRAY, lw=1.6)
    ax.plot([centers[0], centers[-1]], [8.88, 8.88], color=GRAY, lw=1.6)

    for x, (method, color, rule, sample, disposition, reading) in zip(centers, paths, strict=True):
        flow_box(ax, x - 2.23, 6.55, 4.46, 2.10, color)
        flow_arrow(ax, (x, 8.89), (x, 8.66))
        ax.text(x, 8.41, method, ha="center", va="center", fontsize=18.4,
                weight="bold", color=color)
        ax.text(x, 7.98, rule, ha="center", va="center", fontsize=15.4, linespacing=1.12, color=INK)
        ax.text(x, 7.51, sample, ha="center", va="center", fontsize=14.8, color=INK)
        ax.plot([x - 1.97, x + 1.97], [7.28, 7.28], lw=.9, color=color)
        ax.text(x, 7.05, disposition, ha="center", va="center", fontsize=15.8,
                weight="bold", color=color)
        ax.text(x, 6.75, reading, ha="center", va="center", fontsize=15, color=INK)

    flow_arrow(ax, (centers[0], 6.55), (centers[0], 6.40))
    flow_box(ax, .12, 5.95, 7.02, .44, INK)
    ax.text(3.63, 6.17, f"Available-case analyses within the {len(ckd)} CKD records",
            ha="center", va="center", fontsize=16.1, weight="bold", color=INK)
    ax.text(7.42, 6.17, "A record can contribute to more than one analysis.",
            va="center", fontsize=14, color=GRAY)
    ax.plot([.30, .30], [5.95, 1.76], color=GRAY, lw=1.55)
    flow_arrow(ax, (.30, 5.49), (.67, 5.49))
    flow_arrow(ax, (.30, 1.76), (.67, 1.76))
    measured_pair_plots(ax, patients)
    grade_zero_branch(ax, patients)

    save(fig, "missing_data_paths.pdf",
         "Adapted from the JH poster's Figure 1. Three missing-data rules applied to the "
         "same 400 records. The measured CKD branch "
         "contains three overlapping paired analyses and a separate grade-zero subgroup. "
         "Of 45 jointly observed grade-zero records, 16 had anemia or high glucose. "
         "Only one of the 45 met the 24-field rule and none of the 16 findings remained.")


def cohort():
    rates = pd.read_csv(TABLES / "missingness.csv")
    top = rates.loc[rates.group.eq("all")].nlargest(5, "n_missing")
    labels = {"rbc": "Red cell assessment", "rbcc": "Red cell count",
              "wbcc": "White cell count", "pot": "Potassium", "sod": "Sodium"}
    retention = pd.read_csv(TABLES / "retention.csv").set_index("group")
    fig, (fields, mix) = plt.subplots(1, 2, figsize=(13.4, 3.25), layout="constrained",
                                      gridspec_kw={"width_ratios": [1.16, 1], "wspace": .08})
    fields.set_title("Five fields most often missing", loc="left")
    y = np.arange(len(top))
    counts = top.n_missing.to_numpy()
    fields.barh(y, counts, .56, color=GRAY)
    for pos, row in enumerate(top.itertuples()):
        fields.text(row.n_missing + 4, pos, f"{row.n_missing}  ({row.missing_rate:.1%})",
                    va="center", fontsize=12)
    fields.set(yticks=y, yticklabels=[labels[f] for f in top.feature], xticks=[0, 50, 100, 150],
               xlim=(0, 218), xlabel="Records missing the field, out of 400")
    fields.invert_yaxis()

    mix.set_title("Who remains after deletion?", loc="left")
    strategies = [("n_total", "All records"), ("n_complete", "Complete cases")]
    for pos, (column, _) in enumerate(strategies):
        left = 0
        for group, color, hatch in [("ckd", BURGUNDY, ""), ("notckd", TEAL, "///")]:
            n = retention.loc[group, column]
            mix.barh(pos, n, .55, left=left, facecolor=color, edgecolor="white", hatch=hatch, lw=1)
            mix.text(left + n / 2, pos, str(int(n)), ha="center", va="center", color="white",
                     fontsize=13, weight="bold", bbox={"fc": color, "ec": "none", "pad": 1})
            left += n
    mix.set(yticks=[0, 1], yticklabels=[x[1] for x in strategies], xlim=(0, 402),
            xticks=[0, 100, 200, 300, 400], xlabel="Number of patient records")
    mix.set_ylim(1.50, -.79)
    mix.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=BURGUNDY, label="CKD"),
                        plt.Rectangle((0, 0), 1, 1, fc=TEAL, hatch="///", ec="white", label="Non-CKD")],
               loc="upper right", bbox_to_anchor=(1, 1.04), ncol=2, handlelength=1.2, fontsize=12)
    for ax in (fields, mix):
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    save(fig, "cohort_selection.pdf", "Overall missingness and group counts for all and complete records.")


def hemoglobin():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    hb = values.loc[values.feature.eq("hemo")]
    series = [
        ("Available", hb.observed.dropna(), INK, "-"),
        ("Complete", hb.loc[hb.complete_case, "observed"], BURGUNDY, (0, (5, 2))),
        ("Imputed", hb.imputed, TEAL, (0, (1, 1.35))),
    ]
    fig, ax = plt.subplots(figsize=(8.4, 4.8), layout="constrained")
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
    ax.set(ylim=(-.025, 1.03), yticks=[0, .25, .5, .75, 1],
           xlabel="Hemoglobin (UCI source units)", ylabel="Share at or below value")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color=LIGHT, lw=.8)
    ax.legend(loc="upper left", fontsize=12)
    save(fig, "hemoglobin_views.pdf", "Empirical cumulative distributions, each normalized to its own sample size.")


def grade_zero():
    patients = pd.read_csv(PATIENTS)
    grade = measured_grade_zero(patients)
    # Within each result category the cells follow source row order in both panels.
    grade = grade.sort_values(["finding", "row_id"], ascending=[False, True]).reset_index(drop=True)
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.95))
    fig.subplots_adjust(left=.03, right=.97, bottom=.20, top=.78, wspace=.16)
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

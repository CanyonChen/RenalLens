"""Export the three print panels from the published RenalLens result tables.

Run from any directory with the project's Python environment. Each original record
has a one-based row_id. Complete cases have all 24 explanatory fields observed.
No random placement or sampling is used.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "reanalysis" / "tables"
PATIENTS = HERE.parent / "reanalysis" / "clinical_tables" / "patient_measurements.csv"
FIGURES = HERE / "figures"
INK = "#26232C"
BURGUNDY = "#8B1949"
TEAL = "#00675F"
GRAY = "#665F69"
LIGHT = "#E1DDE1"


def save(fig, filename, description):
    fig.savefig(FIGURES / filename, facecolor="white",
                metadata={"Creator": "RenalLens", "Subject": description, "CreationDate": None})
    plt.close(fig)


def cohort():
    rates = pd.read_csv(TABLES / "missingness.csv")
    top = rates.loc[rates.group.eq("all")].nlargest(5, "n_missing")
    labels = {"rbc": "Red cell assessment", "rbcc": "Red cell count",
              "wbcc": "White cell count", "pot": "Potassium", "sod": "Sodium"}
    retention = pd.read_csv(TABLES / "retention.csv").set_index("group")
    fig, (fields, mix) = plt.subplots(2, 1, figsize=(8.4, 6.4), layout="constrained",
                                      gridspec_kw={"height_ratios": [1.5, 1], "hspace": .12})
    fields.set_title("A   Five fields most often missing", loc="left")
    y = np.arange(len(top))
    counts = top.n_missing.to_numpy()
    fields.barh(y, counts, .56, color=GRAY)
    for pos, row in enumerate(top.itertuples()):
        fields.text(row.n_missing + 4, pos, f"{row.n_missing}  ({row.missing_rate:.1%})",
                    va="center", fontsize=12)
    fields.set(yticks=y, yticklabels=[labels[f] for f in top.feature], xticks=[0, 50, 100, 150],
               xlim=(0, 218), xlabel="Records missing the field, out of 400")
    fields.invert_yaxis()

    mix.set_title("B   Who remains after deletion?", loc="left")
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
    mix.set_ylim(1.52, -.52)
    mix.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=BURGUNDY, label="CKD"),
                        plt.Rectangle((0, 0), 1, 1, fc=TEAL, hatch="///", ec="white", label="Non-CKD")],
               loc="lower right", bbox_to_anchor=(1, .85), ncol=2, handlelength=1.2, fontsize=11.5)
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
    grade = patients.loc[patients.al.eq(0)].dropna(subset=["anemia", "high_glucose"]).copy()
    grade["finding"] = grade.anemia.eq(1) | grade.high_glucose.eq(1)
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
        cohort()
        hemoglobin()
        grade_zero()

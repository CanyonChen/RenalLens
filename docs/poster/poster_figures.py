"""Draw the poster's vector panels from the published clinical analysis tables."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


BASE = Path(__file__).resolve().parent
TABLES = BASE.parent / "reanalysis" / "clinical_tables"
DEST = BASE / "figures"
INK = "#292529"
CRIMSON, BURGUNDY, PALE = "#D2133F", "#941344", "#F4D6DF"
GRID, RANGE, NEUTRAL = "#E0DADD", "#797277", "#9E979B"


def chart(height):
    fig, ax = plt.subplots(figsize=(8.0, height), layout="constrained")
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, name):
    fig.savefig(DEST / (name + ".pdf"), metadata={"Creator": "RenalLens", "CreationDate": None})
    plt.close(fig)


def albumin():
    patients = pd.read_csv(TABLES / "patient_measurements.csv")
    grade_zero = (patients.loc[patients.al.eq(0)].dropna(subset=["sc"])
                  .sort_values(["sc", "row_id"]).reset_index(drop=True))
    rank = grade_zero.index + 1
    case_index = grade_zero.index[grade_zero.row_id.eq(43)][0]
    median = grade_zero.sc.median()
    fig, ax = chart(4.40)
    ax.set_yscale("log", base=2)
    ticks = [.5, 1, 2, 4, 8, 16, 32]
    ax.set_yticks(ticks, [str(v) for v in ticks])
    ax.grid(axis="y", color=GRID, lw=.8)
    ax.axhline(median, color=RANGE, lw=1.3, ls="--")
    ax.scatter(rank, grade_zero.sc, s=40, color=RANGE, zorder=3)
    ax.text(len(rank), median * 1.05, f"Median {median:.2f}", ha="right", va="bottom", color=INK, fontsize=14)
    case = grade_zero.iloc[case_index]
    ax.scatter(case_index + 1, case.sc, s=132, marker="D", facecolor=CRIMSON, edgecolor="white", lw=1.0, zorder=4)
    ax.annotate(f"Record 43 · {case.sc:.1f}", (case_index + 1, case.sc), xytext=(6, 4),
                weight="bold", color=BURGUNDY, fontsize=16, ha="left",
                arrowprops={"arrowstyle": "-", "color": BURGUNDY, "lw": 1.4})
    ax.annotate(f"{grade_zero.sc.max():.1f}", (len(rank), grade_zero.sc.max()), xytext=(-7, -1),
                textcoords="offset points", ha="right", va="center", weight="bold", color=INK)
    ax.set(ylim=(.45, 34), xlim=(-.5, len(rank) + 1.5), xticks=[],
           xlabel=f"{len(rank)} grade-0 patients, ordered by creatinine", ylabel="Blood creatinine (mg/dL, log₂ scale)")
    save(fig, "albumin_range")


def hemoglobin():
    pairs = pd.read_csv(TABLES / "patient_measurements.csv").dropna(subset=["sc", "hemo"])
    fit = pd.read_csv(TABLES / "anemia_fit.csv")
    case = pairs.set_index("row_id").loc[43]
    fig, ax = chart(4.40)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.fill_between(fit.sc, fit.ci_low, fit.ci_high, color=PALE)
    ax.scatter(pairs.sc, pairs.hemo, s=29, facecolor="none", edgecolor=RANGE, linewidths=.9)
    ax.plot(fit.sc, fit.mean_hemo, color=CRIMSON, lw=2.8)
    ax.scatter(case.sc, case.hemo, marker="D", s=132, facecolor=CRIMSON, edgecolor="white", zorder=4)
    ax.annotate(f"Record 43 · {case.hemo:.1f}", (case.sc, case.hemo), xytext=(.55, 4.6), color=BURGUNDY,
                weight="bold", fontsize=16, va="center", ha="left",
                arrowprops={"arrowstyle": "-", "color": BURGUNDY, "lw": 1.4},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2})
    last = fit.iloc[-1]
    ax.annotate("Fitted mean", (last.sc, last.mean_hemo), xytext=(70, 10.2),
                ha="right", fontsize=15, weight="bold", color=BURGUNDY,
                arrowprops={"arrowstyle": "-", "color": BURGUNDY, "lw": 1.3})
    ax.set_xscale("log", base=2)
    ticks = [.5, 1, 2, 4, 8, 16, 32, 64]
    ax.set_xticks(ticks, [str(v) for v in ticks])
    ax.set(xlim=(.48,86), xlabel="Blood creatinine (mg/dL, log₂ scale)", ylabel="Hemoglobin (UCI units)")
    save(fig, "hemoglobin_fit")


def overlap():
    patients = pd.read_csv(TABLES / "patient_measurements.csv")
    grade_zero = (patients.loc[patients.al.eq(0)].dropna(subset=["anemia", "high_glucose"])
                  .sort_values(["anemia", "high_glucose", "row_id"]).reset_index(drop=True))
    fig, ax = chart(3.05)
    categories = [
        (0, 0, "o", "white", NEUTRAL, "Neither"),
        (0, 1, "s", PALE, BURGUNDY, "High glucose only"),
        (1, 0, "^", INK, INK, "Anemia only"),
        (1, 1, "D", CRIMSON, CRIMSON, "Both")
    ]
    for k, (anemia, high, marker, fill, edge, label) in enumerate(categories):
        group = grade_zero.loc[grade_zero.anemia.eq(anemia) & grade_zero.high_glucose.eq(high)]
        ax.scatter(group.index % 9, group.index // 9, marker=marker, s=145,
                   facecolor=fill, edgecolor=edge, linewidths=1.5)
        ax.scatter(10.15, k * .98 + .25, marker=marker, s=125, facecolor=fill, edgecolor=edge, linewidths=1.5)
        ax.text(10.8, k * .98 + .25, str(len(group)), ha="left", va="center", fontsize=18, color=INK, weight="bold")
        ax.text(12.05, k * .98 + .25, label, ha="left", va="center", fontsize=16, color=INK)
    case_index = grade_zero.index[grade_zero.row_id.eq(43)][0]
    ax.annotate("Record 43", (case_index % 9, case_index // 9), xytext=(4.6, 5.25),
                ha="center", va="center", fontsize=16, color=BURGUNDY, weight="bold",
                arrowprops={"arrowstyle": "->", "lw": 1.4, "color": BURGUNDY})
    ax.set(xlim=(-.6, 18.0), ylim=(5.74, -.5))
    ax.axis("off")
    save(fig, "overlap_counts")


if __name__ == "__main__":
    DEST.mkdir(exist_ok=True)
    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 16, "axes.labelsize": 15,
        "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 14,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": RANGE,
        "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "legend.frameon": False, "pdf.fonttype": 42, "text.color": INK
    }):
        albumin()
        hemoglobin()
        overlap()

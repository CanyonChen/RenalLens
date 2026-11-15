"""Draw the Case 43 report figures from the measured CKD records and fitted model."""

from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullLocator

REPORT = Path(__file__).resolve().parent
TABLES = REPORT.parent / "reanalysis" / "clinical_tables"
ACCENT = "#941344"
RED = "#D2133F"
INK = "#292529"
GRAY = "#716A70"
GRID = "#E3DFE1"
CASE_ROW = 43


def style_axes(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRAY)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.65)
    ax.set_axisbelow(True)
    ax.tick_params(color=GRAY, length=2.5)


def mark_case(ax, x, y, label, offset):
    ax.scatter(x, y, marker="D", s=29, facecolor=RED, edgecolor="white", linewidth=0.7,
               zorder=5)
    ax.annotate(label, xy=(x, y), xytext=offset, textcoords="offset points",
                fontsize=7.1, color=ACCENT, fontweight="bold", va="center",
                arrowprops={"arrowstyle": "-", "linewidth": 0.85, "color": ACCENT},
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6}, zorder=6)


def set_doubling_axis(axis, ticks):
    axis.set_ticks(ticks, labels=[f"{x:g}" for x in ticks])
    axis.set_minor_locator(NullLocator())


def albumin_creatinine(records):
    paired = records.dropna(subset=["al", "sc"])
    case = paired.loc[CASE_ROW]
    grade = paired.groupby("al").sc
    fig, ax = plt.subplots(figsize=(3.02, 1.82), layout="constrained")
    ax.axhspan(-0.38, 0.38, color="#F9EEF2", zorder=0)
    for level, values in grade:
        color = ACCENT if level == case.al else GRAY
        q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
        ax.hlines(level, values.min(), values.max(), color=color, linewidth=1.1)
        ax.scatter([values.min(), values.max()], [level, level], marker="|",
                   s=27, color=color, linewidths=1)
        ax.hlines(level, q1, q3, color=color, linewidth=4, zorder=2)
        ax.scatter(median, level, marker="|", s=35, color=INK, linewidths=1.7, zorder=3)
    mark_case(ax, case.sc, case.al, "Case 43", (3, 9))
    ax.set_xscale("log", base=2)
    set_doubling_axis(ax.xaxis, [0.5, 1, 2, 4, 8, 16, 32])
    ax.set_xlim(0.45, 36)
    ax.set_ylim(5.45, -1)
    ax.set_yticks(grade.size().index,
                  labels=[f"Grade {int(i)}  (n={n})" for i, n in grade.size().items()])
    ax.set_xlabel("Blood creatinine (mg/dL)")
    style_axes(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return fig


def creatinine_hemoglobin(records):
    paired = records.dropna(subset=["sc", "hemo"])
    fit = pd.read_csv(TABLES / "anemia_fit.csv")
    fig, ax = plt.subplots(figsize=(3.02, 1.82), layout="constrained")
    others = paired.drop(index=CASE_ROW)
    ax.scatter(others.sc, others.hemo, s=7, facecolors="white", edgecolors=GRAY,
               linewidths=0.45, zorder=2)
    ax.fill_between(fit.sc, fit.ci_low, fit.ci_high, color="#F1D4DE", zorder=1)
    ax.plot(fit.sc, fit.mean_hemo, color=ACCENT, linewidth=1.8, zorder=3)
    case = paired.loc[CASE_ROW]
    mark_case(ax, case.sc, case.hemo, "Case 43", (3, -17))
    ax.set_xscale("log", base=2)
    set_doubling_axis(ax.xaxis, [0.5, 1, 2, 4, 8, 16, 32, 64])
    ax.set_xlim(0.43, 91)
    ax.set_xlabel("Blood creatinine (mg/dL)")
    ax.set_ylabel("Hemoglobin (source units)")
    style_axes(ax)
    return fig


def patient_overlap(records):
    complete = records.dropna(subset=["al_positive", "anemia", "high_glucose"])
    grade_zero = complete.loc[complete.al_positive == 0]
    states = [(0, 0), (0, 1), (1, 0), (1, 1)]
    labels = ["Neither finding", "High glucose only", "Anemia only", "Both findings"]
    fig, (ax, overall) = plt.subplots(2, 1, figsize=(5.90, 2.25), layout="constrained",
                                     gridspec_kw={"height_ratios": [1.45, 1]})
    ax.set_title("A   One mark per grade-0 record", loc="left",
                 fontsize=8.8, fontweight="bold")
    row_labels = []
    for row, ((anemia, high_glucose), label) in enumerate(zip(states, labels)):
        members = grade_zero.loc[(grade_zero.anemia == anemia) &
                                 (grade_zero.high_glucose == high_glucose)].sort_index(ascending=False)
        # Patient rows determine the order, so each mark maps to a unique source record.
        x = np.arange(1, len(members) + 1)
        row_labels.append(f"{label}  ({len(members)})")
        other_positions = x[members.index != CASE_ROW]
        ax.scatter(other_positions, [row] * len(other_positions), s=20,
                   facecolor="#7F777E", edgecolor=GRAY,
                   linewidth=0.45)
        if CASE_ROW in members.index:
            pos = members.index.get_loc(CASE_ROW) + 1
            ax.scatter(pos, row, marker="D", s=27, facecolor=RED, edgecolor=ACCENT,
                       linewidth=0.6, zorder=3)
            ax.annotate("Case 43", xy=(pos, row), xytext=(5.8, row), va="center",
                        fontsize=7.6, fontweight="bold", color=ACCENT,
                        arrowprops={"arrowstyle": "-", "color": ACCENT, "linewidth": 0.8})
    ax.set_yticks(range(len(row_labels)), labels=row_labels)
    ax.set_ylim(3.65, -0.65)
    ax.set_xlim(0, 30)
    ax.spines[:].set_visible(False)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    overall.set_title("B   Two or more findings across all grades", loc="left",
                      fontsize=8.8, fontweight="bold")
    observed = 100 * (complete.min_signals >= 2).mean()
    lower = 100 * (records.min_signals >= 2).mean()
    upper = 100 * (records.max_signals >= 2).mean()
    overall.scatter(observed, 1, marker="o", facecolor="white", edgecolor=INK,
                    linewidth=1.4, s=35, zorder=3)
    overall.text(observed + 3, 1, f"{observed:.1f}%", va="center", fontsize=7.6)
    overall.hlines(0, lower, upper, color=GRAY, linewidth=3)
    overall.scatter([lower, upper], [0, 0], marker="|", color=GRAY, s=85)
    overall.text(upper + 2, 0, f"{lower:.1f}–{upper:.1f}%", va="center", fontsize=7.6)
    overall.set_yticks([0, 1], ["All 250 records", "175 with all three results"])
    overall.set_ylim(-0.5, 1.5)
    overall.set_xlim(0, 100)
    overall.set_xlabel("Share of records with two or three findings (%)")
    style_axes(overall, grid_axis="x")
    overall.spines["left"].set_visible(False)
    overall.tick_params(axis="y", length=0)
    return fig


def main():
    records = pd.read_csv(TABLES / "patient_measurements.csv").set_index("row_id")
    output = REPORT / "figures"
    output.mkdir(exist_ok=True)
    style = {"font.size": 7.7, "font.family": "DejaVu Sans", "text.color": INK,
             "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
             "axes.linewidth": 0.65, "pdf.fonttype": 42}
    charts = [
        (albumin_creatinine, "Blood creatinine across urine albumin grades"),
        (creatinine_hemoglobin, "Hemoglobin across blood creatinine measurements"),
        (patient_overlap, "Anemia and high glucose among grade-0 records"),
    ]
    with mpl.rc_context(style):
        for chart, title in charts:
            fig = chart(records)
            fig.savefig(output / f"{chart.__name__}.pdf",
                        metadata={"Title": title, "CreationDate": None})
            plt.close(fig)


if __name__ == "__main__":
    main()

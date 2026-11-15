"""Draw the cohort report figures from the CKD measurements and fitted model."""

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
INK = "#292529"
GRAY = "#716A70"
GRID = "#E3DFE1"


def style_axes(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRAY)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.65)
    ax.set_axisbelow(True)
    ax.tick_params(color=GRAY, length=2.5)


def set_doubling_axis(axis, ticks):
    axis.set_ticks(ticks, labels=[f"{x:g}" for x in ticks])
    axis.set_minor_locator(NullLocator())


def albumin_creatinine(records):
    paired = records.dropna(subset=["al", "sc"])
    grade = paired.groupby("al").sc
    fig, ax = plt.subplots(figsize=(3.02, 1.76), layout="constrained")
    ax.axhspan(-0.38, 0.38, color="#F9EEF2", zorder=0)
    for level, values in grade:
        color = ACCENT if level == 0 else GRAY
        q1, median, q3 = values.quantile([0.25, 0.5, 0.75])
        ax.hlines(level, values.min(), values.max(), color=color, linewidth=1.1)
        ax.scatter([values.min(), values.max()], [level, level], marker="|",
                   s=27, color=color, linewidths=1)
        ax.hlines(level, q1, q3, color=color, linewidth=4, zorder=2)
        ax.scatter(median, level, marker="|", s=35, color=INK, linewidths=1.7, zorder=3)
    ax.set_xscale("log", base=2)
    set_doubling_axis(ax.xaxis, [0.5, 1, 2, 4, 8, 16, 32])
    ax.set_xlim(0.45, 36)
    ax.set_ylim(5.45, -0.5)
    ax.set_yticks(grade.size().index,
                  labels=[f"Grade {int(i)}  (n={n})" for i, n in grade.size().items()])
    ax.set_xlabel(r"Serum creatinine (mg/dL, $\log_2$ scale)")
    style_axes(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return fig


def creatinine_hemoglobin(records):
    paired = records.dropna(subset=["sc", "hemo"])
    fit = pd.read_csv(TABLES / "anemia_fit.csv")
    fig, ax = plt.subplots(figsize=(3.02, 1.80), layout="constrained")
    ax.scatter(paired.sc, paired.hemo, s=7, facecolors="white", edgecolors=GRAY,
               linewidths=0.45, zorder=2)
    ax.fill_between(fit.sc, fit.ci_low, fit.ci_high, color="#F1D4DE", zorder=1)
    ax.plot(fit.sc, fit.mean_hemo, color=ACCENT, linewidth=1.8, zorder=3)
    ax.set_xscale("log", base=2)
    set_doubling_axis(ax.xaxis, [0.5, 1, 2, 4, 8, 16, 32, 64])
    ax.set_xlim(0.43, 91)
    ax.set_yticks([3, 6, 9, 12, 15])
    ax.set_xlabel(r"Serum creatinine (mg/dL, $\log_2$ scale)")
    ax.set_ylabel("Hemoglobin (source units)")
    style_axes(ax)
    return fig


def patient_overlap(records):
    complete = records.dropna(subset=["al_positive", "anemia", "high_glucose"])
    states = [(0, 0), (0, 1), (1, 0), (1, 1)]
    labels = ["Neither finding", "High glucose only", "Anemia only", "Both findings"]
    counts = pd.crosstab([complete.anemia, complete.high_glucose], complete.al_positive)
    counts = counts.reindex(index=states, columns=[0, 1], fill_value=0)
    totals = counts.sum()
    shares = counts.div(totals)

    fig = plt.figure(figsize=(3.02, 2.87))
    title = {"fontsize": 8.4, "fontweight": "bold", "va": "top"}
    fig.text(0.015, 0.99, "A   Anemia and glucose by albumin grade", **title)
    ax = fig.add_axes([0.38, 0.48, 0.60, 0.32])
    shades = mpl.colors.LinearSegmentedColormap.from_list("burgundy", ["#FCF8F9", "#C788A0"])
    ax.imshow(shares, cmap=shades, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for row in range(len(states)):
        for col in range(len(totals)):
            ax.text(col, row, f"{counts.iat[row, col]} ({shares.iat[row, col]:.1%})",
                    ha="center", va="center", fontsize=7.8)
    ax.set_xticks([0, 1], [f"Grade 0\n(n={totals[0]})", f"Grades 1–5\n(n={totals[1]})"])
    ax.set_yticks(range(len(labels)), labels)
    ax.xaxis.tick_top()
    ax.set_xticks([0.5], minor=True)
    ax.set_yticks(np.arange(0.5, len(labels) - 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.3)
    ax.tick_params(which="both", length=0)
    ax.spines[:].set_visible(False)

    fig.text(0.015, 0.42, "B   Records with at least two findings", **title)
    overall = fig.add_axes([0.28, 0.14, 0.67, 0.20])
    observed = 100 * (complete.min_signals >= 2).mean()
    lower = 100 * (records.min_signals >= 2).mean()
    upper = 100 * (records.max_signals >= 2).mean()
    overall.scatter(observed, 1, facecolor=ACCENT, edgecolor=ACCENT, s=21, zorder=3)
    overall.text(observed + 3, 1, f"{observed:.1f}%", va="center", fontsize=7.6)
    overall.hlines(0, lower, upper, color=GRAY, linewidth=3)
    overall.scatter([lower, upper], [0, 0], marker="|", color=GRAY, s=55)
    overall.text(upper + 4, 0, f"{lower:.1f}–{upper:.1f}%", va="center", fontsize=7.5)
    overall.set_yticks([0, 1], [f"Full cohort\n(n={len(records)})", f"All 3 known\n(n={len(complete)})"])
    overall.set_ylim(-0.6, 1.6)
    overall.set_xlim(0, 100)
    overall.set_xticks([0, 25, 50, 75, 100])
    overall.set_xlabel("Share of records (%)")
    style_axes(overall, grid_axis="x")
    overall.spines["left"].set_visible(False)
    overall.tick_params(axis="y", length=0)
    return fig


def main():
    records = pd.read_csv(TABLES / "patient_measurements.csv")
    output = REPORT / "figures"
    output.mkdir(exist_ok=True)
    style = {"font.size": 7.7, "font.family": "DejaVu Sans", "text.color": INK,
             "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
             "axes.linewidth": 0.65, "pdf.fonttype": 42}
    charts = [
        (albumin_creatinine, "Serum creatinine across urine albumin grades"),
        (creatinine_hemoglobin, "Hemoglobin across serum creatinine measurements"),
        (patient_overlap, "Anemia and high glucose by urine albumin grade and full-cohort bounds"),
    ]
    with mpl.rc_context(style):
        for chart, title in charts:
            fig = chart(records)
            fig.savefig(output / f"{chart.__name__}.pdf",
                        metadata={"Title": title, "CreationDate": None})
            plt.close(fig)


if __name__ == "__main__":
    main()

"""Render vector figures for the one-page CKD report using the published analysis tables."""
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


REPORT = Path(__file__).resolve().parent
TABLES = REPORT.parent / "reanalysis" / "tables"
BURGUNDY, TEAL, INK = "#941344", "#156368", "#27242A"
GRID = "#DAD7DA"


def composition():
    counts = pd.read_csv(TABLES / "retention.csv").set_index("group")
    fig, ax = plt.subplots(figsize=(2.95, 1.00))
    fig.subplots_adjust(left=.29, right=.985, top=.95, bottom=.05)
    for y, key, label in [(1, "n_total", "All records"), (0, "n_complete", "Complete")]:
        n = counts[key].sum()
        offset = 0
        for name, group, color in [("CKD", "ckd", BURGUNDY), ("Non-CKD", "notckd", "#ECE8EB")]:
            count = counts.at[group, key]
            fraction = count / n
            ax.barh(y, fraction, left=offset, height=.70, color=color, edgecolor=INK, linewidth=.5)
            ax.text(offset + fraction / 2, y, f"{name}\n{count}", va="center", ha="center",
                    fontsize=7, color="white" if group == "ckd" else INK)
            offset += fraction
        ax.text(-.035, y, f"{label}\n(n={n})", va="center", ha="right", fontsize=7.1)
    ax.set(xlim=(0, 1), ylim=(-.5, 1.5))
    ax.axis("off")
    return fig


def hemoglobin(values):
    hb = values[values.feature.eq("hemo")]
    fig, ax = plt.subplots(figsize=(2.95, 1.76))
    fig.subplots_adjust(left=.20, right=.98, bottom=.24, top=.96)
    series = [
        ("Available", hb.observed.dropna(), INK, "-"),
        ("Complete", hb.loc[hb.complete_case, "observed"], BURGUNDY, "--"),
        ("Imputed", hb.imputed, TEAL, ":"),
    ]
    for label, data, color, linestyle in series:
        unique, counts = np.unique(data, return_counts=True)
        ax.step(np.r_[unique[0], unique], np.r_[0, counts.cumsum()/len(data)], where="post",
                lw=1.5, color=color, linestyle=linestyle, label=f"{label} ({len(data)})")
    median = hb.observed.median()
    at_median = hb.observed.isna()
    low = hb.imputed.lt(median - 1e-6).mean()
    high = hb.imputed.le(median + 1e-6).mean()
    ax.annotate(f"{at_median.sum()} filled\nat {median:.2f}", (median, (low + high)/2),
                xytext=(14.35, .24), ha="left", va="center", color=TEAL, fontsize=7.1,
                arrowprops={"arrowstyle": "-", "lw": .65, "color": TEAL})
    ax.set(xlabel="Hemoglobin (UCI source units)", ylabel="Cumulative share",
           xlim=(2.5, 18.5), xticks=[4, 8, 12, 16], ylim=(-.015, 1.04), yticks=[0, .5, 1])
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color=GRID, lw=.5)
    ax.legend(loc="upper left", frameon=False, fontsize=6.5, handlelength=2, borderpad=0)
    return fig


def glucose(values):
    ckd = values[values.feature.eq("bgr") & values.group.eq("ckd")]
    groups = [(ckd.observed.dropna(), "o", INK), (ckd.loc[ckd.complete_case, "observed"], "s", BURGUNDY),
              (ckd.imputed, "D", TEAL)]
    fig, ax = plt.subplots(figsize=(2.95, 1.48))
    fig.subplots_adjust(left=.27, right=.98, top=.96, bottom=.31)
    for y, (readings, marker, color) in zip([3, 2, 1], groups, strict=True):
        high = readings.ge(200).sum()
        pct = 100 * high / len(readings)
        ax.plot(pct, y, marker=marker, ms=5, color=color)
        ax.annotate(f"{high}/{len(readings)}", (pct, y), xytext=(5, 0),
                    textcoords="offset points", va="center", fontsize=7)
    high = ckd.observed.ge(200).sum()
    missing = ckd.observed.isna().sum()
    bounds = 100 * np.array([high, high + missing]) / len(ckd)
    ax.hlines(0, *bounds, color=INK, linewidth=1.6)
    ax.plot(bounds, [0, 0], "|", color=INK, markersize=7)
    ax.set(xlim=(0, 61), xticks=[0, 20, 40, 60], ylim=(-.5, 3.5),
           yticks=[3, 2, 1, 0], yticklabels=["Available", "Complete", "Imputed", "All possible"],
           xlabel="Share with random glucose ≥200 mg/dL")
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=.5)
    return fig


def main():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    style = {"font.family": "DejaVu Sans", "font.size": 7.4, "pdf.fonttype": 42,
             "axes.linewidth": .55, "axes.axisbelow": True, "axes.spines.top": False,
             "axes.spines.right": False, "text.color": INK, "axes.labelcolor": INK}
    charts = [
        ("sample_composition", composition, (), "Diagnosis counts among all and complete records", "retention.csv"),
        ("hemoglobin_ecdf", hemoglobin, (values,), "Hemoglobin distributions by missing-data rule", "measurement_values.csv"),
        ("glucose_threshold", glucose, (values,), "High glucose by rule and bounds for all CKD records", "measurement_values.csv"),
    ]
    with mpl.rc_context(style):
        for name, draw, args, title, source in charts:
            figure = draw(*args)
            figure.savefig(REPORT / "figures" / f"{name}.pdf", facecolor="white",
                           metadata={"Title": title, "Subject": f"UCI CKD | docs/reanalysis/tables/{source}",
                                     "CreationDate": None})
            plt.close(figure)


if __name__ == "__main__":
    main()

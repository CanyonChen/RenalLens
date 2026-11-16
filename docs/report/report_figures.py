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
    counts = pd.read_csv(TABLES / "eligibility_rules.csv").set_index(["rule", "group"])
    fig, ax = plt.subplots(figsize=(2.95, 1.22))
    fig.subplots_adjust(left=.29, right=.985, top=.95, bottom=.05)
    for y, rule, label in [(2, None, "All records"), (1, "core5", "5 markers"), (0, "all24", "24 fields")]:
        n = 400 if rule is None else int(counts.at[(rule, "all"), "n_retained"])
        offset = 0
        for name, group, color in [("CKD", "ckd", BURGUNDY), ("Non-CKD", "notckd", "#ECE8EB")]:
            count = int(counts.at[("all24", group), "n_original_group"] if rule is None else counts.at[(rule, group), "n_retained"])
            fraction = count / n
            ax.barh(y, fraction, left=offset, height=.70, color=color, edgecolor=INK, linewidth=.5)
            ax.text(offset + fraction / 2, y, f"{name}\n{count}", va="center", ha="center",
                    fontsize=7, color="white" if group == "ckd" else INK)
            offset += fraction
        ax.text(-.035, y, f"{label}\n(n={n})", va="center", ha="right", fontsize=7.1)
    ax.set(xlim=(0, 1), ylim=(-.5, 2.5))
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
    measured = ckd.observed.dropna()
    known_high = measured.ge(200).sum()
    unknown = len(ckd) - len(measured)
    low, high = 100 * np.array([known_high, known_high + unknown]) / len(ckd)
    groups = [
        ("Available", measured, "o", INK),
        ("Complete", ckd.loc[ckd.complete_case, "observed"], "s", BURGUNDY),
        ("Imputed", ckd.imputed, "D", TEAL),
    ]

    fig, ax = plt.subplots(figsize=(3.45, 1.48))
    fig.subplots_adjust(left=.375, right=.957, top=.79, bottom=.29)
    fig.text(.02, .92, f"Shaded range in all {len(ckd)} CKD records: {low:.1f}%–{high:.1f}%",
             va="center", fontsize=7.4, color="#804209")
    ax.axvspan(low, high, color="#FBEDDC", zorder=0)
    ax.vlines([low, high], -.45, 2.45, colors="#9A5516", linestyles=":", lw=.8)
    labels = []
    for y, (name, readings, marker, color) in zip([2, 1, 0], groups, strict=True):
        count = readings.ge(200).sum()
        share = 100 * count / len(readings)
        labels.append(f"{name} ({count}/{len(readings)})")
        ax.plot(share, y, marker=marker, ms=4.8, color=color,
                markerfacecolor="white" if name == "Imputed" else color, zorder=3)
        ax.text(.995, y, f"{share:.1f}%", transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=7.4, fontweight="bold", color=color)

    ax.set(xlim=(0, 60), xticks=[0, 20, 40, 60], ylim=(-.45, 2.45),
           yticks=[2, 1, 0], yticklabels=labels,
           xlabel="Share with random glucose ≥200 mg/dL")
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.tick_params(axis="y", length=0, labelsize=7.4)
    ax.tick_params(axis="x", length=2, pad=2)
    ax.xaxis.labelpad = 2
    ax.spines["left"].set_visible(False)
    return fig


def renal_coefficients():
    rows = pd.read_csv(TABLES / "renal_correlations.csv").query("group == 'all'").set_index("view")
    methods = [
        ("observed", "Available", "o", INK),
        ("complete_case", "Complete", "s", BURGUNDY),
        ("imputed", "Imputed", "D", TEAL),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(3.55, 1.50), sharey=True)
    fig.subplots_adjust(left=.245, right=.978, bottom=.15, top=.84, wspace=.25)
    for axis, metric, title in zip(axes, ["pearson", "spearman"], ["Pearson r", "Spearman ρ"], strict=True):
        axis.set_title(title, fontsize=8.2, fontweight="bold", pad=3)
        axis.set(xlim=(0, 1), xticks=[0, .5, 1], xticklabels=["0", "0.5", "1"], ylim=(-.38, 2.65))
        axis.grid(axis="x", linewidth=.45, color=GRID)
        axis.spines["left"].set_visible(False)
        axis.tick_params(axis="x", length=2, pad=2)
        axis.tick_params(axis="y", length=0, pad=4)
        for y, (key, _, marker, color) in zip([2, 1, 0], methods, strict=True):
            row = rows.loc[key]
            value = row[metric]
            lower, upper = row[[f"{metric}_ci_low", f"{metric}_ci_high"]]
            if pd.notna(lower) and pd.notna(upper):
                axis.hlines(y, lower, upper, color=color, linewidth=.9)
                axis.vlines([lower, upper], y-.09, y+.09, color=color, linewidth=.8)
            axis.plot(value, y, marker=marker, markersize=4, color=color, zorder=3,
                      markerfacecolor="white" if key == "imputed" else color)
            axis.annotate(f"{value:.3f}", (value, y), xytext=(0, 3), textcoords="offset points",
                          ha="center", va="bottom", fontsize=7.3, color=color)
    labels = [f"{name}\nn = {int(rows.at[key, 'n_pairs'])}" for key, name, _, _ in methods]
    axes[0].set_yticks([2, 1, 0], labels, fontsize=7.3)
    return fig


def main():
    values = pd.read_csv(TABLES / "measurement_values.csv")
    style = {"font.family": "DejaVu Sans", "font.size": 7.4, "pdf.fonttype": 42,
             "axes.linewidth": .55, "axes.axisbelow": True, "axes.spines.top": False,
             "axes.spines.right": False, "text.color": INK, "axes.labelcolor": INK}
    charts = [
        ("sample_composition", composition, (), "Diagnosis counts among all, five-marker and all-24-field complete records", "eligibility_rules.csv"),
        ("hemoglobin_ecdf", hemoglobin, (values,), "Hemoglobin distributions by missing-data rule", "measurement_values.csv"),
        ("glucose_threshold", glucose, (values,), "High glucose by rule and bounds for all CKD records", "measurement_values.csv"),
        ("renal_coefficients", renal_coefficients, (), "Creatinine and blood urea: estimated correlations and 95% bootstrap intervals", "renal_correlations.csv"),
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

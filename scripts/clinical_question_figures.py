"""Create the four case-led clinical figures from the observed CKD tables."""

import argparse
import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator
from reanalysis_figures import DPI, ROOT

INK = "#282329"
MUTED = "#615961"
RED = "#BA1748"
WINE = "#87113C"
PINK = "#F7DCE4"
GRID = "#E5DFE2"
GRAY = "#817780"
CASE = 43
STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "svg.fonttype": "none",
    "svg.hashsalt": "RenalLens-record-43",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
}


def figure_notes(title, alt, caption, *source_tables):
    return {
        "title": title,
        "alt": alt,
        "caption": caption,
        "sources": [f"../clinical_tables/{table}.csv" for table in source_tables],
    }


def records(tables_dir):
    return pd.read_csv(tables_dir / "patient_measurements.csv").set_index("row_id")


def page(topic, title, subtitle):
    fig = plt.figure(figsize=(10.8, 5.85))
    fig.text(0.047, 0.923, topic.upper(), color=WINE, size=9, weight="bold")
    fig.text(0.045, 0.834, title, size=22, weight="bold")
    fig.text(0.047, 0.767, subtitle, size=11.2, color=MUTED)
    fig.add_artist(
        Line2D([0.047, 0.956], [0.722, 0.722], transform=fig.transFigure, color=GRID, linewidth=1)
    )
    return fig


def axes(fig, rect):
    ax = fig.add_axes(rect)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(length=0, pad=7)
    ax.set_axisbelow(True)
    return ax


def foot(fig, first, second):
    fig.add_artist(
        Line2D(
            [0.047, 0.956], [0.155, 0.155], transform=fig.transFigure, color=GRID, linewidth=0.85
        )
    )
    fig.text(0.047, 0.101, first, size=10.1, weight="bold")
    fig.text(0.047, 0.052, second, size=9.1, color=MUTED)


def doubling(ax, ticks, lo, hi):
    ax.set_xscale("log", base=2)
    ax.set_xlim(lo, hi)
    ax.set_xticks(ticks, labels=[f"{v:g}" for v in ticks])
    ax.xaxis.set_minor_locator(NullLocator())


def case_mark(ax, x, y):
    ax.scatter(x, y, s=96, facecolors="white", edgecolors=WINE, lw=1.9, zorder=7)
    ax.scatter(x, y, s=25, marker="D", color=RED, zorder=8)


def side(fig, label, value, detail, top=0.666):
    fig.text(0.725, top, label, fontsize=10, color=MUTED, weight="bold", va="top")
    fig.text(0.72, top - 0.064, value, fontsize=27, color=WINE, weight="bold", va="top")
    fig.text(0.725, top - 0.162, detail, fontsize=10.3, linespacing=1.48, va="top")


def albumin_creatinine(tables_dir):
    pairs = records(tables_dir).dropna(subset=["al", "sc"])
    grades = (
        pd.read_csv(tables_dir / "albumin_grades.csv")
        .query("view == 'observed'")
        .set_index("grade")
    )
    association = (
        pd.read_csv(tables_dir / "albumin_association.csv")
        .query("view == 'observed' and sample == 'all_grades'")
        .iloc[0]
    )
    title = "One urine grade, a wide range of creatinine"
    fig = page(
        "Kidney markers",
        title,
        "Each circle is a measured patient. "
        "The short vertical line marks the median within each grade.",
    )
    ax = axes(fig, [0.165, 0.294, 0.486, 0.38])
    doubling(ax, [0.5, 1, 2, 4, 8, 16, 32], 0.43, 39)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.axhspan(-0.48, 0.48, color="#FBEFF3", zorder=0)
    for grade, group in pairs.groupby("al"):
        for creatinine, tied in group.groupby("sc"):
            row_ids = tied.index.sort_values()
            offsets = np.linspace(-0.22, 0.22, len(row_ids)) if len(row_ids) > 1 else [0.0]
            for row_id, offset in zip(row_ids, offsets):
                ax.scatter(creatinine, grade + offset, s=18, fc="white", ec=GRAY, lw=0.75, zorder=2)
                if row_id == CASE:
                    case_mark(ax, creatinine, grade + offset)
        ax.plot(
            grades.loc[grade, "median"], grade, marker="|", color=WINE, ms=15, mew=2.25, zorder=5
        )
    ax.set_ylim(5.45, -0.5)
    ax.set_yticks(
        grades.index,
        labels=[f"Grade {grade}   ·   {int(count)}" for grade, count in grades.n_pairs.items()],
    )
    ax.set_xlabel("Serum creatinine (mg/dL, doubling scale)", labelpad=8)
    grade_zero = grades.loc[0]
    side(
        fig,
        "MEASURED AT GRADE 0",
        f"{grade_zero['min']:g}–{grade_zero['max']:g}",
        f"mg/dL across {int(grade_zero.n_pairs)} people.\nThe circled diamond marks\n"
        f"record 43 at {pairs.loc[CASE, 'sc']:.1f} mg/dL.",
    )
    foot(
        fig,
        f"Typical values rose from {grade_zero['median']:.2f} mg/dL at grade 0 "
        f"to {grades.loc[4, 'median']:.2f} at grade 4.",
        f"{len(pairs)} measured pairs. Rank correlation {association.rho:.3f} "
        f"(95% bootstrap interval {association.ci_low:.3f}–{association.ci_high:.3f}). "
        "Grade 5 has one record.",
    )
    return fig, figure_notes(
        title,
        "Six horizontal strips show measured creatinine. The grade-0 strip spans 0.6–24 mg/dL, "
        "including record 43 at 1.0.",
        "Only identical readings are offset vertically. The grade labels show the number of "
        "patients and the scale doubles at each tick.",
        "patient_measurements",
        "albumin_grades",
        "albumin_association",
    )


def creatinine_hemoglobin(tables_dir):
    pairs = records(tables_dir).dropna(subset=["sc", "hemo"])
    fit = pd.read_csv(tables_dir / "anemia_fit.csv")
    model = (
        pd.read_csv(tables_dir / "anemia_association.csv")
        .query("view == 'observed' and sample == 'all_pairs'")
        .iloc[0]
    )
    case = pairs.loc[CASE]
    title = "How much lower was hemoglobin at twice the creatinine?"
    fig = page(
        "Blood and oxygen",
        title,
        f"Hemoglobin carries oxygen in red blood cells. The chart compares {len(pairs)} people "
        "with both blood tests.",
    )
    ax = axes(fig, [0.095, 0.295, 0.56, 0.37])
    doubling(ax, [0.5, 1, 2, 4, 8, 16, 32, 64], 0.45, max(90, pairs.sc.max()))
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.fill_between(fit.sc, fit.ci_low, fit.ci_high, color=PINK)
    ax.scatter(pairs.sc, pairs.hemo, s=17, fc="white", ec=GRAY, lw=0.7)
    ax.plot(fit.sc, fit.mean_hemo, color=WINE, lw=2.2)
    case_mark(ax, case.sc, case.hemo)
    ax.annotate(
        "43",
        (case.sc, case.hemo),
        xytext=(-12, -18),
        textcoords="offset points",
        ha="right",
        fontsize=9,
        weight="bold",
        color=WINE,
        arrowprops={"arrowstyle": "-", "color": WINE},
    )
    ax.set(xlabel="Serum creatinine (mg/dL, doubling scale)", ylabel="Hemoglobin (UCI units)")
    fig.text(0.72, 0.65, "TWO FITTED MEANS", fontsize=9.5, weight="bold", color=MUTED)
    fig.text(0.72, 0.378, "Average difference", fontsize=9.5, weight="bold", color=MUTED)
    side_ax = fig.add_axes([0.73, 0.455, 0.195, 0.12])
    creatinine_levels = (2, 4)
    predictions = [model.intercept + model.slope * np.log2(value) for value in creatinine_levels]
    side_ax.plot([0, 1], predictions, color=WINE, lw=2, marker="o", ms=6)
    for position, (creatinine, prediction) in enumerate(zip(creatinine_levels, predictions)):
        side_ax.annotate(
            f"{prediction:.2f}",
            (position, prediction),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=12,
            weight="bold",
        )
        side_ax.annotate(
            f"{creatinine} mg/dL",
            (position, prediction),
            xytext=(0, -16),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=MUTED,
        )
    side_ax.set(xlim=(-0.18, 1.18), ylim=(min(predictions) - 0.25, max(predictions) + 0.25))
    side_ax.axis("off")
    fig.text(
        0.716, 0.281, f"{model.slope:.2f}".replace("-", "−"), fontsize=27, color=WINE, weight="bold"
    )
    foot(
        fig,
        f"Record 43 had creatinine {case.sc:.1f} mg/dL, hemoglobin {case.hemo:.1f} "
        "and anemia recorded in the chart.",
        f"Pink band: 95% interval for the fitted mean. Per doubling: {model.slope:.2f} UCI units "
        f"(95% HC3 interval {model.ci_low:.2f} to {model.ci_high:.2f}).",
    )
    return fig, figure_notes(
        title,
        "The fitted hemoglobin is 0.90 source units lower at twice the creatinine; "
        "the right-hand graphic compares predictions at 2 and 4 mg/dL.",
        "All original measured pairs are shown, including the highest creatinine value. "
        "The line joining predicted means is a model contrast across patients.",
        "patient_measurements",
        "anemia_fit",
        "anemia_association",
    )


def hyperglycemia(tables_dir):
    patients = records(tables_dir)
    measured = patients.dropna(subset=["bgr", "dm"])
    by_history = (
        pd.read_csv(tables_dir / "glucose_threshold.csv")
        .query("view == 'observed'")
        .set_index("dm")
    )
    title = "What did the blood test add to the diabetes history?"
    fig = page(
        "Random blood glucose",
        title,
        "Each mark is one measured blood glucose. Pink shading begins at the study threshold "
        "of 200 mg/dL.",
    )
    ax = axes(fig, [0.13, 0.3, 0.515, 0.36])
    right = max(510, measured.bgr.max() + 15)
    ax.axvspan(200, right, color="#FBEFF3")
    ax.axvline(200, color=WINE, lw=1.3, ls="--")
    # Place nearby readings in alternating vertical lanes, preserving their measured x positions.
    lane_order = [0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6]
    for group_y, history in [(1, "no"), (0, "yes")]:
        group = measured.loc[measured.dm.eq(history)].sort_values(["bgr", "row_id"])
        last_glucose = dict.fromkeys(lane_order, -np.inf)
        for row in group.itertuples():
            available = (lane for lane in lane_order if row.bgr - last_glucose[lane] >= 5)
            lane = next(available, min(last_glucose, key=last_glucose.get))
            last_glucose[lane] = row.bgr
            mark_y = group_y + lane * 0.059
            ax.plot(
                row.bgr,
                mark_y,
                ls="none",
                marker="|",
                ms=6,
                mew=1.25,
                color=RED if row.bgr >= 200 else GRAY,
            )
            if row.Index == CASE:
                case_mark(ax, row.bgr, mark_y)
                ax.annotate(
                    f"43 · {row.bgr:g}",
                    (row.bgr, mark_y),
                    xytext=(20, 27),
                    textcoords="offset points",
                    color=WINE,
                    weight="bold",
                    fontsize=9,
                    arrowprops={"arrowstyle": "-", "color": WINE},
                )
    ax.set(
        xlim=(0, right),
        ylim=(-0.52, 1.65),
        yticks=[0, 1],
        yticklabels=["History: yes", "History: no"],
        xlabel="Random glucose (mg/dL)",
    )
    ax.set_xticks([0, 100, 200, 300, 400, 500])
    ax.grid(axis="x", color=GRID, lw=0.65)
    for y, history, label in [
        (0.65, "no", "NO DIABETES HISTORY"),
        (0.423, "yes", "DIABETES HISTORY"),
    ]:
        group_stats = by_history.loc[history]
        fig.text(0.71, y, label, fontsize=9.2, color=MUTED, weight="bold")
        fig.text(
            0.706,
            y - 0.095,
            f"{int(group_stats.n_high)} / {int(group_stats.n_measured)}",
            fontsize=25,
            color=WINE,
            weight="bold",
        )
        fig.text(
            0.71,
            y - 0.151,
            f"{group_stats.proportion:.1%}  ·  95% CI "
            f"{group_stats.ci_low:.1%}–{group_stats.ci_high:.1%}",
            fontsize=9.1,
        )
    without_history, with_history = by_history.loc["no"], by_history.loc["yes"]
    foot(
        fig,
        f"Record 43 measured {patients.loc[CASE, 'bgr']:g} mg/dL "
        "with diabetes history recorded as no.",
        f"Glucose was missing in {int(without_history.n_missing)} of {int(without_history.n_group)} "
        f"without and {int(with_history.n_missing)} of {int(with_history.n_group)} "
        "with diabetes history. Intervals use the Wilson method.",
    )
    return fig, figure_notes(
        title,
        "Two strips show measured glucose. Record 43 is just above 200 mg/dL in the no-history "
        "group; 11/87 in that group and 61/125 with diabetes history reached 200.",
        "Measurements are positioned on the same linear scale. Vertical offsets separate "
        "neighboring marks. Shading denotes the study threshold, not a new diagnosis. "
        "Whole-group missing-data bounds are in the linked table.",
        "patient_measurements",
        "glucose_threshold",
    )


def patient_overlap(tables_dir):
    patients = records(tables_dir)
    complete = patients.dropna(subset=["al", "anemia", "high_glucose"])
    grade_zero = complete.loc[complete.al.eq(0)].sort_values(["anemia", "high_glucose", "row_id"])
    summary = pd.read_csv(tables_dir / "overlap_summary.csv").iloc[0]
    title = "What else was found at urine albumin grade 0?"
    fig = page(
        "Back to record 43",
        title,
        f"One mark per person. All {len(grade_zero)} had grade 0 and known results for both "
        "anemia and random glucose.",
    )
    ax = fig.add_axes([0.043, 0.239, 0.58, 0.442])
    ax.set_aspect("equal")
    styles = {
        (0, 0): ("o", "white", GRAY, "Neither finding"),
        (0, 1): ("s", PINK, WINE, "High glucose only"),
        (1, 0): ("^", INK, INK, "Anemia only"),
        (1, 1): ("D", RED, WINE, "Both findings"),
    }
    ncols = 9
    for i, row in enumerate(grade_zero.itertuples()):
        x, y = i % ncols, i // ncols
        marker, color, edge, _ = styles[(row.anemia, row.high_glucose)]
        ax.scatter(x, y, marker=marker, s=119, fc=color, ec=edge, lw=1.4)
        if row.Index == CASE:
            ax.scatter(x, y, s=374, fc="none", ec=INK, lw=1.5)
            ax.annotate(
                "43",
                (x, y),
                xytext=(0, -21),
                textcoords="offset points",
                ha="center",
                weight="bold",
                size=9,
            )
    ax.set(xlim=(-0.64, ncols - 0.36), ylim=((len(grade_zero) - 1) // ncols + 0.78, -0.6))
    ax.axis("off")
    legend = fig.add_axes([0.604, 0.275, 0.35, 0.40])
    legend.set(xlim=(0, 1), ylim=(-0.55, 3.55))
    legend.axis("off")
    for i, ((anemia, high_glucose), (marker, color, edge, label)) in enumerate(styles.items()):
        count = int((grade_zero.anemia.eq(anemia) & grade_zero.high_glucose.eq(high_glucose)).sum())
        y = 3 - i
        legend.scatter(0.06, y, marker=marker, s=88, fc=color, ec=edge, lw=1.4)
        legend.text(0.16, y, label, fontsize=12, va="center")
        legend.text(
            0.94,
            y,
            str(count),
            fontsize=16,
            weight="bold",
            ha="right",
            va="center",
            color=WINE if anemia or high_glucose else MUTED,
        )
    foot(
        fig,
        f"{int(summary.n_no_albumin_other_complete)} of {len(grade_zero)} had anemia or high "
        "glucose. Record 43 was one of the two who had both.",
        f"Across all grades, {int(summary.n_at_least_two_complete)}/{len(complete)} had at least "
        "two findings. With missing values, the full-cohort bounds are "
        f"{int(summary.n_definite_at_least_two)}–{int(summary.n_possible_at_least_two)} "
        f"of {len(patients)}.",
    )
    return fig, figure_notes(
        title,
        "A matrix of 45 grade-zero records shows 29 with neither finding, 12 with high glucose "
        "alone, two with anemia alone and two with both. A ring marks record 43.",
        "Each position corresponds to a source row, ordered by anemia, high glucose and then "
        "source row. Shapes and fills identify categories. The ring around a diamond "
        "indicates record 43.",
        "patient_measurements",
        "overlap_patterns",
        "overlap_summary",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=ROOT / "docs/reanalysis/clinical_tables")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "docs/reanalysis/clinical_figures"
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    notes = {}
    with mpl.rc_context(STYLE):
        for build in (albumin_creatinine, creatinine_hemoglobin, hyperglycemia, patient_overlap):
            name = build.__name__
            fig, info = build(args.tables_dir)
            width, height = fig.get_size_inches() * 25.4
            info.update(width_mm=round(width, 2), height_mm=round(height, 2), dpi=DPI)
            metadata = {"Title": info["title"], "Description": info["alt"]}
            fig.savefig(args.output_dir / f"{name}.svg", metadata={**metadata, "Date": None})
            fig.savefig(args.output_dir / f"{name}.png", dpi=DPI, metadata=metadata)
            plt.close(fig)
            notes[name] = info
    (args.output_dir / "figure_notes.json").write_text(
        json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

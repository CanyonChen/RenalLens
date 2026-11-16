"""Build the offline eight-slide missing-data presentation from published CSVs.

Run from the repository root:
    python scripts/build_presentation.py
    python scripts/build_presentation.py --render

Rendering requires the project's Playwright npm dependency and local Chrome.
The clinical companion remains in docs/presentation/case-study.html.
"""

from __future__ import annotations

import argparse
import csv
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import sys
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "docs/reanalysis/tables"
OUT = ROOT / "docs/presentation"
INK, MUTED, BURGUNDY, TEAL, GRID = "#231F20", "#595457", "#941344", "#167D8D", "#D4CDD0"
FEATURE_LABELS = {"hemo": "Hemoglobin", "sc": "Creatinine", "bu": "Blood urea", "bgr": "Glucose", "bp": "Blood pressure"}


def read_table(name):
    with (TABLES / f"{name}.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def select(rows, **criteria):
    return next(row for row in rows if all(row[key] == str(value) for key, value in criteria.items()))


def number(row, key):
    return float(row[key])


def integer(row, key):
    return int(float(row[key]))


def percent(value, digits=1):
    return f"{value * 100:.{digits}f}%"


def text(x, y, value, size=26, anchor="start", fill=INK, weight=400):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{weight}">{escape(str(value))}</text>'


def line(x1, y1, x2, y2, color=GRID, width=2, dash=""):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}"/>'


def rect(x, y, width, height, color):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" height="{height:.2f}" fill="{color}"/>'


def circle(x, y, color, radius=5, opacity=1):
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{color}" opacity="{opacity}"/>'


def svg(content, width, height, label):
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label, quote=True)}">{content}</svg>'


def eligibility_chart(eligibility):
    output = ""
    x, scale = 245, 2.05
    for tick in range(0, 401, 100):
        output += line(x + tick * scale, 105, x + tick * scale, 438)
        output += text(x + tick * scale, 480, tick, 25, "middle", MUTED)
    for y, rule, label in [(165, "all24", "All 24 fields"), (355, "core5", "Core 5 fields")]:
        all_row = select(eligibility, rule=rule, group="all")
        ckd = integer(select(eligibility, rule=rule, group="ckd"), "n_retained")
        other = integer(select(eligibility, rule=rule, group="notckd"), "n_retained")
        output += text(213, y + 38, label, 29, "end", INK, 600)
        output += rect(x, y, 400 * scale, 62, "#E7E1E3")
        output += rect(x, y, ckd * scale, 62, BURGUNDY)
        output += rect(x + ckd * scale, y, other * scale, 62, TEAL)
        output += text(x + ckd * scale / 2, y + 41, ckd, 29, "middle", "#fff", 600)
        output += text(x + (ckd + other / 2) * scale, y + 41, other, 29, "middle", "#fff", 600)
        output += text(x, y - 20, f'{integer(all_row, "n_retained")} retained = {ckd} CKD + {other} non-CKD', 28, "start", INK, 600)
    output += text(655, 527, "Records out of the same 400", 26, "middle", MUTED)
    output += rect(263, 566, 24, 24, BURGUNDY) + text(299, 587, "CKD", 26)
    output += rect(453, 566, 24, 24, TEAL) + text(489, 587, "Non-CKD", 26)
    output += rect(731, 566, 24, 24, "#E7E1E3") + text(767, 587, "Excluded", 26)
    return svg(output, 1130, 620, "Retained CKD and non-CKD records under the all-24 and core-five eligibility rules")


def median_chart(shifts):
    output = text(67, 33, "Median creatinine (mg/dL)", 28, weight=600)
    y = lambda value: 458 - value / 5 * 370
    for value in range(6):
        output += line(90, y(value), 1005, y(value)) + text(74, y(value) + 8, value, 24, "end", MUTED)
    for group, x0, x1, title, color in [("all", 240, 430, "Overall", TEAL), ("ckd", 695, 885, "Within CKD", BURGUNDY)]:
        row = select(shifts, group=group, feature="sc")
        observed, complete = number(row, "median_observed"), number(row, "median_complete")
        output += line(x0, y(observed), x1, y(complete), color, 7)
        for x, value, count_key in [(x0, observed, "n_observed"), (x1, complete, "n_complete")]:
            output += circle(x, y(value), color, 10)
            output += text(x, y(value) - 24, f"{value:.2f}", 40, "middle", color, 600)
            output += text(x, 504, "Observed" if x == x0 else "All-24", 26, "middle")
            output += text(x, 540, f'n = {integer(row, count_key)}', 24, "middle", MUTED)
        output += text((x0 + x1) / 2, 597, title, 31, "middle", color, 600)
    return svg(output, 1100, 630, "Overall creatinine median decreases while the median within CKD increases after all-24 complete-case selection")


def ecdf_chart(measurements, fill):
    hemo = [row for row in measurements if row["feature"] == "hemo"]
    observed = sorted(float(row["observed"]) for row in hemo if row["observed"])
    imputed = sorted(float(row["imputed"]) for row in hemo)
    x = lambda value: 105 + (value - 3) / 15 * 890
    y = lambda value: 494 - value * 400
    output = text(105, 35, "Cumulative share of records", 28, weight=600)
    for tick in [0, .25, .5, .75, 1]:
        output += line(105, y(tick), 995, y(tick)) + text(88, y(tick) + 8, percent(tick, 0), 23, "end", MUTED)
    for tick in [3, 6, 9, 12, 15, 18]:
        output += text(x(tick), 536, tick, 24, "middle", MUTED)
    for values, color in [(observed, TEAL), (imputed, BURGUNDY)]:
        commands = [f"M{x(3)},{y(0)}"]
        for i, value in enumerate(values, 1):
            commands.append(f"H{x(value):.2f}V{y(i / len(values)):.2f}")
        commands.append(f"H{x(18):.2f}")
        output += f'<path d="{" ".join(commands)}" fill="none" stroke="{color}" stroke-width="4"/>'
    before = sum(v < fill for v in imputed) / len(imputed)
    after = sum(v <= fill for v in imputed) / len(imputed)
    output += line(x(fill), y(0), x(fill), y(1), BURGUNDY, 2, "7 6")
    output += line(x(fill) + 18, y(before), x(fill) + 18, y(after), BURGUNDY, 7)
    output += text(x(fill) + 35, y((before + after) / 2) + 8, f"{fill:.2f}", 29, fill=BURGUNDY, weight=600)
    output += text(550, 594, "Hemoglobin (g, UCI units)", 27, "middle", MUTED)
    output += line(160, 640, 212, 640, TEAL, 5) + text(228, 649, f"Observed (n = {len(observed)})", 25)
    output += line(640, 640, 692, 640, BURGUNDY, 5) + text(708, 649, f"Imputed (n = {len(imputed)})", 25)
    return svg(output, 1100, 680, "Empirical cumulative distributions of hemoglobin before and after median imputation")


def renal_chart(measurements, correlations):
    patients = {}
    for row in measurements:
        if row["feature"] in ("sc", "bu"):
            patient = patients.setdefault(row["row_id"], {"group": row["group"], "complete": row["complete_case"] == "True"})
            if row["observed"]:
                patient[row["feature"]] = float(row["observed"])
    pairs = [(rid, row) for rid, row in patients.items() if "sc" in row and "bu" in row]
    output = ""
    for col, view, title in [(0, "observed", "Observed pairs"), (1, "complete_case", "All-24 complete cases")]:
        left, top = 100 + col * 825, 83
        x = lambda value: left + value / 80 * 655
        y = lambda value: top + 380 - value / 400 * 380
        row = select(correlations, view=view, group="all")
        output += text(left, 39, f'{title}  (n = {integer(row, "n_pairs")})', 31, weight=600)
        for tick in [0, 100, 200, 300, 400]:
            output += line(left, y(tick), left + 655, y(tick)) + text(left - 18, y(tick) + 8, tick, 23, "end", MUTED)
        for tick in [0, 20, 40, 60, 80]:
            output += text(x(tick), 502, tick, 24, "middle", MUTED)
        for rid, patient in pairs:
            if view == "complete_case" and not patient["complete"]:
                continue
            output += circle(x(patient["sc"]), y(patient["bu"]), BURGUNDY if patient["group"] == "ckd" else TEAL, 5.7, .7)
            if patient["sc"] > 40:
                output += text(x(patient["sc"]) - 8, y(patient["bu"]) - 13, f"#{rid}", 23, "end", BURGUNDY, 600)
        output += text(left + 330, 547, "Creatinine (mg/dL)", 25, "middle", MUTED)
        output += text(left, 605, f'Pearson {number(row, "pearson"):.3f}', 37, fill=BURGUNDY, weight=600)
        output += text(left + 358, 605, f'Spearman {number(row, "spearman"):.3f}', 37, fill=TEAL, weight=600)
    output += text(23, 75, "Blood urea (mg/dL)", 24, fill=MUTED)
    return svg(output, 1700, 640, "Creatinine versus blood urea in observed pairs and all-24 complete cases, colored by diagnosis")


def pca_chart(loadings, variance):
    output = ""
    for col, scale, label, color in [(0, "raw", "Raw measurement units", BURGUNDY), (1, "zscore", "Z scores", TEAL)]:
        offset = col * 835
        center = offset + 420
        x = lambda value: center + value * 250
        v1 = select(variance, scale=scale, component="PC1")
        v2 = select(variance, scale=scale, component="PC2")
        output += text(offset + 20, 41, label, 34, weight=600)
        output += text(offset + 20, 91, f'PC1: {percent(number(v1, "explained_fraction"))} variance', 30, fill=color, weight=600)
        output += text(offset + 20, 135, f'PC1 + PC2: {percent(number(v2, "cumulative_fraction"))}', 26, fill=MUTED)
        for tick in [-1, -.5, 0, .5, 1]:
            output += line(x(tick), 183, x(tick), 536, GRID if tick else MUTED, 2)
            output += text(x(tick), 580, f"{tick:g}", 23, "middle", MUTED)
        for i, feature in enumerate(FEATURE_LABELS):
            row = select(loadings, scale=scale, component="PC1", feature=feature)
            value = number(row, "eigenvector_weight")
            y = 222 + i * 70
            output += text(offset + 10, y + 9, FEATURE_LABELS[feature], 25)
            output += line(x(0), y, x(value), y, color, 8)
            output += circle(x(value), y, color, 9)
            output += text(x(value) + (18 if value >= 0 else -18), y + 9, f"{value:+.3f}", 26, "start" if value >= 0 else "end", color, 600)
        output += text(offset + 420, 631, "Signed PC1 coefficient", 26, "middle", MUTED)
    return svg(output, 1700, 670, "Signed eigenvector coefficients for the first principal component with raw units and z-score standardization")


CSS = """
:root {--bg:#F7F6F6;--ink:#231F20;--muted:#595457;--line:#D4CDD0;--accent:#941344;--dark:#941344;--tint:#F7D9E1;font-family:"Helvetica Neue",Arial,sans-serif;color:var(--ink)}
*{box-sizing:border-box}html,body{height:100%;padding:0;margin:0;overflow:hidden;background:var(--bg)}
#stage{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform:translate(-50%,-50%);transform-origin:center}
.slide{display:none;position:absolute;inset:0;background:var(--bg);padding:84px 118px 58px;overflow:hidden}.slide.active{display:flex;flex-direction:column}
.school-logo{position:absolute;top:24px;right:118px;width:196px;height:auto;display:block}.kicker{font-size:23px;letter-spacing:2.5px;color:var(--muted);text-transform:uppercase;padding-right:228px;font-weight:650}
h1,h2,h3,p,dl,dd{margin:0}h1,h2{letter-spacing:-3.6px;line-height:1.06;font-weight:650}h1{font-size:92px}h2{font-size:72px;margin:37px 0 12px}.sub{font-size:32px;line-height:1.3;color:var(--muted);max-width:1640px}
.cover{background:#fff}.opening{flex:1;display:grid;grid-template-columns:1.2fr 1fr;align-items:center;gap:95px}.opening h1{font-size:85px;line-height:1.07}.opening h1 span{color:var(--accent)}.case-question{font-size:35px;line-height:1.3;color:var(--muted);margin-top:35px}
.case-card{padding:35px 42px;background:var(--bg);border-top:7px solid var(--accent)}.record-id{font-size:28px;letter-spacing:1.5px;text-transform:uppercase;color:var(--dark);font-weight:650}.case-card h3{font-size:46px;line-height:1.13;letter-spacing:-1.1px;margin:19px 0 28px}.case-card dl div{display:flex;justify-content:space-between;align-items:baseline;gap:20px;border-top:2px solid var(--line);padding:20px 0 5px;margin-top:10px}.case-card dt{font-size:27px;color:var(--muted)}.case-card dd{font-size:33px;font-weight:650;white-space:nowrap}.case-hint{margin-top:24px;font-size:26px;color:var(--muted);line-height:1.35}
.source{font-size:22px;line-height:1.35;color:var(--muted);margin-top:auto}.authors{font-size:25px;color:var(--muted);line-height:1.4}.layout{display:grid;grid-template-columns:1.78fr 1fr;gap:62px;align-items:center;flex:1;min-height:0;margin:15px 0}.chart{min-width:0}svg{width:100%;display:block;overflow:visible}svg text{font-family:"Helvetica Neue",Arial,sans-serif}
.value{font-size:91px;line-height:1.06;letter-spacing:-4px;color:var(--accent);font-weight:650;margin:12px 0}.aside{font-size:36px;line-height:1.28;letter-spacing:-.6px}.small{font-size:27px;line-height:1.36;color:var(--muted);margin-top:24px}.guide{margin:auto 0}.guide-row{display:grid;grid-template-columns:385px 1fr;gap:46px;border-top:2px solid var(--line);padding:29px 0;align-items:baseline}.guide-row:last-child{border-bottom:2px solid var(--line)}.guide-row h3{font-size:37px;line-height:1.12;letter-spacing:-1px;color:var(--dark)}.guide-row p{font-size:31px;line-height:1.38}.guide-row strong{font-weight:650}.wide-chart{margin:auto 0 5px}.wide-chart svg{height:600px}.chart-note{font-size:27px;line-height:1.34;color:var(--muted);margin:8px 0 16px}.chart-note strong{color:var(--ink)}
.ending{background:var(--dark);color:#fff;--muted:#F8E6ED}.ending h2{font-size:91px;margin-top:45px}.ending .school-logo{filter:brightness(0) invert(1)}.conclusion{margin:auto 0}.conclusion p{border-top:2px solid #DC9AAF;padding:24px 0;font-size:35px;line-height:1.3}.conclusion strong{color:#fff}.return-case{font-size:33px;line-height:1.35;color:#F8E6ED;margin:28px 0 34px}.explorer-link{color:#fff;display:inline-block;font-size:29px;text-decoration:none;border-bottom:2px solid #F8E6ED;padding-bottom:7px;align-self:flex-start}.ending .source{margin-top:26px}
#menu{display:none;position:fixed;left:16px;top:64px;background:#fff;box-shadow:0 12px 44px #2223;padding:14px;border-radius:12px;color:var(--ink);max-height:80vh;overflow:auto}#menu.open{display:grid}button{font:inherit;color:inherit;cursor:pointer}#menu button{border:0;background:#fff;text-align:left;padding:10px 16px;font-size:16px}#menu button[aria-current=true]{background:var(--tint);color:var(--dark)}#nav{position:fixed;top:0;left:0;opacity:0;padding:12px 15px;transition:opacity .18s}#nav:hover,#nav:focus-within,#nav.open{opacity:1}#nav button{padding:5px 10px;background:#fff;border:1px solid #DBD2D5;border-radius:6px;font-size:20px}#counter{display:none;position:fixed;bottom:15px;right:19px;background:var(--dark);color:white;padding:8px 12px;border-radius:10px;font-size:15px}
@page{size:1920px 1080px;margin:0}@media print{html,body{width:1920px;height:auto;overflow:visible}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}#stage{position:static;width:1920px;height:auto;transform:none!important}.slide,.slide.active{display:flex;flex-direction:column;position:relative;inset:auto;width:1920px;height:1080px;page-break-after:always;break-after:page}.slide:last-child{break-after:auto;page-break-after:auto}#nav,#menu,#counter{display:none!important}}
"""


def build():
    companion = OUT / "case-study.html"
    if not companion.exists():
        raise FileNotFoundError("Preserve the original clinical deck as docs/presentation/case-study.html first.")
    original = companion.read_text(encoding="utf-8")
    logo = re.search(r'<img class="school-logo"[^>]+>', original).group()
    navigation = original[original.index("const slides=Array.from"):original.rindex("</script>")]
    navigation = navigation.replace('if(menu.classList.contains("open"))toggleMenu(false);else show', 'if(e.target.closest("a,button"))return;if(menu.classList.contains("open"))toggleMenu(false);else show')
    measurements = read_table("measurement_values")
    shifts = read_table("median_shifts")
    correlations = read_table("renal_correlations")
    variance = read_table("pca_variance")
    loadings = read_table("pca_loadings")
    diagnostics = read_table("diagnostics")
    mixture = read_table("mixture_standardization")
    influence = read_table("diagnostics_renal_influence")
    if (TABLES / "eligibility_rules.csv").exists():
        eligibility = read_table("eligibility_rules")
    else:
        import pandas as pd
        from data_preprocess import clean_column
        from eligibility import compare_rules
        raw = pd.read_csv(ROOT / "data/raw/ckd.csv", dtype="string", na_filter=False)
        raw.index = pd.RangeIndex(1, len(raw) + 1, name="row_id")
        cleaned = pd.DataFrame({name: clean_column(raw[name])[0] for name in raw}, index=raw.index)
        eligibility = [{key: str(value) for key, value in row.items()} for row in compare_rules(cleaned).to_dict("records")]
    with (ROOT / "data/raw/ckd.csv").open(encoding="utf-8-sig", newline="") as stream:
        raw_records = list(csv.DictReader(stream))
    patient = {key: value.strip() for key, value in raw_records[42].items()}
    missing = [key for key, value in patient.items() if key != "class" and value.lower() in ("", "?", "nan", "na", "n/a")]
    glucose = float(patient["bgr"])
    all24 = select(eligibility, rule="all24", group="all")
    core5 = select(eligibility, rule="core5", group="all")
    hb = select(diagnostics, feature="hemo", group="all")
    fill = number(hb, "median")
    sc_mix = select(mixture, feature="sc")
    most_influential = max(influence, key=lambda row: abs(number(row, "pearson_change")))
    observed_pair = select(correlations, group="all", view="observed")
    ckd_observed = select(correlations, group="ckd", view="observed")
    ckd_complete = select(correlations, group="ckd", view="complete_case")
    non_observed = select(correlations, group="notckd", view="observed")
    non_complete = select(correlations, group="notckd", view="complete_case")
    sources = "Source: published project tables in docs/reanalysis/tables. UCI CKD, DOI 10.24432/C5G020."
    sections = []

    def slide(title, body, source, classes="", kicker="RenalLens · Missing-data sensitivity"):
        sections.append(f'<section class="slide {classes}" data-title="{escape(title, quote=True)}">{logo}<p class="kicker">{escape(kicker)}</p>{body}<p class="source">{source}</p></section>')

    slide("One missing field, one excluded record", f'''<div class="opening"><div><h1>One missing field<br>removes a measured<br><span>glucose result</span></h1><p class="case-question">How does handling missing data change the clinical picture in the same 400 records?</p></div><div class="case-card"><p class="record-id">Record 43 · CKD</p><h3>{24 - len(missing)} of 24 fields observed</h3><dl><div><dt>Random glucose</dt><dd>{glucose:g} mg/dL</dd></div><div><dt>Missing field</dt><dd>{escape(', '.join(missing))}</dd></div><div><dt>All-24 rule</dt><dd>Excluded</dd></div></dl><p class="case-hint">The glucose result is measured. The missing red-blood-cell field triggers the exclusion.</p></div></div><p class="authors">How Missing Data Shape the Clinical Picture of Chronic Kidney Disease</p>''', "Source: original UCI CSV, one-based record 43. rbc = red blood cells.", "cover", "City University of Hong Kong · RenalLens")
    slide("Three rules, different denominators", f'''<h2>Three rules, different denominators</h2><p class="sub">The explanatory fields define eligibility. The diagnosis label never fills a missing value.</p><div class="guide"><div class="guide-row"><h3>Observed measurements</h3><p>Use recorded values for each question.<br><strong>Hemoglobin n = {integer(hb, 'n_measured')}, creatinine n = {integer(select(diagnostics, feature='sc', group='all'), 'n_measured')}, renal pairs n = {integer(observed_pair, 'n_pairs')}.</strong></p></div><div class="guide-row"><h3>Complete cases</h3><p>Require all 24 explanatory fields to be present.<br><strong>{integer(all24, 'n_retained')} of {len(raw_records)} records remain.</strong> We also test a core-five eligibility rule.</p></div><div class="guide-row"><h3>Median + mode fill</h3><p>Fill numerical gaps with global medians and categorical gaps with modes.<br><strong>All {len(raw_records)} records remain. Filled cells retain their provenance.</strong></p></div></div>''', "Sources: diagnostics.csv, renal_correlations.csv, eligibility_rules.csv. Core five: hemoglobin, creatinine, blood urea, glucose, blood pressure.")
    added = integer(core5, "n_retained") - integer(all24, "n_retained")
    ckd24, ckd5 = select(eligibility, rule="all24", group="ckd"), select(eligibility, rule="core5", group="ckd")
    slide("Eligibility changes the retained cohort", f'''<h2>Eligibility changes the retained cohort</h2><p class="sub">Both rules use observed values. Only the required fields change.</p><div class="layout"><div class="chart">{eligibility_chart(eligibility)}</div><div><p class="value">+{added}</p><p class="aside">records remain when eligibility uses the five measurements.</p><p class="small">CKD retention rises from <strong>{percent(number(ckd24, 'retention'))}</strong> to <strong>{percent(number(ckd5, 'retention'))}</strong>.</p><p class="small">Record 43 enters the core-five cohort because all five measurements are present.</p></div></div>''', "Source: eligibility_rules.csv. All 24 includes rbc. Core five includes hemo, sc, bu, bgr and bp. Each bar starts with the same 400 records.")
    slide("The creatinine shift reverses within CKD", f'''<h2>The creatinine shift reverses within CKD</h2><p class="sub">The overall median and the median within CKD move in opposite directions.</p><div class="layout"><div class="chart">{median_chart(shifts)}</div><div><p class="aside">The all-24 cohort changes who contributes to the summary.</p><p class="small">Among observed creatinine values, <strong>{percent(number(sc_mix, 'ckd_share_observed'))}</strong> come from CKD records.</p><p class="small">After all-24 selection, that share is <strong>{percent(number(sc_mix, 'ckd_share_complete'))}</strong>. The retained CKD records have higher creatinine.</p></div></div>''', "Sources: median_shifts.csv, mixture_standardization.csv. Observed creatinine denominators differ from the full-cohort diagnosis counts.")
    slide("Median filling creates a visible concentration", f'''<h2>Median filling creates a visible concentration</h2><p class="sub">Hemoglobin ECDFs show where the replacement values accumulate.</p><div class="layout"><div class="chart">{ecdf_chart(measurements, fill)}</div><div><p class="value">{integer(hb, 'n_missing')} / {len(raw_records)}</p><p class="aside">hemoglobin values take the same replacement value, <strong>{fill:.2f}</strong>.</p><p class="small">That creates a <strong>{percent(integer(hb, 'n_missing') / len(raw_records))}</strong> jump in the filled ECDF.</p><p class="small">The extra mass comes from the filling rule. The observed values stay unchanged.</p></div></div>''', "Sources: measurement_values.csv, diagnostics.csv. ECDF = empirical cumulative distribution. Hemoglobin units follow UCI's gms label.")
    slide("Pearson rises while rank correlation falls", f'''<h2>Pearson rises while rank correlation falls</h2><p class="sub">The same renal pair tells a different story under all-24 selection.</p><div class="wide-chart">{renal_chart(measurements, correlations)}</div><p class="chart-note"><strong style="color:{BURGUNDY}">CKD</strong> and <strong style="color:{TEAL}">non-CKD</strong> mix changes. Within CKD, Pearson is {number(ckd_observed, 'pearson'):.3f} then {number(ckd_complete, 'pearson'):.3f}. Within non-CKD, it is {number(non_observed, 'pearson'):.3f} then {number(non_complete, 'pearson'):.3f}.<br>Extreme-value sensitivity: omitting observed record {integer(most_influential, 'omitted_row_id')} changes Pearson from {number(most_influential, 'pearson_all'):.3f} to {number(most_influential, 'pearson_after_omission'):.3f}.</p>''', "Sources: measurement_values.csv, renal_correlations.csv, diagnostics_renal_influence.csv. Raw axes retain every measured extreme.")
    slide("Scaling changes the first principal component", f'''<h2>Scaling changes the first principal component</h2><p class="sub">PCA uses the same {len(raw_records)} filled records and five measurements in both views.</p><div class="wide-chart">{pca_chart(loadings, variance)}</div><p class="chart-note">Raw PC1 mainly follows glucose. Standardization gives creatinine and blood urea more weight, with hemoglobin in the opposite direction.</p>''', "Sources: pca_loadings.csv (eigenvector_weight), pca_variance.csv. Signs follow the published orientation. An entire PCA axis can reverse sign.")
    slide("Back to record 43", f'''<h2>Back to record 43</h2><p class="return-case">Glucose <strong>{glucose:g} mg/dL</strong> is observed. Only <strong>{escape(', '.join(missing))}</strong> is missing.<br>The all-24 rule excludes this record. The core-five rule retains it.</p><div class="conclusion"><p><strong>Eligibility selects people.</strong> The retained cohort changes the overall clinical summary.</p><p><strong>Filling changes distributions.</strong> The hemoglobin ECDF exposes the repeated median.</p><p><strong>Statistics and scale change the picture.</strong> Pearson, ranks and PCA emphasize different structure.</p></div><a class="explorer-link" href="../results/figures/cohort.html?patient=43&amp;feature=bgr&amp;view=complete_case">Open the cohort explorer at record 43 ↗</a>''', sources, "ending")
    nav_html = '<div id="nav"><button aria-label="Previous slide" id="prev">‹</button> <button aria-label="Slide list" id="list">☰</button> <button aria-label="Next slide" id="next">›</button></div><div id="menu" aria-label="Slide list"></div><div id="counter"></div>'
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>RenalLens: How Missing Data Shape the Clinical Picture of Chronic Kidney Disease</title><style>' + CSS + '</style></head><body><main id="stage">' + "\n".join(sections) + '</main>' + nav_html + '<script>"use strict";\n' + navigation + '</script></body></html>\n'
    (OUT / "deck.html").write_text(html, encoding="utf-8")
    notes = f'''# RenalLens: How Missing Data Shape the Clinical Picture of Chronic Kidney Disease

Eight slides, approximately seven minutes. The main presentation compares missing-data rules in the 400-record UCI CKD dataset. The earlier clinical companion is preserved as [case-study.html](case-study.html), with [its original notes](Case_study_notes.md).

## 1. One missing field, one excluded record (0:45)

Record 43 has a measured random glucose of {glucose:g} mg/dL and a CKD diagnosis. It has {24 - len(missing)} of 24 explanatory fields recorded. Only {', '.join(missing)} is missing. The all-24 complete-case rule removes the entire record, including that observed glucose result. Ask the audience what information a requirement for every field could remove. The project compares how those choices change the picture of the same 400 records. Record identifiers count from one after the CSV header. Source: original `data/raw/ckd.csv`.

## 2. Three rules, different denominators (0:55)

Observed measurements use the available values for each question, so the sample size depends on the feature or pair. Hemoglobin has {integer(hb, 'n_measured')} observed values, creatinine has {integer(select(diagnostics, feature='sc', group='all'), 'n_measured')}, and the renal pair has {integer(observed_pair, 'n_pairs')}. Complete cases require all 24 explanatory features and retain {integer(all24, 'n_retained')} records. Median and mode filling retains all 400 records. Numerical fields use the global observed median, categorical fields use the mode, and diagnosis never supplies the fill. Filled cells keep a provenance flag. The five displayed measurements are hemoglobin, creatinine, blood urea, glucose and blood pressure. Sources: `diagnostics.csv`, `renal_correlations.csv`, `eligibility_rules.csv` and the preprocessing rule.

## 3. Eligibility changes the retained cohort (0:55)

The bars start from the same 400 records. All-24 retains {integer(all24, 'n_retained')} records: {integer(ckd24, 'n_retained')} CKD plus {integer(select(eligibility, rule='all24', group='notckd'), 'n_retained')} non-CKD. Requiring only the five measurements retains {integer(core5, 'n_retained')}: {integer(ckd5, 'n_retained')} CKD plus {integer(select(eligibility, rule='core5', group='notckd'), 'n_retained')} non-CKD. This is a change in eligibility, with no imputation. CKD retention changes from {percent(number(ckd24, 'retention'))} to {percent(number(ckd5, 'retention'))}. Record 43 has all five measurements, so it enters the core-five cohort. Source: `eligibility_rules.csv`.

## 4. The creatinine shift reverses within CKD (0:55)

Across all measured creatinine values, the median is {number(select(shifts, group='all', feature='sc'), 'median_observed'):.2f} mg/dL. The all-24 median is {number(select(shifts, group='all', feature='sc'), 'median_complete'):.2f}. Within CKD, the median instead rises from {number(select(shifts, group='ckd', feature='sc'), 'median_observed'):.2f} to {number(select(shifts, group='ckd', feature='sc'), 'median_complete'):.2f}. The group mix and the retained patients within each group both change. The CKD share among measured creatinine values falls from {percent(number(sc_mix, 'ckd_share_observed'))} to {percent(number(sc_mix, 'ckd_share_complete'))}. Read the plotted denominators aloud: they are the actual samples behind these medians. Sources: `median_shifts.csv`, `mixture_standardization.csv`.

## 5. Median filling creates a visible concentration (0:55)

The ECDF is the share at or below each hemoglobin value. The teal curve uses {integer(hb, 'n_measured')} measured values. The burgundy curve uses all 400 records after filling. All {integer(hb, 'n_missing')} missing hemoglobin values receive {fill:.2f}, the observed global median. That produces a {percent(integer(hb, 'n_missing') / len(raw_records))} jump at that value. The observed values stay unchanged. Filling keeps records in the analysis while imposing a visible distributional feature. UCI describes hemoglobin as gms without a volume denominator. Sources: `measurement_values.csv`, `diagnostics.csv`.

## 6. Pearson rises while rank correlation falls (1:00)

The raw axes show all renal pairs, including the extremes. Pearson compares linear co-variation on the numerical scale, while Spearman compares ranks. Overall Pearson rises from {number(observed_pair, 'pearson'):.3f} to {number(select(correlations, group='all', view='complete_case'), 'pearson'):.3f}, but Spearman falls from {number(observed_pair, 'spearman'):.3f} to {number(select(correlations, group='all', view='complete_case'), 'spearman'):.3f}. The retained cohort has a different diagnosis mix and extreme values influence the raw covariance. The within-group Pearson figures and leave-one-record calculation on the slide show why one overall coefficient is an incomplete description. Omitting observed record {integer(most_influential, 'omitted_row_id')} changes Pearson to {number(most_influential, 'pearson_after_omission'):.3f}. This sensitivity calculation describes the observed pairs, rather than a deletion recommendation. Sources: `measurement_values.csv`, `renal_correlations.csv`, `diagnostics_renal_influence.csv`.

## 7. Scaling changes the first principal component (0:55)

Both PCAs use the same 400 filled records and five measurements. The chart reports signed eigenvector coefficients, specifically `eigenvector_weight`, rather than scaled loadings. With raw units, glucose dominates PC1. With z scores, blood urea and creatinine have larger positive coefficients and hemoglobin has a negative coefficient. Read PC1 and cumulative PC1-plus-PC2 explained variance from the chart. A whole component can change sign without changing the PCA geometry. Relative signs are what show opposing feature directions. Sources: `pca_loadings.csv`, `pca_variance.csv`.

## 8. Back to record 43 (0:40)

Return to the observed {glucose:g} mg/dL glucose value. One unrelated missing field removes it under all-24 selection, whereas core-five eligibility keeps it. State the three conclusions on the slide: eligibility selects people, filling changes distributions, and the statistic and scale change the picture. Open the linked cohort explorer to show record 43, glucose and the complete-case view together.

## Playback and reproduction

Open `deck.html` locally. Arrow keys or Space advance, G opens the slide list, F opens full screen, C toggles the counter, and 1-8 jump directly. The HTML embeds the CityU logo and all plotted SVG data, with no remote dependencies. The final link is relative to the repository and opens `../results/figures/cohort.html?patient=43&feature=bgr&view=complete_case`.

Run `python scripts/build_presentation.py` from the repository root to regenerate the HTML and these notes from the published CSVs. Use `python scripts/build_presentation.py --render` to export the PDF, the contact sheet `preview.png`, eight full-size screenshots and a browser-check JSON record under `outputs/presentation/`. Rendering uses local Chrome and the project's Playwright dependency. Override the executable with `--chrome` or the `CHROME` environment variable.
'''
    (OUT / "Presenter_notes.md").write_text(notes, encoding="utf-8")
    print(f"Built {OUT / 'deck.html'} with {len(sections)} slides from published CSVs.")


RENDER_JS = r"""
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async () => {
  const [root, chrome] = process.argv.slice(1);
  const folder = path.join(root, 'docs', 'presentation');
  const out = path.join(root, 'outputs', 'presentation');
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:chrome, headless:true, args:['--allow-file-access-from-files']});
  const page = await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
  const errors=[]; page.on('pageerror', e=>errors.push(String(e)));
  await page.goto(pathToFileURL(path.join(folder,'deck.html')).href);
  await page.evaluate(()=>document.fonts.ready);
  const count=await page.locator('.slide').count();
  if(count!==8)throw Error('Expected eight slides, got '+count);
  const checks=[];
  for(let i=1;i<=count;i++) {
    await page.evaluate(i=>{location.hash='#'+i},i);
    await page.waitForTimeout(60);
    const check=await page.evaluate(()=>{
      const slide=document.querySelector('.slide.active'), box=slide.getBoundingClientRect();
      const outside=[...slide.querySelectorAll('h1,h2,h3,p,dl,svg,a')].filter(el=>{
        const r=el.getBoundingClientRect(); return r.left<box.left-1||r.top<box.top-1||r.right>box.right+1||r.bottom>box.bottom+1;
      }).map(el=>({tag:el.tagName,text:el.textContent.slice(0,90)}));
      return {slide:location.hash,title:slide.dataset.title,scrollHeight:slide.scrollHeight,clientHeight:slide.clientHeight,outside};
    });
    checks.push(check);
    await page.screenshot({path:path.join(out,'slide-'+String(i).padStart(2,'0')+'.png')});
  }
  const link=await page.locator('.explorer-link').getAttribute('href');
  const target=path.resolve(folder,link.split('?')[0]);
  await page.pdf({path:path.join(folder,'RenalLens_Presentation.pdf'),printBackground:true,preferCSSPageSize:true});
  await browser.close();
  const result={slides:count,checks,errors,explorerLink:link,explorerExists:fs.existsSync(target)};
  fs.writeFileSync(path.join(out,'browser-check.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
  if(errors.length||!result.explorerExists||checks.some(c=>c.outside.length||c.scrollHeight>c.clientHeight))process.exitCode=1;
})();
"""


def render(chrome):
    subprocess.run(["node", "-e", RENDER_JS, str(ROOT), chrome], cwd=ROOT, check=True)
    from PIL import Image
    folder = ROOT / "outputs/presentation"
    tile_width, tile_height, gap = 480, 270, 10
    sheet = Image.new("RGB", (4 * tile_width + 5 * gap, 2 * tile_height + 3 * gap), (214, 209, 211))
    for index in range(8):
        with Image.open(folder / f"slide-{index + 1:02d}.png") as image:
            sheet.paste(image.resize((tile_width, tile_height), Image.Resampling.LANCZOS), (gap + index % 4 * (tile_width + gap), gap + index // 4 * (tile_height + gap)))
    sheet.save(OUT / "preview.png")
    try:
        from pypdf import PdfReader
    except ImportError:
        pdfinfo = shutil.which("pdfinfo")
        if pdfinfo:
            details = subprocess.check_output([pdfinfo, str(OUT / "RenalLens_Presentation.pdf")], text=True)
            count = int(re.search(r"^Pages:\s+(\d+)", details, re.MULTILINE).group(1))
            if count != 8:
                raise ValueError(f"Expected eight PDF pages, got {count}")
            print(f"Verified {count} PDF pages with pdfinfo.")
        else:
            print("PDF exported. PDF page counting requires pypdf or pdfinfo.")
    else:
        count = len(PdfReader(OUT / "RenalLens_Presentation.pdf").pages)
        if count != 8:
            raise ValueError(f"Expected eight PDF pages, got {count}")
        print(f"Verified {count} PDF pages.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="Export PDF and browser screenshots with local Chrome")
    parser.add_argument("--chrome", default=os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium") or ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" if sys.platform == "darwin" else r"C:\Program Files\Google\Chrome\Application\chrome.exe"))
    args = parser.parse_args()
    build()
    if args.render:
        render(args.chrome)

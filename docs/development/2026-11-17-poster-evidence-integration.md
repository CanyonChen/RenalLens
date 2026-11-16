# Poster evidence integration implementation plan

The user approved integrating the reviewed poster's stronger evidence on
November 17, 2026. The starting commit is `3824b374c9e2a491162a59dab5531e43db04c250`.
The deliverable stays on `zjj/visualization-integration`.

## Approved design

Keep the short title, CityU/Gemini theme, authors, 132 x 80 cm page and signed
PCA coefficient chart. Put Record 43's six readings in a compact three-row
patient table beside the three processing definitions. Below this entry band,
use three readable columns: selection (cohort comparison and the same 45
patients), filling plus the full-cohort glucose bound, and association plus
scale. Give the five findings numbered headings. The grade-0 point matrix is
the sole main-page display of that subgroup; the nested clinical mini-charts
and duplicate finding-count bars stay off the main poster.

The glucose figure reports the 250-person CKD cohort's 72 high, 38 missing and
140 below-threshold readings, its 28.8%-44.0% logical bounds, and the separately
labelled measured (72/212), complete-case (20/43) and filled (72/250) results.
The bounds are logical limits for the missing readings, distinct from confidence
intervals. The patient matrix preserves row identity and marks Record 43; it
states that 1/45 patients remain and all 16 with a finding are excluded.

## Tasks and acceptance

- [x] Add two source-data regression tests before implementing the preparation
  helpers in `docs/poster/poster_figures.py`. Verify bounds/denominators and
  patient identities/retention, observe the missing-helper failures, implement
  `glucose_bounds_data()` and `grade_zero_data()`, and rerun the poster tests.
- [x] Restore the two figures to the default vector-PDF build, improve their
  labels, and update `docs/poster/main.tex` to the entry-band/five-finding layout.
  Generate the compact case table from the same CSV and keep signed PCA axes.
- [x] Compile with Tectonic, inspect full-page and cropped renders, check page
  bounds, overlap, headings and smallest fonts, then refresh the print PDF and
  `preview.png`. The result must remain one 132 x 80 cm page.
- [x] Refresh `BUILD.md`, `SOURCE_MAP.md` and `VALIDATION.md`; run the full build,
  unit/browser/link checks and offline packaging. Compare all 51 existing CSVs
  and `RenalLensPoster/` against the starting commit. Review the source and
  visual result, commit and push the existing branch, then verify remote HEAD.

## Verification commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_poster_figures.py
.\.venv\Scripts\python.exe docs/poster/poster_figures.py
.\.venv\Scripts\python.exe scripts/build.py --pdf --check --package
git diff --check
git push origin HEAD:refs/heads/zjj/visualization-integration
git ls-remote --heads origin refs/heads/zjj/visualization-integration
```

The one-page A4 report and eight-page presentation retain their prior content.
Generated screenshots, logs and package checks live under
`outputs/poster-integration-2026-11-17/`. The user-supplied PDF remains the review
reference; the repository's editable LaTeX/Python sources produce the revision.

## Verification record

The full build passes 8 Python tests, 3 JavaScript tests and 27 browser checks
with zero page errors; the site checker confirms 110 local links/assets across
7 pages. All 51 existing CSVs match the baseline numerically and JH's archive
is unchanged. The report and presentation text/pixels match their previous
versions, so their original binaries are retained.

The final poster has one 132 x 80 cm page, five evidence headings and a minimum
extracted font size of 20.66 pt. Full-page and four cropped renders were checked;
no overfull boxes, out-of-page text/links or replacement characters remain.
Independent review confirmed source patient identities and denominators and
identified a missing 24-field qualifier in the creatinine paragraph; that
condition was restored before the final compilation. The final poster and
preview are included in the refreshed offline package.

# Poster refinement implementation plan

The user approved the comparison's recommendation on November 16, 2026: keep the missing-data project as the baseline, adopt JH's readable patient panel and threshold scatterplot, and reduce the poster to four main evidence groups. Work stays on `zjj/visualization-integration`.

## Design

Keep the current 132 × 80 cm CityU/Gemini poster, burgundy/teal palette, original authors and data. Use a narrow left column for Record 43, measured glucose by diabetes history and the three processing definitions. Use the two wider columns for four numbered groups: selection, filling, association and scale. Shorten the title, enlarge the main charts and remove the repeated clinical-overlap chart and standalone bounds chart from the main page. Their original data and supplementary analyses remain available in the project.

The case table and glucose points are generated from the published CSVs. Glucose keeps its measured x values and source row IDs; deterministic vertical offsets separate coincident points. The threshold is 200 mg/dL, and every subgroup reports high/measured and unmeasured counts. Record 43 is marked at 204 mg/dL. The existing 24-field baseline and all statistical CSVs remain unchanged.

## Tasks

- [x] Extend `docs/poster/poster_figures.py` with a generated Record 43 table, a measured-glucose scatterplot, a larger standalone cohort comparison and a focused hemoglobin ECDF. Add tests in `tests/test_poster_figures.py` for case values, subgroup denominators and plotted source records.
- [x] Update `docs/poster/main.tex` to the three-column case-plus-four-results layout. Enlarge the signed PCA chart, retain the correlation sensitivity row, and state the creatinine reversal as a concise selection result.
- [x] Generate native vector figures and compile the poster with Tectonic. Inspect full-page and cropped PNGs, PDF page count, clipping, overlap and font sizes; revise the source until it fits cleanly on one page.
- [x] Update source/build/validation documentation, rebuild the offline package, run the numerical and browser checks, compare original tables and the JH archive, review and push the existing branch.

## Commands and acceptance

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe docs/poster/poster_figures.py
.\.venv\Scripts\python.exe scripts/build.py --pdf --check --package
git diff --check
```

The glucose figure contains the 212 measured CKD records: no-history 11/87 high with 26 unmeasured; history 61/125 high with 12 unmeasured. The selected case remains 204 mg/dL and all source observations are preserved. The poster has four numbered evidence headings, one readable patient table and one glucose scatterplot; it remains one 132 × 80 cm page. The report remains one page and the presentation eight pages. All original CSVs and files under `RenalLensPoster/` match the previous branch version.

## Verification record

The full build/check/package command passed six Python tests, three JavaScript
tests and 27 browser checks with zero page errors. The site checker verified 110
local links/assets across seven pages. All 51 original CSVs matched the starting
commit numerically. Report and presentation text/pixels matched their previous
versions; their original binaries were retained. The final poster was recompiled
and rendered after the last typography/text adjustment. Full-page and cropped
inspection confirmed the patient table, denominators, four main charts and
footer fit. `preview.png` is the final rendered review image. Only the existing
feature branch is used for the submission.

# Visualization integration validation

Validated on November 16, 2026 against base commit `b8b7eab3a17cb5863eb0459f3b248c3bfe6a17e2`.

## Results

- All 50 existing CSV tables under `docs/results`, `docs/reanalysis/tables` and `docs/reanalysis/clinical_tables` match the base numerically (`rtol=1e-11`, `atol=1e-12`). The original 24-field analysis is preserved.
- The new eligibility table retains 158 records (43 CKD, 115 non-CKD) under all24, and 300 (165 CKD, 135 non-CKD) under core5.
- Six Python tests pass: eligibility counts/denominators, unchanged measurements and Record 43, invalid field validation, site-build idempotence, poster patient readings, and all measured-glucose source records/subgroup denominators.
- Three JavaScript tests pass: tied-rank Spearman arithmetic, field eligibility and unchanged readings, and interpolated quantiles.
- Twenty-seven real-browser checks pass with zero page errors. They exercise rule switching, Record 43, query restoration, cross-page patient identity, group-specific correlations, scale-invariant coefficients, presets, central heatmap clipping, mobile page width and all eight presentation slides.
- Seven main published pages have 110 valid local links/assets. No unresolved HTML generation markers remain.
- Native LaTeX compilation produces a one-page 132 × 80 cm poster and a one-page A4 report. Chrome produces an eight-page presentation PDF. PDF text extracts without replacement characters, and rendered pages were inspected.
- Repeating the site build leaves homepage/report content unchanged and keeps one shared navigation block per page.

## Commands

```sh
uv run --locked python scripts/build.py --pdf --check --package
uv run --locked python -m unittest discover -s tests
npm test
npm run check:browser
uv run --locked python scripts/check_site.py
git diff --check
```

The local run used Python 3.13.15, Playwright 1.65.1, Chrome and Tectonic 0.17.0. Font setup is documented in `docs/poster/BUILD.md`. Local screenshots and machine-readable checks are written under `outputs/browser-check`, `outputs/presentation` and `outputs/verification`; the offline site package is `outputs/RenalLens-offline.zip`.

The Pages workflow is configured to deploy after a main-branch build. Publishing this feature branch does not activate a Pages deployment.

## Poster refinement, November 16, 2026

The refinement was checked against `3e2eb2162bfed4d3ea4a4e83209f428ebca8a13e`.
All 51 CSV tables match that version numerically with the tolerances above,
including `eligibility_rules.csv`. No files under `RenalLensPoster/` changed.

The current poster has four numbered evidence groups and a generated patient
table. Its glucose figure preserves all 212 measured CKD records and their source
row IDs/x values. Record 43 remains at 204 mg/dL. No-history high/measured is
11/87 with 26 missing; recorded-history high/measured is 61/125 with 12 missing.

The full `scripts/build.py --pdf --check --package` run passed six Python tests,
three JavaScript tests, 27 browser checks with zero page errors, and 110 local
links/assets across seven pages. The final poster was separately recompiled
after the last typography/text adjustment and inspected as a full-page PNG and
patient/glucose and selection-text crops. It is one 132 x 80 cm page, with all
four evidence headings present, no extracted replacement characters and no text
outside the page. `docs/poster/preview.png` renders the final vector PDF.

The rebuilt report is one A4 page and the presentation eight pages. Their text
and rendered pixels match the pre-refinement versions, so their original PDF
binaries are retained. The offline package is refreshed with the final poster
and preview. Local build logs, PDF checks, numerical comparisons and crop images
are under `outputs/poster-refinement/`.

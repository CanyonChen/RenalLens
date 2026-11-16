# Visualization integration validation

Validated on November 16, 2026 against base commit `b8b7eab3a17cb5863eb0459f3b248c3bfe6a17e2`.

## Results

- All 50 existing CSV tables under `docs/results`, `docs/reanalysis/tables` and `docs/reanalysis/clinical_tables` match the base numerically (`rtol=1e-11`, `atol=1e-12`). The original 24-field analysis is preserved.
- The new eligibility table retains 158 records (43 CKD, 115 non-CKD) under all24, and 300 (165 CKD, 135 non-CKD) under core5.
- Four Python tests pass: eligibility counts/denominators, unchanged measurements and Record 43, invalid field validation, and site-build idempotence.
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

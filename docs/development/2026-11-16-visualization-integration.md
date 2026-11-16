# Visualization integration plan

The project review and the user's follow-up approve the following implementation on branch `codex/visualization-integration`.

## Design

Keep Python, the locked environment, offline HTML and the existing visual language. Keep the 24-field complete-case analysis as the published baseline. Add clearly named eligibility rules for five core measurements and the fields needed for each analysis. The clinical-strata table continues to use the original 24-field definition and labels that choice explicitly.

Generate the new rule tables, plot data and presentation from existing patient records and result CSVs. Embed shared navigation and state code into generated HTML so the pages also work under `file://`. Preserve the source-row identifier across explorer links. The eight-slide presentation follows the missing-data research questions, with Record 43 opening and closing the story.

## Tasks and checks

- [x] Add patient eligibility comparisons and tests for retained groups, observed denominators, unchanged measured values and Record 43.
- [x] Extend the cohort explorer with field rules, group-specific correlations, log display, presets, state and searchable row selection. Test actual browser interactions.
- [x] Add a project homepage and navigation; carry patient identity to PCA; improve small-screen plot width and the optional central heatmap range.
- [x] Generate an eight-slide project presentation and speaker notes from result tables; simplify the poster workflow and show signed PCA coefficients; regenerate the one-page report.
- [x] Add a cross-platform build/check command, an offline package, source/template guidance and a Pages workflow. Keep historical poster sources labelled as archived alternatives.
- [x] Reproduce the existing numerical tables, run numerical and browser checks, inspect rendered PDFs and review the diff before pushing the branch.

## Acceptance

The five-measurement rule retains 300 records (165 CKD, 135 non-CKD), versus 158 (43, 115) under the 24-field rule. Every rate displays its denominator. Changing only plot scale leaves the reported raw-value correlations unchanged. Generated HTML works offline with no remote scripts. The report remains one page, the poster one page and the main presentation eight pages. Only this feature branch is pushed.

# RenalLens: How Missing Data Shape the Clinical Picture of Chronic Kidney Disease

Eight slides, approximately seven minutes. The main presentation compares missing-data rules in the 400-record UCI CKD dataset. The earlier clinical companion is preserved as [case-study.html](case-study.html), with [its original notes](Case_study_notes.md).

## 1. One missing field, one excluded record (0:45)

Record 43 has a measured random glucose of 204 mg/dL and a CKD diagnosis. It has 23 of 24 explanatory fields recorded. Only rbc is missing. The all-24 complete-case rule removes the entire record, including that observed glucose result. Ask the audience what information a requirement for every field could remove. The project compares how those choices change the picture of the same 400 records. Record identifiers count from one after the CSV header. Source: original `data/raw/ckd.csv`.

## 2. Three rules, different denominators (0:55)

Observed measurements use the available values for each question, so the sample size depends on the feature or pair. Hemoglobin has 348 observed values, creatinine has 383, and the renal pair has 380. Complete cases require all 24 explanatory features and retain 158 records. Median and mode filling retains all 400 records. Numerical fields use the global observed median, categorical fields use the mode, and diagnosis never supplies the fill. Filled cells keep a provenance flag. The five displayed measurements are hemoglobin, creatinine, blood urea, glucose and blood pressure. Sources: `diagnostics.csv`, `renal_correlations.csv`, `eligibility_rules.csv` and the preprocessing rule.

## 3. Eligibility changes the retained cohort (0:55)

The bars start from the same 400 records. All-24 retains 158 records: 43 CKD plus 115 non-CKD. Requiring only the five measurements retains 300: 165 CKD plus 135 non-CKD. This is a change in eligibility, with no imputation. CKD retention changes from 17.2% to 66.0%. Record 43 has all five measurements, so it enters the core-five cohort. Source: `eligibility_rules.csv`.

## 4. The creatinine shift reverses within CKD (0:55)

Across all measured creatinine values, the median is 1.30 mg/dL. The all-24 median is 1.10. Within CKD, the median instead rises from 2.25 to 4.10. The group mix and the retained patients within each group both change. The CKD share among measured creatinine values falls from 62.1% to 27.2%. Read the plotted denominators aloud: they are the actual samples behind these medians. Sources: `median_shifts.csv`, `mixture_standardization.csv`.

## 5. Median filling creates a visible concentration (0:55)

The ECDF is the share at or below each hemoglobin value. The teal curve uses 348 measured values. The burgundy curve uses all 400 records after filling. All 52 missing hemoglobin values receive 12.65, the observed global median. That produces a 13.0% jump at that value. The observed values stay unchanged. Filling keeps records in the analysis while imposing a visible distributional feature. UCI describes hemoglobin as gms without a volume denominator. Sources: `measurement_values.csv`, `diagnostics.csv`.

## 6. Pearson rises while rank correlation falls (1:00)

The raw axes show all renal pairs, including the extremes. Pearson compares linear co-variation on the numerical scale, while Spearman compares ranks. Overall Pearson rises from 0.586 to 0.896, but Spearman falls from 0.703 to 0.478. The retained cohort has a different diagnosis mix and extreme values influence the raw covariance. The within-group Pearson figures and leave-one-record calculation on the slide show why one overall coefficient is an incomplete description. Omitting observed record 22 changes Pearson to 0.674. This sensitivity calculation describes the observed pairs, rather than a deletion recommendation. Sources: `measurement_values.csv`, `renal_correlations.csv`, `diagnostics_renal_influence.csv`.

## 7. Scaling changes the first principal component (0:55)

Both PCAs use the same 400 filled records and five measurements. The chart reports signed eigenvector coefficients, specifically `eigenvector_weight`, rather than scaled loadings. With raw units, glucose dominates PC1. With z scores, blood urea and creatinine have larger positive coefficients and hemoglobin has a negative coefficient. Read PC1 and cumulative PC1-plus-PC2 explained variance from the chart. A whole component can change sign without changing the PCA geometry. Relative signs are what show opposing feature directions. Sources: `pca_loadings.csv`, `pca_variance.csv`.

## 8. Back to record 43 (0:40)

Return to the observed 204 mg/dL glucose value. One unrelated missing field removes it under all-24 selection, whereas core-five eligibility keeps it. State the three conclusions on the slide: eligibility selects people, filling changes distributions, and the statistic and scale change the picture. Open the linked cohort explorer to show record 43, glucose and the complete-case view together.

## Playback and reproduction

Open `deck.html` locally. Arrow keys or Space advance, G opens the slide list, F opens full screen, C toggles the counter, and 1-8 jump directly. The HTML embeds the CityU logo and all plotted SVG data, with no remote dependencies. The final link is relative to the repository and opens `../results/figures/cohort.html?patient=43&feature=bgr&view=complete_case`.

Run `python scripts/build_presentation.py` from the repository root to regenerate the HTML and these notes from the published CSVs. Use `python scripts/build_presentation.py --render` to export the PDF, the contact sheet `preview.png`, eight full-size screenshots and a browser-check JSON record under `outputs/presentation/`. Rendering uses local Chrome and the project's Playwright dependency. Override the executable with `--chrome` or the `CHROME` environment variable.

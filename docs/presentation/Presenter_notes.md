# RenalLens: Reading Beyond Urine Albumin

Eight slides, seven minutes. The C61 group presentation uses the uploaded poster on the classroom computer. The deck can be used for rehearsal. [C61 presentation instructions](https://canvas.cityu.edu.hk/courses/70778/discussion_topics/644602)

## 1 · What else would you look for? (0:40)

“Here are two entries from a real patient record. The patient already has a chronic kidney disease label. Their urine albumin score is zero, the lowest grade, and the diabetes history says no. If you could open the rest of the record, what would you look at next?” Pause before advancing. Leave the anemia and glucose results covered. This is record 43 in the original data, counting from one. We return to the same person at the end.

## 2 · Why these measurements? (1:00)

“Think of the kidney as a filter. Albumin is a protein we usually want to keep in the blood. Creatinine is a waste product the kidneys clear. The urine test tells us about protein leakage. Blood creatinine gives us a clue to filtration. The kidneys also send a hormonal signal that helps the body make red blood cells. Hemoglobin carries oxygen inside those cells. Finally, high blood sugar over time can damage kidney blood vessels. A history of diabetes and a blood sugar reading answer different questions.” We studied the 250 CKD records among 400 patients. Each question uses the patients with the relevant fields recorded. [NIDDK on kidney tests](https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/tests-diagnosis) · [NIDDK on anemia](https://www.niddk.nih.gov/health-information/kidney-disease/anemia) · [NIDDK on diabetes and the kidney](https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease)

## 3 · What did grade zero tell us? (0:50)

Point to the shaded grade-0 column. “Each mark represents one person. The diamond is record 43. Their blood creatinine measured 1.0 mg/dL. Yet the 47 people with this same urine grade had creatinine readings from 0.6 all the way to 24. Each step up the chart doubles the value. The horizontal lines are the middle values at each grade.” There were 197 pairs overall and only one at grade 5. The measure here is the dataset’s albumin grade on a scale from 0 to 5.

## 4 · Why look at hemoglobin? (0:50)

“Urine albumin tells us about protein leakage. Blood creatinine gives a clue to filtration. Now look at what happens when we add a measure of oxygen-carrying capacity. Among 198 patients with both tests, those with twice the creatinine averaged about 0.90 units lower hemoglobin. The line describes this average. The points show how individual patients varied.” The interval was 0.62 to 1.18 units lower. An age-adjusted estimate in 192 patients was similar at 0.89 units lower. These are comparisons between patients measured once. UCI reports hemoglobin as “gms” without a volume denominator.

## 5 · What did a negative diabetes history tell us? (0:55)

“Return to the second entry on our opening card. A history marked no tells us what was recorded about diabetes. It still leaves today’s blood sugar to be measured. Among 87 people with a negative history and a glucose reading, 11 had random glucose at or above 200 mg/dL. Among 125 with a positive history and a reading, 61 reached that threshold.” The whiskers are 95% Wilson intervals. A further 26 people with negative history lacked a glucose result. Symptoms and confirmatory tests were unavailable. A single high reading here cannot establish a new diabetes diagnosis. [ADA diagnostic criteria, 2026](https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes)

## 6 · How often did findings overlap? (1:05)

“Count one mark for each of the 175 patients with all three findings recorded. We counted urine albumin grade 1 or above, an anemia entry marked yes, and glucose at or above 200. The filled squares identify 70 out of 175 people with two or more findings. Fifty-nine had exactly two and eleven had all three.” For the other 75 people at least one field was missing. Even with missing fields, nine of them had two confirmed positives. Therefore at least 79 of all 250 had two or more. If every unknown were positive, the largest possible total would be 122. Those limits are 31.6% and 48.8% of this sample.

## 7 · What appeared at grade zero? (0:50)

“Now select the patients with the same albumin grade as record 43. We have anemia status and a glucose measurement for 45 of them. Follow the rows, one dot per patient. Twenty-nine had neither finding. Twelve had high glucose alone, and two had recorded anemia alone. Two had both. That makes 16 people with at least one additional finding.” Nine more people with grade 0 lacked a glucose reading. They are outside this figure. Ask the audience which row they think contains record 43, then turn to the last slide.

## 8 · Back to record 43 (0:50)

“Open the rest of the record. The anemia field says yes, and hemoglobin was 9.7 in the units supplied by UCI. The diamond on the scale marks this patient’s random glucose of 204 mg/dL, just above our threshold of 200. Of the 45 grade-0 records with anemia status and glucose available, two had both findings. Record 43 is one of those two. Their urine score and diabetes history alone would have left both findings out of view.” The anemia observation comes directly from the recorded field. The single glucose value describes that measurement and does not establish a new diabetes diagnosis.

## Data and playback

The opening and closing use one observed patient, selected to illustrate co-occurrence. Cohort counts, uncertainty intervals and missing-data bounds come from the project tables. The HTML embeds the plotted data and logos. [UCI CKD dataset](https://doi.org/10.24432/C5G020) · [Patient measurements](../reanalysis/clinical_tables/patient_measurements.csv) · [Full result tables](../reanalysis/clinical_tables/)

Open `deck.html` locally. Use the arrow keys or Space to advance, **G** for the slide list, **F** for full screen, **C** for the page count, and **1–8** to jump. To export a vector PDF, use Chrome’s **Save as PDF** with background graphics enabled, no headers or footers, and the CSS page size (16:9).

To recreate the thumbnails in PowerShell, set `$env:CHROME` to the full Chrome executable path and run `python render_preview.py deck.html 8 preview` from this directory. The script requires Pillow.


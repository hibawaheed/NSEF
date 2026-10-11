# What the Version 4 graphs mean

Start with **03b_paper_policy_alerts** for a paper and **03_paired_policy_alerts** for a wide presentation. The [gallery](../../figures/revision4/final/index.html) and [combined PDF](../../figures/revision4/final/CHART_PACK.pdf) contain all twelve figures. Every graph has an exact CSV with the same filename.

**PSI** compares counts in fixed ranges. **KS** compares the ordered distributions without those fixed ranges. A **subgroup** is a declared slice such as a recorded sex/race combination. **Accumulation** means waiting for more records in that group before testing. Both statistics see the same collected records.

**Age 60+ weight ×2 / ×4 / ×0.25** changes the probability of drawing an existing record. It never changes a recorded age, school level, group or outcome. A whole-record draw may repeat a source household; these are constructed experiments, not new respondents. “Unchanged” means independent draws from the same empirical source. “Look” means one constructed batch, not a calendar date.

| Graph | How to read it | What it does not establish |
|---|---|---|
| 01 sensitivity, unchanged | Each square is the fraction of 100 single-block repetitions that signalled under an unchanged source. Gray is historical shortage, not zero alerts. | Low rates in these controls do not prove an unconditional error guarantee. |
| 01 sensitivity, weight ×2 | Move across incoming counts and reference sizes to see how often the predefined modest change is noticed. PSI and KS have matching panels. | This is not whole-stream power, population accuracy, or an optimized set of conditions. |
| 01 sensitivity, weight ×4 | Same grid for the stronger design change. The color scale stays 0–100%. | A stronger constructed change is not evidence that real-world changes are this large. |
| 02 frozen targets / validation | Each dot is the worst lower confidence bound across both statistics and both design changes at the selected target. None reaches the dashed 80% line. Blank rows have too little historical source support. | Fallback 800 does not mean 800 is sufficient, feasible, or validated. |
| 03 and 03b complete policy comparison | Blue is PSI; orange is KS. The unchanged panel shows any false alert. Other panels show exact-target detection after onset. Whiskers are pointwise 95% Wilson intervals. | An interval is not a probability that the method is universally better. The two layouts contain identical data. |
| 04 all-group assessability | Bright cells mean a group could be tested at least once; dark cells mean it usually could not. All 30 views remain. | Being able to test does not mean detecting change. A dark cell does not prove stability. |
| 05 waiting including misses | Lower means earlier detection. Misses receive 15, the full post-onset restriction. | These numbers are not days and do not exclude unsuccessful runs to make methods look fast. |
| 06 OULAD model / baseline | Both predictions are checked on the same 973 records. The constant class comes from training labels only. Accuracy counts correct labels; balanced accuracy gives each outcome class equal weight. TPR is the fraction of actual successes predicted positive; FPR is the fraction of non-successes predicted positive. | This weak model is not evidence of useful student-success prediction or harm caused by drift. |
| 07 compute cost | The left panel times each statistic’s computation. The right includes both statistics and shared setup. | Mean times on this machine are not deployment guarantees. |
| 08 OULAD corrected PSI | Gray keeps the original broken-bin result; blue shows the documented 0 / 1 / 2+ correction. Blank subgroup rows lack support. | Correcting known bins is not untouched validation or proof of when a real change began. |
| 09 total cost / memory | Calibration takes work too. Whole-process peak memory and logical statistic arrays are shown separately. | Tiny histogram arrays do not mean the entire system needs only those bytes of memory. |

The main result is a limitation: asking for 800 incoming subgroup records prevented the target from being tested in the available 20 batches. The simpler, predefined target of 100 was more usable in this experiment. The methods’ detection results vary by change direction; keep all conditions in the presentation.

The source CSVs retain confidence limits, misses, unsupported groups and ties. For exact-target metrics, aggregate/single-only reporting is not applicable. Under the unchanged source, target alerts are false alerts, not detections of genuine changes. The reporting table explicitly marks these distinctions; literal raw engine records are preserved underneath.

The ACS labels use published codes. SEX 1/2 mean recorded male/female. RAC1P 1 is White alone; 2 Black or African American alone; 3 American Indian alone; 4 Alaska Native alone; 5 the dictionary’s combined American Indian/Alaska Native category; 6 Asian alone; 7 Native Hawaiian and Other Pacific Islander alone; 8 Some Other Race alone; 9 Two or More Races. Full definitions and source attribution are in the [Version 3 data cards](../revision3/DATA_CARDS.md). The target is SEX=2 & RAC1P=2. No gender identity or causal disadvantage is inferred.

Use the detailed heatmaps at full-page or poster size. Use the compact 7.2-inch-wide 03b PDF at full paper width; shrinking it to a narrow column makes the labels harder to read. The natural OULAD figures and constructed ACS figures describe different kinds of evidence. The older Version 2 simulation graphs stay labelled synthetic.

# Revision 4 findings — 12 October 2026, Pakistan time

This is an AI-assisted technical explanation of computed results, not a student-authored final submission. Subgroup PSI remains the project’s core. The proposed subgroup-specific collection extension was **not supported under the approved settings**. The completed work supports an empirical investigation of sensitivity, support and waiting costs, not a claim of a new superior algorithm.

## What was actually done

The study reused genuine public ACS records and OULAD cohorts. Historical ACS households were split into 3,924 selection and 3,944 validation representatives. A separate 2016 empirical pool contained 15,584 household representatives. The new controls resampled whole records; values and outcomes were never invented or edited. Repeated draws are not additional people. Actual ACS year comparisons and OULAD cohort comparisons remain separate descriptive evidence.

Selection evaluated 67,500 paired group-block repetitions on the approved reference/count/change grid. Validation added 6,000 paired repetitions after the targets were frozen. Fifteen of 30 declared views met the historical source-support rule; the other fifteen remain explicit shortages. The final comparison used 220 streams and five policies, making 1,100 engines with identical PSI/KS blocks within each policy. All methods used the agreed support rules and finite testing budgets.

The target group was the published ACS code combination `SEX=2 & RAC1P=2`: recorded female and Black or African American alone. Recorded sex is not inferred gender identity. “Weight ×2” and “weight ×4” make whole records with recorded age at least 60 more likely to be sampled. “Weight ×0.25” makes them less likely. These multipliers do **not** multiply anyone’s age. The predefined change starts at constructed delivery 6, not a claimed real-world date.

## The calibrated rule failed its stated test

No supported group reached the required minimum 95% Wilson lower bound of 0.80 across both statistics and both design alternatives at reference size 400. All group targets therefore fell back to 800. The global rule also fell back to 800. None of the 15 supported validation groups met that same criterion either. The targets were not relaxed or retuned.

Consequently, the global and subgroup policies were scientifically identical in all 220 evaluation streams. The target subgroup never accumulated 800 incoming draws within 20 batches, so neither fallback policy ever tested it. This is an operational failure of the proposed rule in this design, not evidence that no drift existed.

The sensitivity study shows why incoming sample size alone is insufficient: reference size, the underlying distribution and the size/direction of the change also matter. A larger requested target can make monitoring less useful when it cannot be collected soon enough.

## Complete primary comparison

Each changed condition has 40 streams; the unchanged condition has 100. Each table cell gives **PSI / KS counts**. “Detection” requires an alert for the exact named subgroup after the declared onset. The last column counts any alert anywhere in the full intersection family under the unchanged source.

| Collection policy | Age 60+ weight ×2 detections /40 | Weight ×4 detections /40 | Weight ×0.25 detections /40 | Any unchanged-source alert /100 |
|---|---:|---:|---:|---:|
| One batch, minimum 50 | 0 / 0 | 0 / 1 | 0 / 0 | 2 / 0 |
| Accumulate 100 | 3 / 8 | 39 / 40 | 15 / 7 | 1 / 0 |
| Accumulate 400 | 0 / 0 | 25 / 30 | 3 / 1 | 2 / 0 |
| Global fallback 800 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |
| Group fallback 800 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 |

Source: [rates.csv](../../results/summary/revision4/main-approved/rates.csv), derived from saved stream decisions. Every policy and declared condition is retained. The fixed-100 rule is a prespecified baseline, not a newly optimized algorithm.

At fixed 100, PSI minus KS detection differences were −12.5 percentage points for ×2 (paired 95% bootstrap interval −25 to 0), −2.5 points for ×4 (−7.5 to 0), and +20 points for ×0.25 (+5 to +35). These are pointwise, conditional intervals from 2,000 paired complete-stream bootstrap draws; they are not simultaneous certification across all comparisons. PSI had more detections in the downward stress condition; KS had more observed detections in the upward conditions. There is no universal winner. See [all paired differences](../../results/summary/revision4/main-approved/paired_differences.csv).

For the strongest upward condition, fixed-100 mean restricted delays were 5.175 looks for PSI and 3.675 for KS. Every miss contributes the full 15-look restriction. Fixed-400 delays were 9.9 and 8.9. These are delivery indices, not days. In the 100 unchanged streams the target was assessable at least once in 7 with the batch rule, 100 with fixed 100, 100 with fixed 400, and zero with either fallback. First assessment and first detection are separate quantities. Mean reference count for this target was 327.51, below the 400-draw calibration planning size; that mismatch is retained in [reference counts](../../results/summary/revision4/main-approved/evaluation_reference_counts.csv).

## OULAD correction and prediction context

The previous-attempts representation now separates 0, 1 and 2+ using the historical design data. Original Version 3 results remain unchanged. For the overall supported cohort comparison, old PSI was 0.0017208 and corrected PSI was 0.0292326; KS was unchanged within numerical rounding. This repairs information lost by the original bins. It is explicitly a correction after seeing the earlier results, not untouched validation.

On the same 973 later audit records, the frozen model correctly predicted 541 (55.6%) and the training-majority constant predicted 547 (56.2%). Balanced accuracy was approximately 50.9% versus 50.0%. The constant class was selected only from the 2013J training labels. The model is weak; these results cannot establish a useful outcome predictor or prove a relationship between detected input change and outcome harm.

## Preserved earlier evidence and limits

The complete 1,820-stream matched accumulated-KS extension of the Version 2 **synthetic** benchmark is preserved, including ties and KS advantages. Its tables are in [the correction results](../../results/summary/correction/benchmark_aggregate.csv). It is not a new human-record study. The original Version 3 weak real-record substitution comparison also remains: both accumulated methods missed its exact target in the saved 30-stream cells. The OULAD bin fix does not explain away those ACS misses.

The new null results are consistent with low alert rates in these finite controls; zero KS alerts in 100 streams does not prove a universal guarantee. The resampling source is fixed and previously examined. Household keys are disjoint by recorded year/role, but cannot prove that no real person appears across survey years. Natural ACS/OULAD observations are not used to estimate drift-detection accuracy because true change onsets are unknown. No survey-weighted population claim, causal harm claim, real-time deployment validation or algorithmic novelty claim follows.

The main study used approximately 25.4 CPU minutes and 27.5 wall-clock minutes, with peak process RSS about 213.7 MiB. Selection, validation, engine and kernel costs are saved separately. Logical histogram-array bytes are not whole-system memory. Hardware, startup, reporting, verification and publication costs must not be conflated with statistic timings.

All 124 software tests pass. Full verification checked 1,320,000 declared feature-test rows, all 220 global/group ties, source/lineage hashes, and unchanged earlier evidence. Three calibration cells and two complete policy streams were reproduced. Twelve final figures include exact CSVs, 300 dpi PNGs, vector PDFs/SVGs and a combined PDF pack. The original plotting failure and intermediate layout are retained; use [the final gallery](../../figures/revision4/final/index.html).

The evidence snapshot is prepared before the planned 18 October results freeze and 26 October submission deadline. It does not select the student’s final project version or establish mentor/fair approval. The defensible contribution is the documented sensitivity and collection trade-off study, including the negative calibrated-policy result.

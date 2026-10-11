# Revision 2: what was built and what the results mean

AI-assisted research and technical explanation, 11 October 2026. This is evidence for the student's interpretation, not a student-authored submission or a claim of independent invention.

## The answer in plain language

The useful project is now a tested monitoring prototype: compare old and new data, look inside predefined groups and their intersections, keep small groups visible, limit repeated false alarms, and check prediction outcomes separately when labels exist. Subgrouping is implemented. For two binary attributes A and B there are nine views: everyone, A=0, A=1, B=0, B=1 and four A/B intersections.

An example: the overall population can look unchanged if one group's values rise while another's fall. The group comparisons can expose that cancellation. This is a known phenomenon, not a discovery unique to this project. A distribution change also does not automatically mean unfairness or prediction failure.

The revised software adds a complete-stream error budget, count-based accumulation for small groups, a KS comparator, and independent labelled outcome audits. It does not retrain or improve a production prediction model. The synthetic prediction rule is fixed; Adult uses a simple fitted logistic model. “Better detection” below means detecting introduced changes under specified experiments, not improved prediction accuracy or proven real-world fairness.

## What was actually run

The original 440-run exploratory study is preserved. Revision 2 adds **1,820 synthetic streams and 120 conditional Adult resampling streams**, each with 20 batches. The change starts at batch 6. Five software smoke streams are excluded from evidence. All 1,940 evaluation streams completed with zero failures.

The synthetic study contains 500 unchanged streams, 960 grid streams spanning two batch sizes, four affected-group sizes and three shift strengths, 120 cancellation streams, and 240 robustness streams. Adult uses three fixed randomized role splits, each with 20 unchanged and 20 shifted resampling streams. Settings and seeds were recorded before the main evaluation; thresholds were not selected from the results.

Runtime: 1,839.5 seconds synthetic and 212.3 seconds Adult on the local machine. These are execution times, not total development time. Full results, source/configuration snapshots, hashes, counts, decisions and timings are saved.

## Findings, including unfavorable results

### Repeated false alarms improved

Among 250 unchanged streams at each batch size, horizon-controlled intersection PSI raised at least one alert in **10/250 (4.0%)** at n=250 and **12/250 (4.8%)** at n=1,000. Using a fresh 5% group correction at each batch without a horizon budget raised alerts in **105/250 (42.0%)** and **132/250 (52.8%)**. Fixed PSI ≥0.1 alerted in 250/250 and 249/250.

The controlled estimates have 95% Wilson intervals of **2.19–7.21%** and **2.77–8.20%**. Their upper limits exceed 5%; this experiment does not empirically certify a population error rate below 5%. The theoretical finite-horizon bound depends on valid constituent tests, fixed groups, exchangeable independent samples and the declared monitoring horizon. This comparison is within revision 2, not a before/after comparison against v1's different six-batch experiment.

### Accumulation helped, with a time and scope cost

Post-change detection is any alert in the 15 batches beginning at the intervention. The benchmark gives equal weight to its 12 grid cells at each batch size; it is not an estimate of deployment case frequencies.

| Method | n=250: detected / 480 | n=1,000: detected / 480 |
|---|---:|---:|
| Overall PSI | 125 (26.0%) | 215 (44.8%) |
| Intersection PSI | 141 (29.4%) | 327 (68.1%) |
| Intersection KS | 152 (31.7%) | 347 (72.3%) |
| Accumulated PSI | 313 (65.2%) | 417 (86.9%) |

Accumulation had the same observed synthetic complete-stream false-alert counts as ordinary intersection PSI: 10/250 and 12/250. This equality is an observation, not a universal property.

Any alert is not the same as identifying the exact affected intersection. At n=250, a 5% target share and a 1.4-SD change, the ordinary method never had 50 target records in a batch and detected that target in **0/40** runs. Accumulation reached its 100-record block requirement and detected the target in **40/40**, with a mean first-alert delay of **7.325 batches after onset**. The 95% Wilson interval for 40/40 is 91.2–100%; observed perfection does not imply population perfection.

For a 2% target under the same settings, accumulated target coverage/detection was only **19/40 (47.5%)**, with a restricted mean delay of **14.175** when missed targets are assigned the 15-batch horizon. Small groups remain difficult. Accumulated blocks can mix pre-change and post-change data, and the result has not been tested against accumulated KS or all other accumulation strategies.

### PSI did not show general superiority

Ordinary intersection KS detected more of the balanced grid than ordinary intersection PSI at both batch sizes. Figure 3 includes every declared grid cell and paired uncertainty. These results do not support a claim that PSI is generally the best statistic. Benefits from subgrouping or additional accumulated observations must not be credited automatically to PSI itself.

### Cancellation works as an example, not a universal advantage

At exact cancellation, intersection PSI, intersection KS and accumulated PSI each alerted in **40/40** runs. Overall PSI alerted in **1/40**; the overall input distribution is unchanged in that scenario, so that aggregate alert is a false alarm for its own target, not successful detection of aggregate drift. With no opposing shift or a half opposing shift, overall PSI also alerted in **40/40**. The striking separation therefore depends on the masking condition; the broader grid is needed to evaluate less idealized cases.

### Input change and prediction deterioration differ

When only the outcome relationship changed, the outcome audit and combined monitor alerted in **40/40** runs; ordinary intersection PSI alerted in **2/40** and never identified the altered target. Its monitored inputs had not changed. With only the correlation structure changed, both marginal input distributions stayed unchanged: the independent outcome audit and combined monitor again alerted in **40/40**, while intersection PSI had **0/40 post-onset** alerts.

When an unused feature shifted, intersection PSI alerted in **40/40**, but the outcome audit alerted in **1/40**. The predictor does not use that shifted feature. Calling every such input alert harmful would be wrong. Outcome tests measure specified deterioration (TPR down, FPR up, accuracy down), not a complete definition of fairness. Immediate labels and known generated interventions make these tests easier than many deployment settings.

### Public data do not establish superiority or real chronological drift

All main input methods alerted in **60/60** introduced Adult shift streams. Overall PSI and the subgroup methods therefore tie on this coarse detection endpoint. On unchanged resampling streams, intersection/accumulated PSI alerted in **5/60 (8.3%)**, overall PSI in **3/60**, intersection KS in **0/60**, and the combined monitor in **3/60**. Figure 8 reports each split separately with wide intervals. The 8.3% estimate must not be hidden or described as observed control below 5%.

These runs reuse a finite historical pool within fixed splits. Their uncertainty is conditional resampling uncertainty, not uncertainty across newly sampled populations. The weighted working-hours intervention is imposed; this is not evidence of real historical drift, causal discrimination, or applicability to Pakistan. No second real dataset has been validated.

## How to read the chart pack

1. **False alarms:** how often a complete unchanged stream triggers an alert. Lower is better here. The 5% line is a target, not an empirical certification.
2. **Detection map:** how batch size, affected-group size and shift strength alter any-alert rates. Darker means more detections, not automatically more exact localization or fairness.
3. **PSI versus KS:** positive differences favor PSI; negative differences favor KS. Identical paired outcomes can give zero-width bootstrap intervals without proving equality.
4. **Coverage and delay:** whether the actual target was ever tested and how long target detection took. Misses remain in the calculation.
5. **Cancellation:** when opposing shifts defeat an aggregate input monitor. Points are horizontally offset to expose overlap.
6. **Input and outcomes:** why independent outcome checks matter and why a changed input can be harmless to the fixed predictor.
7. **Group outcomes:** actual TPR, FPR and accuracy changes inside each group. These are labelled performance measures, not an automatic fairness score.
8. **Adult splits:** what persisted under three conditional public-data resampling checks, including false alarms.
9. **Operating tradeoff:** fixed methods' detection and false-alarm costs together. It is not an ROC curve or a threshold search.
10. **Drift over time:** two first-index saved synthetic streams showing PSI before and after the intervention. Filled markers mark corrected alerts. These illustrations do not replace repeated-run evidence.

Each figure has vector PDF/SVG, 300 dpi PNG, source CSV, caption and provenance hashes. Source tables retain precise values even where plotted percentages are rounded.

## What is defensible to present

A suitable working description is **“Subgroup drift monitoring under limited data: false alarms, coverage and outcome relevance.”** The defensible contribution is an implemented, reproducible evaluation and usable local-data web prototype. The most useful measured result is the coverage/detection tradeoff from accumulating small-group observations while allocating error across time, together with explicit limits of input-only monitoring.

Novelty is **not established**. Subgroup auditing, accumulation, alpha spending and input/performance monitoring have prior art. No aligned comparison to Maximum Subgroup Discrepancy was implemented, and no claim of outperforming it is justified. The current results reject a broad claim that PSI uniquely detects unfairness or is generally superior. A narrow evidence-based engineering/research presentation remains possible; competition eligibility or acceptance has not been determined.

Further research would need a prospectively fixed comparison against accumulated KS and a relevant established subgroup method, another genuinely temporal openly licensed dataset, delayed-label conditions, and tests with dependence. These are recorded next studies, not work represented as already completed. Do not change the current evaluation to hide an unfavorable result.

## Website scope

The website accepts reference/current CSVs, one monitored feature, up to two group columns and optional batches. It runs in a worker in the visitor's browser and generates charts and result exports. Uploaded records are not sent to a server. The website is an input-only analyzer; the research's outcome audits are not implemented as a visitor-facing feature.

Browser and research procedures differ explicitly: the browser reserves 25% of reference rows for bin design and corrects one family across selected groups and batches; the research uses separate design data and an online allocation over 20 batches. Browser results are not interchangeable with research rates. The browser prototype cannot certify fairness or monitor an unlimited stream with a perpetual 5% bound.

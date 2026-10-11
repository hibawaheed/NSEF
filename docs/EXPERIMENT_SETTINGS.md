# Recorded experimental choices

These are explicit choices for exploratory validation, saved before the runs. The user instructed Codex to proceed without protocol sign-off and to log all work. This file records computational choices; it does not assert administrative approval or replace the student's formal plan.

| Decision | Implemented choice | Limitation |
|---|---|---|
| Primary diagnostic | Run-level alert probability under concentrated/intersection input change, alongside null error | An exploratory comparison, not a universal superiority claim |
| Synthetic trials | 60 independent runs per S0–S5; 6 windows, onset at 3; 2,000 observations per reference/current sample | Broad intervals at this trial count; one main magnitude and size |
| Independent roles | Logistic fit 3,000; bin design 3,000; reference 2,000; baseline labelled audit 4,000; new windows | No temporal/cluster dependence modelled |
| Bins | 8 target quantile bins from design only; duplicate cuts collapse; constant design gets explicit below/equal/above bins | Effective bins differ for tied features |
| Missing/unknown | Extra missing numeric bin; fixed category vocabulary plus unknown and missing bins | Main experiments use two numeric monitored features |
| Smoothing | 0.5 added to every bin count, normalize each sample by its own total | This estimator is not raw population PSI |
| Support | Both sample totals ≥50 for a feature/group comparison | A count floor does not guarantee power or enough labelled positives |
| Permutations | 1,999 random pooled-count permutations, ties included, `(b+1)/(B+1)`; tiny cases exact | Assumes exchangeability under the null; Monte Carlo p-value noise remains |
| Testing families | A1: 2 aggregate tests; B1: aggregate + 4 single groups ×2 features =10; B2 adds 4 intersections =18 | Holm controls each declared family per window, not a whole stream |
| Fixed-threshold baselines | A0 aggregate and B0 all predefined groups, PSI ≥0.1 | Contextual practical thresholds, not matched-error procedures |
| Unsupported tests | Visible status and p=1 in the declared family; no alert | Not labelled stable |
| Reference/alerts | Reference fixed within stream; every alert retained; no reset, cooldown or repair | Repeated alerts can occur |
| Outcome measurement | Fixed logistic classifier, independent baseline labelled audit; overall accuracy, TPR/FPR for every group | Synthetic model uses signal only; nuisance intentionally excluded |
| Outcome relevance | ≥5 percentage-point increase in absolute A-group TPR gap | A marginal metric cannot diagnose every intersection disparity; descriptive noisy outcome estimate |
| Rate uncertainty | Wilson intervals using complete runs as units | Adult intervals are conditional Monte Carlo uncertainty, not population inference |
| Mean uncertainty | Mean within each run then Student-t interval across runs | Pointwise descriptive intervals, no simultaneous coverage claim |
| Paired comparison | B2–A1 indicators, 5,000 paired run bootstrap resamples | Percentile bounds can degenerate when all differences coincide |
| Public data | UCI Adult, CC BY 4.0, attribution saved; one fixed deduplicated random split | Historical US cross-sectional data, not Pakistani or deployment data |
| Adult repeats | 40 runs/condition; 4 windows of 2,000, onset at 2 | Reusing the same finite records does not create more independent people |
| Adult intervention | Within Female × fixed age-band strata, increase selection weight sixfold for hours/week >40; records/labels unchanged | Semi-synthetic selection shift, not natural observed chronology |
| Adult grouping | A: recorded sex; B: age <40 vs ≥40; 4 fixed intersections | Source categories reflect historical recording; no broader demographic conclusions |
| Optional repair | Not implemented or evaluated in this package | No claim to fix bias automatically |

## Interventions

- S0: no distributional intervention, independent sampling variation.
- S1: add 1.25 to the observed signal for A=1 (10% share); latent signal and label mechanism remain unchanged. This is measurement corruption.
- S2: four equally weighted intersections have latent means +0.8 or −0.8 in a checkerboard. Reverse the observed means after onset while preserving the latent outcome mechanism. Both marginal attribute summaries and aggregate input distributions are unchanged in the population. This is intentionally constructed exact cancellation.
- S3: add 1.25 to nuisance, which the classifier excludes. A real input change can be benign for this classifier.
- S4: flip outcomes only for A=1 while retaining exactly the same input-generation mechanism. Input-only monitoring is not expected to detect it reliably.
- S5: raise A=1 share from 0.1 to 0.4 without changing within-group feature distributions. Aggregate drift is a correct signal of a different question.

No seed searching, model selection on evaluation data, threshold tuning from results, or post-hoc removal of failed runs is permitted in this workflow. Changes go in `records/CHANGELOG.md`, and reruns go in new directories.

“Subgroup-decomposed” means reporting conditional PSI values for the predefined groups. It is not an assertion that aggregate PSI equals a weighted sum of subgroup PSIs. Population-composition changes and conditional-feature changes are different targets.

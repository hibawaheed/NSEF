# Revision 2 implementation and evaluation record

AI-assisted technical documentation, not a student-authored submission. This is a new evaluation after the exploratory v1 results. The original 440 runs and figures remain unchanged.

## Fixed choices before evaluation

Configuration: `configs/revision2.json`. Independent new seeds and generated data; no search for favorable thresholds. Smoke runs are software checks and are excluded from evidence. Synthetic model is a fixed threshold rule with known inputs; it is not a newly trained AI model. Adult uses the existing fixed logistic-regression fitting procedure with three independently randomized role splits. No reference is updated after an alert.

- Twenty batches; change begins at batch 6. Alpha = 0.05 across the declared horizon.
- 24 grid cells: affected intersection shares 2%, 5%, 10%, 25%; batches of 250 or 1,000; shifts of 0.35, 0.7, 1.4 baseline standard deviations; 40 independent repeats per cell.
- 500 unchanged streams: 250 at each batch size. These estimate error rates, not tune parameters.
- Three degrees of cancellation (0, 0.5, 1), plus gradual, missingness, irrelevant-feature, outcome-only, group-composition and correlation-only shifts; 40 repeats each.
- Total synthetic evaluation: 1,820 independent streams. Public-data check planned: 3 fixed splits × 20 repeats × 2 conditions = 120 conditional resampling streams.
- Fixed reference n=10,000, independent bin-design n=3,000, separate labelled audit n=10,000. Six requested quantile bins plus explicit missingness. Pseudocount 0.5; minimum 50 records on each side. Counts and support retained, not converted to “no drift.”
- Main grid changes A=1,B=1. A's prevalence is twice the requested affected-intersection share; B has prevalence 0.5. Cancellation has equal intersections and swaps means at full cancellation.

## Comparisons

Overall PSI and intersection PSI use the same per-test permutation procedure; overall KS and intersection KS use the same KS procedure. Fixed-threshold PSI and per-batch Holm PSI are ablations without horizon-wide control, not equally controlled competitors. Nine fixed views: everyone, four single-attribute views, four intersections.

For a family at each batch, apply Holm and compare with alpha/20. The union bound then bounds any null rejection over the horizon by alpha if each constituent p-value is valid. This does not require independent overlapping-group tests or independent comparisons to the shared reference. It DOES require exchangeable independent samples for each permutation test; arbitrary autocorrelated rows and adaptive value-based sampling are outside this guarantee. The declared 20-batch horizon cannot be reset repeatedly while retaining the same total error guarantee.

The accumulated method buffers each group's observations until its count reaches 100, tests at that batch boundary, then resets that group's buffer. Different groups may test at different boundaries. Triggering uses group membership/counts only, never the monitored feature or labels; each group's current blocks do not overlap. Up to 20 potential tests still receive alpha/20, including skipped opportunities. Both baseline and current block must reach 100. A block may straddle the change point; that dilution is retained as a real delay cost. This is an application of existing ideas, not claimed invention of sample accumulation or alpha spending.

Monte Carlo PSI uses 15,999 hypergeometric count permutations, plus-one p-values and inclusive ties. A conservative shortcut replaces p with 1 only when accumulated extreme draws already force the full-budget p above the largest decision threshold where it is used. This never creates a rejection. Reported p=1 can therefore be censored rather than an exact estimate. Permutation resolution covers the combined channel's smallest cutoff, including correlation's two features.

KS tests nonmissing values using SciPy's exact continuous-null distribution. A separate two-sided Fisher test covers missingness; a fixed factor of 2 combines them. Continuous-null KS p-values are conservative with ties. No tuning of ties or missingness settings on results.

## Outcomes and combined monitoring

A separately scheduled labelled audit tests TPR decrease, FPR increase and accuracy decrease in each of nine views. Denominators of 20 required on each side for the relevant label class. One-sided Fisher tests; Holm over 27 tests and alpha/20 across time. These measure performance deterioration, not a universal definition of unfairness. Actual outcomes are available immediately in these experiments; delayed/missing labels are not validated.

The combined monitor spends alpha/2 on ordinary intersection PSI and alpha/2 on outcome audits; each also spends across the horizon. It is evaluated separately from either standalone channel. A union of standalone alpha=.05 alerts would not inherit a .05 combined bound.

## Estimands and charts

Report complete-stream any-alert probability under no change, post-onset any alert, exact target-intersection recovery, delays including missed detections, support coverage, and subgroup outcome changes. Detection is not scored as success for a channel whose input distributions did not change (outcome-only and correlation-only marginal monitoring). Non-detection is not evidence of no change. Use Wilson intervals for stream-level proportions, and resample paired complete streams for method differences. Small 40-repeat cells have substantial uncertainty. Time-to-alert after onset remains descriptive if an earlier false alert occurred; separately report pre-onset alarms.

Public Adult records are reused across repetitions; intervals and results are conditional on each finite split and are not independent new populations or natural chronological drift. Source: Becker & Kohavi, UCI Adult, CC BY 4.0, https://archive.ics.uci.edu/dataset/2/adult. No additional dataset is needed for this stage; generalization beyond Adult remains unestablished.

## Prior work and novelty boundary

Read: Maximum Subgroup Discrepancy (https://arxiv.org/html/2502.02221v2) already investigates intersectional masking, sample complexity and computational comparison. Statistically Valid Post-Deployment Monitoring (https://arxiv.org/html/2506.05701v3) distinguishes input and performance tests and discusses repeated testing and label efficiency. We do not claim subgroup auditing, sample-size analysis, alpha spending, or two-channel monitoring is new. This contribution is an implemented, reproducible evaluation of this particular monitor and its operating limits. No superiority to MSD is established; reproducing it with aligned targets is separate work. Study results may reject the proposed accumulation benefit.

SciPy API references checked for KS and Fisher test conventions: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html and https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html.

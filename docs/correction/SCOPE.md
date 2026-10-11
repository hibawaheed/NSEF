# Bounded correction, 11–14 October 2026

This is an explicitly **post-result correction** of Version 3, plus a retrospective comparator for Version 2. It is not untouched validation or a new research direction. The user requested these changes after seeing the previous results. No student decisions, mentor approval, or independent authorship are inferred.

The original 3,011 tracked files are inventoried before editing in `records/correction/preserved_inventory.json`. Earlier code, data configurations, output directories and figures remain intact. This work uses branch `codex/subpsi-r3-corrections` and new `correction` directories. No push, deployment, purchase, or submission is part of this correction.

## OULAD

Keep BBB 2013J→2014J and every previous eligibility rule, role assignment, group, model coefficient and support threshold. The independent historical design subset has 372 students: 314 zero previous attempts, 45 one, 12 two, one three. Set half-integer boundaries 0.5 and 1.5 to distinguish **0 / 1 / 2+**, plus missingness. Larger future integer counts stay in 2+. Negative, fractional or infinite counts fail validation. This is a simple feature-specific count rule, not an algorithmic novelty claim. The sparse 13-record design tail must remain visible.

Only the previous-attempts PSI binning changes. Credit bins and KS remain unchanged. Reference support is still required; a corrected bin cannot rescue an undersized group. These are observational distribution distances, without known drift truth or onset. No detection-accuracy claim or calibrated natural alerts is added.

The constant prediction baseline is selected using the original 757 training labels: 438 positive and 319 negative. It predicts Pass/Distinction for every record; an exact training tie would predict the negative class. Audit labels never select the rule. The existing logistic model is restored from its saved parameters. Report both models' group and aggregate accuracy, TPR and FPR with counts; do not search for another model. Natural rates are descriptive for these records, not independent population estimates.

## Version 2 comparator

Run all 1,820 declared synthetic streams from `configs/revision2.json` and the saved case list, retaining exact seeds, records, historical design bins and group definitions. Use one shared accumulation scheduler, whole-batch blocks, minimum 100 reference and current observations, 20 looks, and the same standalone 5% error budget for each statistic. Each look gets alpha/20 and a fixed Holm family of 9 groups × declared features; PSI retains 15,999 permutations. KS uses its existing exact-test/missingness rule; no extra records are supplied. The union of PSI and KS alerts does not inherit a 5% combined guarantee.

For every stream, require original PSI scores, counts, eligibility, starts and alert group sets to replay. Conservatively censored nonsignificant p-values may differ because the shared engine stops at the horizon cutoff instead of the old ordinary-test shortcut's larger cutoff. Scores and decisions must match. Record coverage, waiting time, restricted delay (15 for no post-onset detection), costs, block ages and unsupported groups. Report all declared cells; paired bootstrap intervals describe repeated simulations within fixed cells. Grid averages equally weight the original 12 cells per batch size; intervals must preserve this stratification. Null alert proportions use Wilson intervals across independently generated streams. The shared reference within a stream is not an additional independent replicate.

No Adult rerun, new datasets, new algorithms, threshold search or classifier search. Stop by 14 October 2026, 23:59:59 Asia/Karachi, or the configured two-hour benchmark wall-time cap. If incomplete, preserve partial outputs and mark the full comparison unresolved.

## Verification and freeze

Save CSVs and vector/raster figures, original and corrected scores, raw/source/configuration hashes and execution commits. Reproduce selected null, shift and correlation streams and the OULAD correction, compare numerical outputs excluding timings, and check plotted values against source tables. Link important claims to exact tables and configurations, retaining negative results, ties and unsupported groups. Freeze the verified evidence set locally. This freeze does not choose the student's final project version and does not write their final results section.

# What changed, and what the charts mean

AI-assisted explanation prepared 11 October 2026. This is assistance for the student's interpretation, not a submission written in the student's voice.

SubPSI compares the distribution of an input separately within declared groups. PSI measures differences between bin proportions. KS compares cumulative distributions without those bins. Both receive the same records within each collection policy. Neither an input difference nor a prediction error automatically demonstrates discrimination.

## Correction already present at the starting commit

The original Version 3 OULAD attempt bins were `[-infinity, 0, infinity]`. Every allowed nonnegative count fell together, so the representation discarded the difference between never attempting a course before and repeating it. The prior correction, preserved here, uses **0, 1, 2 or more, and missing**, with half-integer boundaries. Its rule came from the variable definition and the 2013J historical design: 314 zeros, 45 ones and 13 counts of two or more. Negative, fractional or infinite attempts are rejected; missing values remain separate. The frozen model was not refitted.

The earlier correction changed overall descriptive attempt PSI from about **0.00172 to 0.02923**; KS stayed **0.04457**. KS did not use the faulty bins. The old small nonzero PSI despite collapsed observed counts reflects the pseudocount/sample-size interaction; it was not meaningful separation of attempt levels. This is a **known-problem correction on previously examined cohorts**, not untouched confirmation. All original outputs remain available. Only 4/9 OULAD views have sufficient fixed reference support under the previous 50/100 rules.

Revision 4 verifies those results and adds an explicit audit. It reports distinct historical values, occupied bins, configured bins, missingness and the largest observed-bin share. The effective-bin number is `1 / sum(bin_share squared)` for observed numeric records, so a heavily dominant bin can leave this number near one even when several bins are occupied. The corrected attempts occupy three bins, but the effective number is only **1.373**, because 84.4% of the historical records are zero. The software distinguishes this imbalance from accidental collapse. A genuinely constant feature gets its own status and is not automatically a coding failure.

## Chart 1: the representation repair

[Open chart and exports](../../figures/revision4/preparation/index.html). Exact source: [01_oulad_representation.csv](../../figures/revision4/preparation/01_oulad_representation.csv).

Both panels contain the **same 372 historical students**. The left panel shows how the original representation merged their attempt counts. The right shows what the corrected representation retains. The graph demonstrates a representational correction; it does **not** prove later drift, better prediction, unfairness or PSI superiority. Both sources and the complete audit are saved in `results/summary/revision4/preparation-02/`.

## Chart 2: put the model next to a simple prediction rule

Exact source: [02_oulad_prediction_baseline.csv](../../figures/revision4/preparation/02_oulad_prediction_baseline.csv). Complete group/complement, earlier/later metrics: [oulad_outcomes_extended.csv](../../results/summary/revision4/preparation-02/oulad_outcomes_extended.csv).

The constant rule always predicts successful completion because 438/757 historical training records had that label. Its class was not selected from the audit results. Ties would predict class 0. The later audit contains 973 records: 547 successes and 426 non-successes. The frozen model gets **541/973 = 55.6%** correct; the constant rule gets **547/973 = 56.2%**.

TPR asks what fraction of actual successes are predicted positive. FPR asks what fraction of actual non-successes are incorrectly predicted positive; lower is better. A constant-positive rule has both rates equal to 100%, illustrating why its high TPR alone is not useful. Balanced accuracy averages TPR and the true-negative rate, weighting the two classes equally. The model has **50.9%**, versus **50.0%** for the constant rule. That small descriptive difference does not establish reliable predictive value or general superiority. The outcome model is weak; no large classifier search is being launched.

Each ordinary metric requires at least 20 records in its denominator. Balanced accuracy requires at least 20 positives and 20 negatives; both denominators are shown. Unsupported values stay blank with explicit status, not zero. These additions are arithmetic on saved confusion counts, not a new model fit or later-label choice. The held-out cohort is not treated as many independent experimental replications.

## What the new collector does

A target is the number of incoming group records to wait for before testing. The new collector accepts a separate target for each group, frozen in an immutable plan. It does not look at feature values, outcome labels, PSI, KS or p-values when deciding to collect or reset. A group can therefore have a reference gate of 50 and an incoming target of 400; those are different requirements. Whole delivery batches stay intact, including overshoot. PSI and KS share the same completed blocks.

The new tests check that changing later feature values and labels cannot change the map or schedule, that reference shortages remain visible, that empty deliveries spend a look, and that completed blocks and error budgets do not restart opportunistically. Source/draw checks retain whole records and disclose repeated use. These are software checks, **not evidence that calibrated collection improves detection**.

## What is still unknown

No real-data historical sensitivity estimation, selection of calibrated targets or new policy evaluation has run. There is no sensitivity graph or fitted target map yet. The [one proposed protocol](PROPOSED_PROTOCOL.md) specifies the approval checkpoint. It can produce a failed criterion, identical maps, longer waiting or a KS advantage; those results will be kept. A non-alert does not certify stable inputs or fairness. No new algorithmic novelty claim is supported at this stage.

The prior Version 2 matched extension is already complete and independently replay-checked. It remains labelled synthetic evidence, separate from real records. Its aggregate results do not support a PSI-specific advantage. See the unchanged [correction findings](../correction/FINDINGS.md) for complete denominators and paired comparisons.

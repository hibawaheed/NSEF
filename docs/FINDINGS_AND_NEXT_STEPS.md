# Findings from the first saved run set

**Technical evidence note prepared with AI assistance, 11 October 2026. This is not the student's paper or final interpretation.**

The repository now contains 360 synthetic runs (60 per scenario), 80 Adult semi-synthetic runs (40 per condition), and six separate software smoke runs. No configured experiment failed. All 36 software tests passed after one plotting regression was repaired. Every figure is linked to saved source tables and run/configuration hashes.

## What these results support

- In S2, the constructed intersection-cancellation case, B2 flagged all four changed signal-feature intersections in the first changed window in **60/60 runs**. Its post-onset alert proportion was 100% (95% Wilson interval 94.0–100%). Aggregate and single-attribute feature distributions are unchanged in this scenario's population; their occasional alerts are sampling false alarms for those distributions.
- In S1, a concentrated measurement shift affecting 10% of observations, **both A1 and B2 alerted within the four-window horizon in 60/60 runs**. At the first changed window, A1 alerted in 55/60 and B2 in 60/60. The timing difference is exploratory and is not a demonstrated general superiority result.
- In the Adult injection condition, **A1, B1 and B2 all alerted within the three-window horizon in 40/40 runs** (95% conditional Wilson interval 91.2–100%). The aggregate fixed 0.1-threshold baseline alerted in 0/40. Comparing only against that fixed threshold would overstate the advantage of subgroup monitoring.
- Under S0, naive all-subgroup PSI ≥0.1 produced a first-window alert in **58/60 runs** (96.7%). B2 with Holm produced one in **1/60** (1.7%; 95% Wilson interval 0.3–8.9%). This shows a major practical safeguard benefit in this specific setting, not invention of statistical correction or proof of a universal error guarantee.

## Limits that materially restrict the claim

1. **Repeated monitoring:** B2 gave at least one erroneous alert in **12/60 complete six-window S0 streams** (20.0%; interval 11.8–31.8%). Per-window Holm correction is not stream-wide control. A deployment claim needs a declared horizon-wide strategy and an explicit power/cost comparison.
2. **Input drift is not outcome harm:** all B2 runs alerted in S3 even though only the unused nuisance feature shifted. The mean A-group TPR-gap change was −0.31 percentage points (95% interval −0.87 to +0.25).
3. **Outcome-only failure:** in S4, B2 alerted in only **6/60** post-onset horizons (10.0%, interval 4.7–20.2%) while the mean measured TPR-gap increase was **5.47 percentage points** (95% interval 4.54–6.40). These are input false alarms, not reliable detection of outcome change. SubPSI cannot replace labelled outcome monitoring.
4. **Choice of outcome metric matters:** S2's marginal A-group TPR gap hides much of the intersection-level change. Figure 11 therefore reports intersection TPRs. A single marginal fairness measure is insufficient.
5. **Small samples:** all configured input comparisons happened to pass the n≥50 gate. That is not evidence that smaller-group regimes work. The coverage figure is explicitly analytical. Some labelled outcome cells had only 11 negatives or 17 positives in synthetic windows and 19 positives in Adult, so individual-window outcome estimates can be noisy.
6. **Uncertainty and scope:** 60/40 repeats leave broad rate intervals. Adult reuses one finite historical dataset and fixed split; its intervals are conditional simulation uncertainty, not new independent-person evidence. Exact predictor deduplication cannot establish subject identity.
7. **Novelty:** earlier work already studies intersectional masking and sample-size tradeoffs. No general superiority to MSD, alternative drift tests, or commercial monitors is established.
8. **Estimator effects:** raw PSI is noisier at small group n. Absolute observed TPR gaps also have sampling bias, and baseline/live audit sizes differ. Treat gap changes as descriptive measurements with the saved denominators and S0 comparison, not automatic proof of unfairness.

## Does the idea work?

It works as an input-distribution monitor in these tested settings, and the constructed S2 example demonstrates a clear reason to include predefined intersections. These results **do not support a universal “detects hidden bias” or “beats aggregate statistical monitoring” claim**. If those universal claims are essential to the idea, the current evidence contradicts them. A narrower empirical study of detection, false alerts, coverage, and outcome relevance remains viable.

## Additions worth doing before stronger paper claims

- Add a small, pre-recorded grid of group shares, sample sizes and shift magnitudes; retain null and unsupported cases.
- Add imperfect cancellation cases to measure how quickly the intersection benefit disappears.
- Add an equivalently calibrated numeric KS comparator to separate benefits of subgroup stratification from benefits specific to PSI.
- Evaluate a stream-wide error policy without retrospectively choosing the rule from favorable results.
- Report full subgroup TPR/FPR, label counts and accuracy, and justify the outcome relevance definition. The raw data and diagnostic tables already retain them.
- Review the full prior literature and have the student explain the design and limitations in their own words.

Figures 1–6 and 9–11 are empirical; Figures 7–8 are analytical planning/teaching examples. Preserve those labels in the paper and judging presentation. The CSVs, not rounded prose, are the authoritative displayed values.

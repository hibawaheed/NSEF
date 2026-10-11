# Bounded correction completed — evidence for review

**Status: corrected results frozen locally; original Versions 1, 2 and 3 preserved. This is post-result work, not untouched validation. The final project version has not been selected.**

The OULAD previous-attempts histogram now distinguishes zero, one and two-or-more attempts. Its rule uses only the 372 historical design records (314 / 45 / 13). The sparse tail remains a limitation. Overall PSI changes from 0.001721 to 0.029233; KS remains 0.044566. The original small PSI was driven by smoothing unequal sample sizes across empty bins, because all valid counts fell in one occupied bin. A larger corrected distance demonstrates a repaired measurement, not better prediction, proven harm, or natural drift-detection accuracy.

The same four of nine OULAD group views qualify. The five unsupported groups stay visible. Credits, the cohorts, student splits, labels, groups, thresholds and logistic parameters are unchanged.

For example, zero prior attempts accounts for **310/362** reference students and **882/979** monitored students. The old bins could not represent this difference in proportions. The corrected count table shows it directly, without turning it into a known-change detection claim.

The simple predictor is fixed from 438 positive versus 319 negative historical training labels: always predict Pass/Distinction. On the later audit, the frozen logistic model correctly predicts **541/973 (55.60%)** versus **547/973 (56.22%)** for this baseline. On the earlier audit, logistic gets **229/392** versus **211/392**. The six-record later difference is descriptive, not a significance claim. Both TPR and FPR are 100% for an all-positive predictor; this is not a useful claim of fairness. No classifier search or retraining was performed.

## Matched Version 2 comparison

All **1,820 original synthetic streams** completed. Every original PSI score, support decision, block start and alert-group set passed the replay checks. Both statistics use the same complete blocks and alpha/20 budget with a fixed Holm family. No extra observations were given to either method. This is a retrospective comparison on the old benchmark, not a new prospectively untouched study.

| Batch size | Accumulated PSI: grid alerts | Accumulated KS: grid alerts | PSI null alerts | KS null alerts |
|---|---:|---:|---:|---:|
| 250 | 313/480 (65.2%) | 327/480 (68.1%) | 10/250 (4.0%) | 3/250 (1.2%) |
| 1000 | 417/480 (86.9%) | 425/480 (88.5%) | 12/250 (4.8%) | 4/250 (1.6%) |

On the completed shift grid, accumulated KS has more observed post-onset alerts at both batch sizes. This does not establish universal superiority; false alerts, exact localization, support and delay must also be read alongside it. The old PSI counts are reproduced, rather than replaced.

Grid denominators give equal weight to the original 12 settings per batch size. Any alert is not exact target identification. The source table contains stratified paired bootstrap intervals; null rates have Wilson intervals. The methods are separate 5% monitors, not a combined 5% PSI-or-KS rule.

- Original 5%-target, n=250, 1.4-SD example: PSI: 40/40 exact target alerts; restricted mean delay 7.325 batches; KS: 40/40 exact target alerts; restricted mean delay 6.875 batches.
- Original 2%-target, n=250, 1.4-SD example: PSI: 19/40 exact target alerts; restricted mean delay 14.175 batches; KS: 19/40 exact target alerts; restricted mean delay 14.175 batches.

Misses count as 15 batches in restricted delay. Support and waiting are identical between statistics because collection is shared. All 35 cases, including nulls, cancellation, gradual changes, missingness, benign shifts, outcome-only changes, composition and correlation, remain in the tables. None were removed for an unattractive result.

The added comparison addresses the missing comparator behind the old accumulation claim. Any benefit of pooling more observations should be credited to the shared collection policy unless a matched statistic comparison supports something narrower. **No new algorithmic novelty or general PSI superiority is established.**

The original Version 3 real-record controls remain separate and unchanged: exact target recovery is 0/30 for both accumulated statistics at both batch sizes. This negative result is not replaced by the synthetic study. Natural ACS comparisons are unchanged.

Benchmark execution: 1480.3 seconds wall time, 1474.7 seconds CPU; shared peak process RSS 162.1 MiB. These are local software costs, not deployment guarantees. Logical histogram/raw-array payload and separately instrumented Python allocations are not total monitor memory. KS warnings: 0.

## Reading and reproducing the frozen set

- [New chart pack](../../figures/correction/SubPSI_correction_chart_pack.pdf) and [interactive file index](../../figures/correction/index.html). Ten charts, each with PNG/PDF/SVG and a source CSV.
- [Plain-English chart guide](CHART_GUIDE.md).
- [Claim-to-evidence ledger](CLAIM_EVIDENCE.md), with machine-readable CSV/JSON alongside it.
- [Reproduction steps](REPRODUCE.md).
- [Change and AI contribution log](../../records/correction/WORK_LOG.md).
- [Freeze manifest](../../records/correction/FREEZE.json) binds the evidence hashes and code versions.

The freeze records the bounded evidence set requested in this correction. It does not choose a final submission version, certify competition eligibility, establish novelty, or claim independent student authorship. No final results section is written in the student’s voice.

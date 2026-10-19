# SubPSI — low-compute engineering addendum

Registered title: **SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis.**

This is the review branch `codex/subpsi-low-compute-20261018`, based on Version 4 at `39014345b53f4ff7fe8481e6aa9a996d00c10b5b`. The completed 18–19 October 2026 addendum makes the existing subgroup PSI implementation do less repeated work. It does not introduce a new detector, recalibration, dataset or classifier. No merge, website deployment or fair submission is authorized by the review-branch request.

Start with the [basic-English findings](../LOW_COMPUTE_FINDINGS.md), [claim-to-evidence ledger](../docs/low_compute/CLAIM_EVIDENCE.csv), [method and limitations](../docs/low_compute/METHOD_AND_LIMITS.md), and [reproduction instructions](../docs/low_compute/REPRODUCE.md).

## What the evidence supports

- **Exact checked scope:** 20 fixed-100 replays plus four fixed-400 replays, totaling 24 checked replays and 28,800 feature comparisons. All checked PSI histograms, scores, permutation outcomes, adjusted decisions and first alerts matched. The 54 corrected OULAD descriptive rows matched too.
- **Historical scope is larger:** the old fixed-100 study contains 220 streams. The other 200 fixed-100 streams were not verified with the optimized engine. Timing repetitions are not additional detection trials. Historical rates remain clearly labelled historical.
- **CPU:** on the same balanced 20-stream workload, five technical repeats gave median complete CPU time of 15.41 s for faithful original PSI-only versus 9.16 s for count-reuse PSI (40.6% lower). Median elapsed time decreased 37.8%. This is a one-machine measurement, not measured energy savings.
- **Memory:** median process peak RAM decreased only 0.7% (140.24 to 139.30 MiB). Optimized PSI used more RAM at the 10-batch prefix. Exact identity-validation storage grows with the stream; small histogram arrays do not imply constant total memory.
- **KS and scientific limits:** matched KS used less CPU in the strongest-change subset. PSI did not dominate KS in historical detection. Misses, false alerts, waiting, unsupported groups, failed 800-record policies, and the weak OULAD model relative to its training-majority baseline remain visible. Natural records do not establish known drift onset or natural detection accuracy. Histogram reuse is an implementation technique, not a new statistical invention.

## Final three figure groups

Use `figures/low_compute/final/`. Each figure has its exact saved CSV, a 300 dpi PNG, and vector PDF/SVG. The dated directory retains the earlier layout, with identical numerical CSVs.

| Figure | PDF | Source CSV | Other formats |
|---|---|---|---|
| Runtime and throughput | [PDF](../figures/low_compute/final/01_runtime.pdf) | [CSV](../figures/low_compute/final/01_runtime.csv) | [PNG](../figures/low_compute/final/01_runtime.png), [SVG](../figures/low_compute/final/01_runtime.svg) |
| Measured memory and state accounting | [PDF](../figures/low_compute/final/02_memory.pdf) | [CSV](../figures/low_compute/final/02_memory.csv) | [PNG](../figures/low_compute/final/02_memory.png), [SVG](../figures/low_compute/final/02_memory.svg) |
| Equivalence and historical trade-offs | [PDF](../figures/low_compute/final/03_equivalence_and_tradeoff.pdf) | [CSV](../figures/low_compute/final/03_equivalence_and_tradeoff.csv) | [PNG](../figures/low_compute/final/03_equivalence_and_tradeoff.png), [SVG](../figures/low_compute/final/03_equivalence_and_tradeoff.svg) |

Raw measurement CSVs are in [results/summary/low_compute/2026-10-18](../results/summary/low_compute/2026-10-18/). Individual process receipts and exact equivalence traces are in [results/raw/low_compute/2026-10-18](../results/raw/low_compute/2026-10-18/). The [benchmark configuration](../configs/low_compute/benchmark.json) and [execution manifest](../records/low_compute/2026-10-18/benchmark_execution_manifest.json) pin the observations, rules, environment and measured source-code hashes.

## Preservation, provenance and review checks

Eight binary cProfile `.prof` files are excluded from this branch and its new commit history at the user's request; local copies and original local commits are preserved. The readable [function profiling CSV](../results/raw/low_compute/2026-10-18/profile/functions.csv), all benchmark measurements and all charts remain available. The [public export record](../records/review_push/2026-10-19/PUBLIC_EXPORT.md) documents the exclusion and the earlier unreferenced Git-object transfer.

All 7,817 files present at the start of this addendum are preserved byte-for-byte. The [original root README](../README.md) is historical Version 1/2 documentation; it is intentionally unchanged. See [Version 4 findings](../docs/revision4/MAIN_FINDINGS.md) and [version history](../VERSIONS.md) for earlier evidence.

The measurement commit `0ca31347b216bb617ac071257386dc4331cf4407` and completed local package `0c156cb9b515dcacb6b974c1095c7923302f9abe` are original local provenance identifiers. Publication preparation retains those commits locally, while excluding local account paths and private-network commit metadata from outgoing history. The measured source-code hashes, results, chart CSVs and numerical profiler values remain unchanged. [Redaction records](../records/review_push/2026-10-19/REDACTIONS.json) and the original frozen manifest document the exact changes. These local commit IDs need not resolve on GitHub; use the published review commit and the execution manifest's file hashes to identify the implementation.

Read the [resolved deployment-gate check](../records/review_push/2026-10-19/DEPLOYMENT_GATE_RESOLVED.md), [earlier publication check](../records/review_push/2026-10-19/STATUS.md), [AI-use record](../records/low_compute/2026-10-18/AI_USE.md), and [change log](../records/low_compute/2026-10-18/WORK_LOG.md). The earlier Vercel API access problem remains recorded; authenticated browser inspection resolved the deployment gate without changing settings. AI-generated technical notes are not the student's final paper or evidence of mentor/fair approval. The submission deadline remains 26 October 2026. Development is stopped; this branch is for review and the paper stage.

This `.github/README.md` is the branch landing page so the original README need not be overwritten. GitHub documents this display priority in [About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).

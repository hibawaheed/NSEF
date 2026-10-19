# Low-compute findings - local engineering addendum, 19 October 2026

Registered title unchanged: **SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis.**

This is AI-generated technical evidence for discussion and the student's own writing, not a final submission in the student's voice. The session began 18 October and crossed midnight. The earlier scientific results remain frozen; this explicitly requested implementation addendum is dated honestly. Deadline: 26 October 2026.

## What changed

The new PSI path counts the fixed reference once, turns each incoming feature into bin codes once per batch, reuses group memberships, and adds integer counts across complete batches. It applies the original smoothing and statistical test when the original collection rule says a group is ready. It can read and write a batch at a time. It does less repeated copying and searching through tables.

The original implementation remains usable and unchanged. This improvement is beside it on local branch `codex/subpsi-low-compute-20261018`. The benchmarked implementation and tests are committed at `0ca3134`; all exact file hashes are in the [execution manifest](records/low_compute/2026-10-18/benchmark_execution_manifest.json). No push, merge, deployment, purchase, email or submission was performed in this pass.

## What stayed identical

Twenty fixed-100 saved runs and four fixed-400 runs were compared with Version 4. All **28,800 declared feature comparisons** matched: reference/current integer histograms, support, collection boundaries, PSI scores, permutation seed/draw hashes and extreme counts, stopping, p-values, Holm-adjusted values, hits and first alerts. There were **7,800 assessed tests** and **5,958,957 actual permutation draws** in that trace check. Maximum PSI difference was **zero**. KS outputs matched too. Unsupported tests remained present.

The corrected OULAD replay also matched all 54 descriptive feature rows exactly across its three existing policies, using the same 0 / 1 / 2+ attempt bins. An initial comparison exposed pandas' default CSV float parsing (difference under 1e-16); reading the saved decimals with round-trip precision recovered exact equality. No tolerance was relaxed and no model was refitted. All **137 Python tests** passed; the browser-core test also passed during this session.

This checks selected replays, not every one of the 220 historical streams. Timing repetitions are not additional detection trials.

## What was actually measured

Each row below covers the same 20-stream, four-condition workload: 20 batches of 1,000 incoming records and a 10,000-record reference per stream. One warm-up was excluded, followed by five alternating-order technical repeats in fresh processes on this machine. Complete execution includes imports, loading, exact ID checks, setup, monitoring and scientific-output writing. Original source preparation and old calibration/model fitting are separate costs.

| Implementation | CPU seconds, median [min-max] | Wall seconds, median | Peak RAM, median MiB |
|---|---:|---:|---:|
| Faithful original PSI-only | 15.41 [14.05-15.94] | 16.50 | 140.24 |
| Count-reuse PSI | 9.16 [8.21-11.83] | 10.26 | 139.30 |
| Matched KS-only | 10.90 [10.58-13.65] | 12.17 | 141.41 |
| Aggregate PSI (less scope) | 3.74 [3.56-3.81] | 4.62 | 137.96 |

Compared with the faithful PSI-only baseline, count-reuse PSI used **40.6% less complete CPU time** and **37.8% less wall time** by these medians. Monitoring-only CPU was 13.38 versus 6.87 seconds. Complete throughput increased from about 24,246 to 38,983 incoming records per second.

Peak RAM improved by only **0.94 MiB (0.7%)** on the primary workload. The 10-batch prefix used **1.31 MiB more** with optimized PSI. There is no uniform or large RAM-saving claim. The histogram arrays occupy 6,720 bytes, but the detector's Python objects occupy about 30 KiB, the retained exact-ID audit about 4.6 MiB at a full stream's end, and the full process about 139 MiB. Those are different quantities, not interchangeable system requirements.

KS was faster in the strongest-change subset: optimized PSI used 2.703 versus KS 2.569 CPU seconds for five streams, about 5.2% more (imports excluded from this condition subtotal). PSI was cheaper on the balanced workload median, not universally cheaper. Aggregate PSI was much cheaper because it checks only Everyone; it cannot replace the subgroup method's scope. Technical timing ranges overlap in some comparisons and are not confidence intervals across machines.

The smaller fixed-400 check and both prefix checks are retained in [all cost summaries](results/summary/low_compute/2026-10-18/cost_summary.csv), including unfavorable memory results. Per-condition timing, per-batch latency and all raw repeats are available beside it. No conditions, permutations or hard tests were dropped.

## Which three figure groups to use

1. [Runtime and throughput](figures/low_compute/final/01_runtime.pdf): shows the measured compute saving and labels aggregate PSI's smaller scope.
2. [Measured RAM and separate state accounting](figures/low_compute/final/02_memory.pdf): shows why tiny histogram arrays do not mean a tiny complete system.
3. [Equivalence and retained scientific trade-offs](figures/low_compute/final/03_equivalence_and_tradeoff.pdf): separates the new exact replay check from old detection, false-alert, coverage and waiting results, including the failed 800-record policies.

Each has an exact same-name source CSV, 300-dpi PNG and vector SVG. Use `figures/low_compute/final`; the earlier layout is preserved. These are full-width figures, not narrow-column miniatures.

## What to explain to a mentor

The defensible claim is an implementation improvement with identical results on the tested replays. Histogram reuse is not a new statistical invention. Exact duplicate-ID auditing remains in RAM and grows with the stream; this is not constant total memory. Source preparation, calibration and training costs are not hidden inside the monitor-only claim. CPU time is not measured energy use or a deployment guarantee.

The historical scientific limitations remain: the 800 targets failed their criterion and never assessed the target, PSI did not dominate KS, and the frozen OULAD predictor performed worse in ordinary accuracy than the training-majority baseline. Actual ACS/OULAD observations remain descriptive; constructed resampling is not new people or natural drift-detection accuracy. The registered title does not establish mentor/fair procedural approval.

See the [claim-to-evidence ledger](docs/low_compute/CLAIM_EVIDENCE.csv), [method and limits](docs/low_compute/METHOD_AND_LIMITS.md), [reproduction notes](docs/low_compute/REPRODUCE.md), and [AI/change log](records/low_compute/2026-10-18/WORK_LOG.md). The bounded pass is complete; development stops here so the next stage can be the paper.

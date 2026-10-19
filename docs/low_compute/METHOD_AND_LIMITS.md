# Local low-compute addendum: method and boundaries

Registered title, unchanged: **SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis.**

This session began 18 October 2026 and crossed midnight into 19 October in Pakistan. It is the explicitly requested bounded engineering addendum after the earlier planned 18 October scientific freeze; it does not backdate that freeze or reopen calibration. Submission remains 26 October. No mentor/fair approval is inferred from the user's authorization.

## What is compared

A is a mechanical PSI-only extraction of `run_frozen_targets` from reviewed Version 4. It retains the full current stream, original scheduler, repeated reference/current frame slicing and histogram rebuilding. Only the KS computation and KS decision dispatch are removed. Additional timers, an optional trace, and an explicitly labelled prefix-cost mode do not change full-stream decisions. `extract_baseline.py` documents the extraction; equivalence compares it to saved Version 4 output. We do not compare PSI-only work to the old combined PSI+KS workload and call the difference a speedup.

B caches reference integer histograms, encodes each incoming feature once, reuses each group selector, and adds per-batch integer counts. It invokes the unchanged count permutation test only on completed blocks, using the original seed `[seed, look, group_index, feature_index, single_or_accumulated]`. Smoothing is applied to completed histograms inside that original test. Conservative stopping, chunk size 64, 23,999 maximum draws, missing/tail bins, reference gate 50, fixed targets, whole-batch overshoot and look budget remain unchanged. All 30 groups and 60 group-feature tests remain in the intersection family, including unsupported p=1 entries. Labels are not detector inputs.

C consumes the same records with the same scheduler and caches raw per-group reference arrays. It retains pending current arrays for the unchanged `ks_score` and `ks_missing` functions. Those preserve exact SciPy KS, Fisher missingness, the factor-two adjustment and warning-to-p=1 safeguard. This is a reasonable cached-reference KS-only comparator, not a deliberately slow row-lookup comparator. Its existing exact-test routines still sort/work on raw arrays; no new KS algorithm is claimed. Identical nominal budgets do not mean identical realized false alerts or sensitivity.

D uses the optimized PSI path with Everyone only (two features). It is a lower-scope cost reference, not equivalent subgroup monitoring. Its cheaper cost must be explained with that smaller scope.

## Validation and memory

The unchanged `FrozenTargetScheduler` remains a separate exact-ID/provenance layer. It retains pending ID tuples and a seen-ID set. A second exact set checks all incoming IDs against reference and earlier batches, including any records outside declared groups. A block digest is only an identity summary, never a substitute for exact duplicate checks. Original source-archive hashes, role files, household-role separation and whole-record draw identity were verified before preparing the reusable input files. Prepared batches are hash-checked again on each timed read.

PSI feature state uses cached reference/current counts rather than a retained full feature stream. The caller can consume an iterator and write one look at a time; `run_lightweight` is an optional collecting convenience function used for checks, not the streaming benchmark. The current batch, Python/pandas objects, bin metadata, counters, IDs, output buffers and permutation temporaries still consume RAM. Exact ID auditing grows with total stream length. This is **not constant total memory**, and histogram bytes are not whole-process RAM. End-of-stream object accounting is explicitly distinct from measured process peak RSS and from peak transient usage.

The incremental path validates an arrival before mutating that look's state. Unlike the old offline prevalidation of the entire supplied stream, it cannot reject a future bad arrival in advance. Such an error aborts the run; previously yielded looks are only a prefix. A complete evidence run is accepted only after exhausting the declared horizon. This interface difference is documented, not a changed scientific decision on valid inputs.

## Bounded workload and timing boundaries

The selection was saved before profiling/timing: first five existing Version 4 runs for each of unchanged, age-up2, age-up4 and age-down4, with fixed-100 accumulation. Secondary workload: first run of each condition at fixed 400. Scaling: first 5 and 10 deliveries of the first age-up4 stream; the full 20-delivery run already exists in the main workload. The horizon and alpha/20 stay unchanged for prefixes; those runs measure cost, not new detection power. Records are genuine public ACS values replayed from the existing constructed resampling experiment, not additional respondents or real chronological arrivals.

One complete warm-up per implementation/workload is excluded, then five alternating-order technical repeats use fresh sequential processes, the same interpreter/libraries/hardware, and numerical thread limits of one. Inputs are freshly loaded in every process. Source preparation is a separately measured one-time stage, including the original role and lineage checks. Calibration/model fitting are excluded from per-monitor execution and remain documented historical costs.

Complete worker time begins before imports and includes configuration/hash checks, loading, validation, setup, monitoring, JSONL serialization, output flush/fsync and cleanup. Parent-observed process wall time additionally includes launch/exit overhead. Monitoring time subtracts measured loading, validation, setup, output and instrumentation/accounting; complete time is the most comparable operational quantity. Phase boundaries are not identical internal workloads: A's validation includes full-stream materialization, while B/C encode arrivals during validation. Per-batch latency includes collection/testing/adjustment/accounting, excludes disk reads and output. Five-repeat min/max are observed technical spread, not confidence intervals over independent people or machines. OS cache state is not forced cold; the host is not an isolated deployment appliance.

Peak RSS is the fresh process's Linux `ru_maxrss`, including imports, data, validation, outputs and temporaries. The process executes multiple streams in sequence, so the peak is for the bounded workload rather than a claim about one individual batch. Throughput counts incoming records only (20,000 per full stream), although complete execution also loads 10,000 reference records per stream. Prefix scaling reuses existing inputs and does not fabricate larger independent datasets.

## Scientific meaning retained

Exact numerical replay checks cover the declared 20 fixed-100 and four fixed-400 runs, not all 220 Version 4 streams. The complete historical detection/false-alert table remains old evidence from the unchanged engine. It is shown as context and is not relabelled as a new 220-stream validation of B. The timing runs do not increase detection denominators. The failed 800-record policies, original weak controls and KS advantages remain in Version 4. Natural ACS/OULAD comparisons stay descriptive; no natural drift accuracy, fairness repair, causal-harm conclusion, deployment guarantee, energy saving or algorithmic novelty is established.

Reusing histograms and selector masks is an implementation technique. This pass evaluates measured costs while keeping the registered scientific topic and prior limitations intact.

## Documentation checked against the installed environment

Installed Python 3.14.8, NumPy 2.5.4, pandas 3.0.6 and SciPy 1.18.1 are recorded in the execution manifest. NumPy's 2.5 documentation describes integer bin counting with `bincount` and count-vector sampling without replacement with `Generator.multivariate_hypergeometric`; the existing test uses the latter with unchanged inputs and RNG calls. Python's 3.14 documentation distinguishes elapsed performance-counter time from process CPU time, and defines `ru_maxrss` as maximum resident set size. CPU time does not measure joules or battery use.

- [NumPy 2.5 bincount](https://numpy.org/doc/2.5/reference/generated/numpy.bincount.html)
- [NumPy 2.5 multivariate hypergeometric count sampling](https://numpy.org/doc/2.5/reference/random/generated/numpy.random.Generator.multivariate_hypergeometric.html)
- [Python 3.14 timing clocks](https://docs.python.org/3.14/library/time.html)
- [Python 3.14 process resource usage](https://docs.python.org/3.14/library/resource.html)

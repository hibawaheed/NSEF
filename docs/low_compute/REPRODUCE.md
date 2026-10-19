# Reproduce or inspect the local low-compute addendum

Run from the repository root. The full measured execution is pinned to local commit `0ca3134`; the execution manifest also hashes every benchmark source file, Python/dependency versions, hardware, source inputs and configuration. The starting Version 4 is `39014345b53f4ff7fe8481e6aa9a996d00c10b5b`. Publication preparation changes reporting and package verification only; the 19 measured source files remain unchanged. Keep the locked environment; no dependency upgrade is part of this pass.

## Check delivered evidence without new experiments

```sh
python scripts/low_compute/verify_package.py
python scripts/revision4/verify_snapshot.py
python -m pytest -q
node --test web/core.test.mjs
```

The first checker reads saved results and hashes only. The existing snapshot checker verifies the earlier evidence. Unit tests use teaching fixtures, not research records. The final Python test result for this code was 137 passing tests.

Key files:

- `configs/low_compute/benchmark.json`: selection saved before timing; input batch hashes and original-result links; exact scopes and repetition rules.
- `records/low_compute/2026-10-18/benchmark_execution_manifest.json`: frozen measured-code/environment hashes and timing boundaries.
- `results/raw/low_compute/2026-10-18/benchmark/*.json`: every process receipt, including excluded warm-ups. `process_wall.csv` includes parent process wall time and receipt hashes.
- `results/summary/low_compute/2026-10-18/process_measurements.csv`, `stream_measurements.csv`, `batch_latency.csv`: tidy raw measurements. `cost_summary.csv` reports medians and observed min/max, not population confidence intervals.
- `results/raw/low_compute/2026-10-18/equivalence`: histogram/seed/RNG/extreme-count traces and explicit selected-run pass summary. New timing observations do not increase detection counts.
- `results/raw/low_compute/2026-10-18/oulad_equivalence.json`: descriptive OULAD replay checks.
- `results/raw/low_compute/2026-10-18/profile`: readable profiling CSVs and numerical diagnostic result records. The eight binary cProfile `.prof` files are retained locally and excluded from the review branch at the user's request. The public package checker does not require those binaries. These diagnostic runs are excluded from reported timings; cumulative function times overlap.
- `figures/low_compute/final`: exactly three final figure groups with PNG/PDF/SVG and exact CSVs. The earlier dated directory preserves the first layout; its numeric CSVs are identical.

## Run a fresh bounded reproduction in an isolated directory

Do not overwrite delivered timing files or delete the evidence to make scripts run. All experiment-producing entry points refuse their existing output directories. Use a separate checkout/export based on the pinned implementation, with a new output root. The scripts' date-scoped directories (`2026-10-18`) identify this original session; for a new run, copy the scripts/config into a clearly named reproduction workspace and replace only output-directory paths, then record the resulting code hashes. Never change seeds, input selection, target, groups, permutations, horizon or thresholds. The source/config hashes in original results still need to match.

Prepare the original source cache using the existing Version 3/4 reproduction instructions, then reconstruct the exact Version 4 private draw lineages. Source records/IDs remain in ignored `data/raw`; they are not exported into figures or created as replacement respondents. If the verified cache is unavailable, stop the numerical replay rather than substitute data. No source downloads were needed for this pass.

The original workflow, in order, was:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0
python scripts/low_compute/prepare.py
python scripts/low_compute/profile_existing.py
python scripts/low_compute/verify.py
python scripts/low_compute/benchmark.py
python scripts/low_compute/verify_oulad.py
python scripts/low_compute/report.py --figures figures/low_compute/reproduction-001
```

Preparation recreates existing records with their original RNG namespaces, checks exact saved source/draw lineages and role separation, and writes per-batch numeric NPZ replay files under ignored `data/raw/low_compute`. These include authentic recorded feature/group values. No randomization changes or new trials occur. It records this one-time preparation time separately. The benchmark consumes these batches with no source-pool preload in optimized processes. Original results and the NPZ inputs must match their saved hashes.

For the delivered checkout, a new set of figures can be rendered directly from existing results using the last command above with an unused figure directory. The reporter recomputes the same summary CSVs and checks all A/B output digests; copy the checkout first if preserving modification times is important. It also checks the aggregate comparator against original aggregate scientific outputs. Scientific outputs for the timed worker replays live in ignored `data/raw/low_compute/2026-10-18/benchmark_outputs`; if absent, regenerate verified inputs/outputs in the isolated reproduction workspace first.

Timings will vary on a different host. Exact scientific outputs and counts should agree within the declared method; any unexplained alert/p-value difference is a failure, not something to fix by increasing tolerance. The originally declared absolute PSI tolerance was 1e-14, but all delivered selected-replay checks attained exact equality. OULAD CSVs must be parsed with round-trip floating precision; the initial default-parser diagnostic is preserved.

The primary benchmark has 20 streams. Fixed-400 has four streams. Prefix checks contain one existing strongest-change stream truncated at 5 or 10 input deliveries for cost measurements while retaining horizon20/alpha20. These workloads have different scope and process-startup amortization: do not compare their total CPU as equal-sized workloads. The prefix20 component-accounting point comes from the corresponding full primary stream, not a separate larger dataset.

## Minimal fresh timing replay with the delivered cache

To repeat one exact primary workload without changing any code or saved evidence, choose an unused output file and repeat label (the label selects output paths, **not** the detector seed):

```sh
mkdir -p work/low-compute-replay-001
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
python scripts/low_compute/worker.py --variant B --workload primary --repeat 99 --out work/low-compute-replay-001/B.json
```

Use A, C or D with the same label and different output filename for the other implementations. The worker rejects a reused output directory and checks the frozen code/config/input hashes. A result with label99 is a new technical timing receipt, not a new scientific replicate. Reproduction requires the original cached NPZ files; this read path does not acquire or fabricate data.

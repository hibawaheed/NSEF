# Reproducing the approved revision-3 study

Use the existing NSEF repository root. No paid services, model API, scikit-learn, or remote deployment is required. All commands below are local except the two public-source retrieval commands. The original v1/v2 artifacts and preparation files are preserved.

## Environment and sources

The main execution used Python 3.14.7 with the versions in `requirements-lock.txt`; full environment/platform details are in the manifests. Create a local virtual environment and install the locked dependencies if needed. The existing workspace interpreter is `/home/hiba_w/Documents/Codex/2026-10-11/hey/work/venv/bin/python`.

On a fresh checkout without the ignored source cache:

```sh
python scripts/revision3/fetch_sources.py --only acs
python scripts/revision3/extract_oulad_metadata.py
python scripts/revision3/inspect_support.py --dataset acs --out results/raw/revision3/reproduced-acs-feasibility
python scripts/revision3/inspect_support.py --dataset oulad --out results/raw/revision3/reproduced-oulad-feasibility
```

The compact OULAD extractor reads original ZIP members and verifies their CRC/size/hash. It does not need the click-log table. It refuses an existing metadata directory; skip extraction when the verified local cache already exists. Inspectors recreate the private deterministic role files used by the loader. Download availability is external; do not substitute a different dataset/version if an expected hash fails. Receipts and the original raw-run manifest identify the expected sources. Private source records/lineage remain under ignored `data/raw/revision3/`, not figure exports.

## Numerical reproduction

Use new output names; scripts intentionally reject existing output directories. The approved configuration is `configs/revision3/approved.json`, and its hash is bound to the approval record. The historical `proposed.json` intentionally remains unapproved as an immutable record of the earlier review stage.

```sh
python -m pytest -q
python scripts/revision3/run_main.py --out results/raw/revision3/reproduction-001
python scripts/revision3/summarize_main.py --raw results/raw/revision3/reproduction-001 --out results/summary/revision3/reproduction-001
python scripts/revision3/plot_main.py --raw results/raw/revision3/reproduction-001 --tables results/summary/revision3/reproduction-001 --out figures/revision3/reproduction-001
python scripts/revision3/verify_main.py --raw results/raw/revision3/reproduction-001 --tables results/summary/revision3/reproduction-001 --figures figures/revision3/reproduction-001
python scripts/revision3/diagnose_main.py --out results/summary/revision3/reproduction-001-diagnostics
```

Set `MPLCONFIGDIR` to a writable cache directory if Matplotlib requires it. Data/settings/seeds are fixed; runtime, platform memory readings, creation dates and export metadata can differ. The verifier excludes runtime fields for exact numerical replay and checks source snapshots against their recorded per-file hashes. Main computation has a two-hour CPU cap and leaves a failure record rather than changing the design after a timeout. The completed original main run used about 5.4 minutes wall time and 301 MiB high-water RSS on this machine; this is not a hardware-independent promise.

To verify existing delivered results without rerunning the main study:

```sh
python scripts/revision3/verify_preparation.py
python scripts/revision3/verify_main.py
```

The second command checks the delivered artifacts and replays the first fixed stream in each of the four design cells. `--no-replay` only repeats hash/result-integrity checks, useful after a figure-layout-only change. It does not replace the original full replay check.

## Authoritative output locations

- Natural and constructed raw results: `results/raw/revision3/main-approved/`.
- Corrected complete-stream summaries: `results/summary/revision3/main-approved-checked/`.
- Checked final chart exports: `figures/revision3/main-approved-checked/`.
- Explicitly post-run bin/source diagnostics: `results/summary/revision3/postrun-diagnostics/`.
- Approval, command outputs, verification and factual logs: `records/revision3/main/`.
- Scientific explanation: `docs/revision3/MAIN_FINDINGS.md`; basic graph guide: `CHART_GUIDE.md`.

`results/summary/revision3/main-approved/` is the preserved failed first summary attempt, with `FAILED.json`. `figures/revision3/main-approved/` contains the numerically valid first chart exports with the caption-layout issue; use the checked directory for presentation. These records were not overwritten. The experimental raw directory has no replacement run.

## Interpretation and reproducibility limits

Thirty repeated streams are Monte Carlo replicates conditional on fixed empirical pools, not thirty new sampled populations. Bootstrap units are complete paired streams. Natural data remain descriptive, and weights are preserved but not used for population estimates. Source/role hashes and immutable snapshots permit reconstruction; they do not remove sampling, dependence, binning or weak-baseline limitations. See the main findings before using any chart in a paper.

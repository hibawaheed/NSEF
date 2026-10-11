# SubPSI

**SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis**

This repository compares aggregate and predefined subgroup input-drift monitors, with explicit statistics, sample-size coverage, and separate model-outcome measurements. An input-distribution alert is not proof of unfairness. The current implementation is an exploratory evidence package, not a deployed monitoring service or a fairness guarantee.

## Outputs

After running the commands below, open `figures/report/index.html` for the local chart gallery, or `figures/report/SubPSI_chart_pack.pdf` for all figures. Each figure also has an editable SVG, vector PDF, 300 dpi PNG, source CSV and JSON provenance manifest. Figures 7 and 8 are analytical planning/teaching examples; the others summarize saved experiments.

- `docs/FINDINGS_AND_NEXT_STEPS.md`: measured findings, limits and next additions.
- `docs/STARTING_STATE.md`: original code audit and actual initial state.
- `docs/EXPERIMENT_SETTINGS.md`: all experimental choices and limits.
- `docs/ADDITIONS_AND_LIMITATIONS.md`: additions, unfinished work and failure criteria.
- `records/CHANGELOG.md`: task change log.
- `records/AI_USE.md`: disclosure of AI-assisted implementation and graphics.
- `legacy/subgroup_psi_original.py`: untouched original for comparison.

## Reproduce

From this repository directory, use Python 3.14 to reproduce the delivered lockfile. Other compatible package/Python combinations have not been tested:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/audit_original.py
.venv/bin/python scripts/run_synthetic.py --config configs/smoke.json --out results/raw/smoke-reproduction
.venv/bin/python scripts/run_synthetic.py --config configs/synthetic.json --out results/raw/synthetic-reproduction
.venv/bin/python scripts/fetch_adult.py
.venv/bin/python scripts/run_adult.py --config configs/adult.json --out results/raw/adult-reproduction
.venv/bin/python scripts/make_figures.py --synthetic results/raw/synthetic-reproduction --adult results/raw/adult-reproduction --out figures/reproduction
.venv/bin/python scripts/summarize_diagnostics.py --runs results/raw/synthetic-reproduction --out results/summary/synthetic-reproduction
.venv/bin/python scripts/validate_assets.py --figures figures/reproduction
```

Run commands create new directories and refuse to overwrite existing results. Use a new output name for another run. `fetch_adult.py` reuses an existing download only when its saved hashes verify; it will not silently replace a dataset. To rebuild only the delivered charts, point `make_figures.py` at `results/raw/synthetic-v1` and `results/raw/adult-v1` and choose a fresh figure directory. Running `scripts/summarize_diagnostics.py` on Adult results produces equivalent conditional diagnostics.

No cloud resources, paid jobs or network access are required after dependencies and Adult have been downloaded. A single local CPU process runs the numerical work. Actual software versions, execution times, source hashes, configuration, seeds, sample counts and failures are saved in the run manifests/results. Source/configuration snapshots accompany the run directories. Scientific reproducibility concerns numerical tables; PDF creation timestamps need not match byte-for-byte across regenerations.

## How the comparisons work

A0 uses aggregate PSI ≥0.1. A1 applies Holm to aggregate feature tests. B0 uses the same practical threshold across all predefined groups. B1 includes aggregate and single-attribute tests under Holm; B2 adds four predefined intersections. The statistical families contain 2, 10 and 18 comparisons. These are different monitoring scopes at the same nominal per-window family-wise level. Fixed-threshold methods are contextual baselines, not error-matched competitors.

Design data fix the bins before the reference/current comparisons. Positive count pseudocounts are normalized separately. The histogram-count permutation sampler matches random reassignment without replacement of pooled labels. A p-value-resolution guard prevents an impossible first Holm rejection threshold. Unassessable declared comparisons remain visible with p=1. Holm's per-window guarantee is not a complete-stream guarantee.

Synthetic fit/design/reference/audit/live roles have independent random streams. Detector code does not consume `y`. Outcomes are used only to fit the historical model and evaluate its frozen predictions; no threshold adjustment or model updates occur. Repeated windows share a reference, so complete runs are the uncertainty unit.

## Public data and attribution

Adult is freely reusable with attribution under **CC BY 4.0**. It is not labelled copyright-free.

Becker, B. & Kohavi, R. (1996). *Adult* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5XW20 . [Provider](https://archive.ics.uci.edu/dataset/2/adult) · [License](https://creativecommons.org/licenses/by/4.0/).

The analysis removes duplicate predictor rows, splits roles, and samples simulated windows. It preserves source records and labels. There is no real time sequence and no basis for present-day Pakistani population claims. Intervals describe conditional Monte Carlo sampling from one finite historical split, not uncertainty from newly recruited independent people. Raw third-party files are gitignored and retrieved by a reproducible script.

AI assisted code, tests, factual checks and visual production. The student retains responsibility for understanding, interpreting and accurately disclosing the work. No remote publication, submission or signed paperwork is part of this repository task.

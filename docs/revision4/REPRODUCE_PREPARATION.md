# Reproduce the preparation without running the proposed experiments

Use the repository's recorded Python environment and already downloaded, ignored raw sources. Tested here with Python 3.14.7, NumPy 2.5.4, pandas 3.0.6, SciPy 1.18.1, matplotlib 3.11.2 and pytest 9.1.1; complete environment metadata is saved with each preparation manifest. The Python executable in this workspace is `/home/hiba_w/Documents/Codex/2026-10-11/hey/work/venv/bin/python`.

From the repository root:

```sh
python -m pytest -q
python scripts/revision4/inspect_preparation.py --out results/summary/revision4/replay-preparation --private-out data/raw/revision4/replay-lineage
python scripts/revision4/plot_corrections.py --source results/summary/revision4/replay-preparation --out figures/revision4/replay-preparation
python scripts/correction/verify.py --out records/revision4/replay-legacy-verification.json
```

Each output path must be unused. Do not delete previous successful or failed outputs to reuse a path. The final line reproduces existing correction checks; it does not rerun the whole synthetic campaign. All empirical inputs are authenticated against the earlier local retrieval hashes. A source mismatch stops execution. These hashes document exact retrieved bytes, not an external guarantee supplied by the data publisher.

`preparation/` is the first support/representation/reporting check. `preparation-02/` adds the proposed age-stratum support counts; both remain intact. Its feature inspection is historical support only. The only new outcome calculations are balanced-accuracy arithmetic from the saved OULAD confusion counts, with consistency checks. No model was refit and no prediction threshold was changed.

All preparation charts are in `figures/revision4/preparation/`, each with exact CSV, PNG/PDF/SVG and a hashed manifest. The new `revision4.py` source is separate from the original engines. Old source, tests, outputs and freeze records are unchanged. Provenance records identify the base SHA plus the precise source snapshot used while the new files were still uncommitted; the final local preparation commit is an additional locator, not a replacement for those snapshots.

The real-data calibration and stream runners will be completed under the approved protocol. No executable approval should be inferred from `proposed.json`; both authorization fields are false. Before executing that phase, save the actual user's approval, the approved configuration hash, role/source hashes, complete ordered cell/seed inventory and source snapshot. Preserve pointwise uncertainty, unmet targets, all family members and incomplete runs. No target map exists yet.

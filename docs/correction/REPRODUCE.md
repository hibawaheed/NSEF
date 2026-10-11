# Reproduce the bounded correction

Use the existing environment and `requirements-lock.txt`; no new package or paid service is required. Numerical execution commits are in each raw manifest, and source snapshots include the code and configurations used at that stage. A later reporting commit does not change the earlier numerical execution version.

## Inputs and roles

The original public source cache is required. See the [Version 3 data cards](../revision3/DATA_CARDS.md) and [main reproduction instructions](../revision3/REPRODUCE_MAIN.md) for official downloads, source hashes, licence attribution and eligibility/split reproduction. OULAD is attributed to Kuzilek, Hlosta and Zdrahal, distributed by the UCI Machine Learning Repository under CC BY 4.0, DOI 10.24432/C5KK69. The existing loader verifies downloaded-file and role-lineage hashes. It loads ACS too for the shared validation contract but this correction does not rerun its natural study or its resampling controls.

No row-level student data or private identifiers are newly exported. Public aggregate count tables retain small counts for research transparency; these anonymised source records and group labels should not be interpreted as identifiable students.

The synthetic comparison reconstructs the exact original V2 design/reference/window records from the saved seed and case definitions. No additional or replacement human records are created. All 1,820 existing raw V2 result hashes are checked, and each recomputation must preserve PSI scores, support, block starts and alert groups. Old nonsignificant Monte Carlo p-values may differ because conservative early stopping differs; this cannot create new rejections at the declared horizon cutoff.

## Commands from the repository root

Replace `python` with the prepared Python environment if necessary. Output directories must be new. Keep the current frozen outputs intact.

```sh
python -m pytest -q
python scripts/correction/run.py v2 --smoke --out results/raw/correction/replay-software-check
python scripts/correction/run.py oulad --out results/raw/correction/replay-oulad
python scripts/correction/run.py v2 --out results/raw/correction/replay-v2
python scripts/correction/summarize.py --raw results/raw/correction/replay-v2 --out results/summary/correction-replay
```

The correction runner enforces its 14 October 2026, 23:59:59 Asia/Karachi deadline and a two-hour benchmark wall-time cap. A full new evaluation after that date requires a separately documented reproduction mode or a new configuration; do not silently edit the original frozen configuration. Numerical verification of a few saved streams is available through the verification script and does not initiate a new main evaluation.

`summarize.py` uses the frozen corrected OULAD output and the specified V2 raw folder. `plot.py` reads the frozen `results/raw/correction/oulad` and `results/summary/correction` tables; give it a fresh `--out` directory to reproduce exports without replacing them. It exports ten charts, source CSVs, a combined PDF and an HTML file index. Matplotlib rendering can vary slightly across versions; the source CSV values, snapshot and environment records are authoritative.

```sh
python scripts/correction/plot.py --out figures/correction-replay
```

`verify.py` performs four numerical replays, checks original-file preservation, tests equality of collection/support for both methods across all streams and compares ten plotted CSV selections with their source tables. It refuses to overwrite the original verification record. `profile.py` likewise refuses to overwrite the separately recorded alternating-order cost check.

## Check the frozen bundle without modifying anything

```sh
python - <<'PY'
import hashlib, json
from pathlib import Path
p = Path('records/correction/FREEZE.json')
m = json.loads(p.read_text())
for name, expected in m['evidence_sha256'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
assert hashlib.sha256(p.read_bytes()).hexdigest() == p.with_suffix('.sha256').read_text().split()[0]
print('All frozen evidence hashes match')
PY
```

Original Version 1/2/3 artifacts retain their own manifests. The correction's preservation inventory hashes all 3,011 files that were tracked at the start. [Claim/evidence CSV](CLAIM_EVIDENCE.csv) and [JSON](CLAIM_EVIDENCE.json) link selected results to precise table selections, code versions and configurations. The freeze manifest defines the verified evidence set, not the student's eventual final submission choice.

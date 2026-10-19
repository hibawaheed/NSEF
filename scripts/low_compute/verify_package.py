"""Read-only final-package hash and key-table consistency verification."""
from pathlib import Path
import hashlib,json,csv
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(entries):
 for name,h in entries.items():
  p=(ROOT/name).resolve()
  if not p.is_relative_to(ROOT) or sha(p)!=h:raise ValueError('Hash mismatch: '+name)
 return len(entries)
def main():
 records=ROOT/'records/low_compute/2026-10-18'
 start=json.loads((records/'starting_inventory.json').read_text());print('Unchanged Version 1-4 files:',verify(start))
 freeze=json.loads((records/'FINAL_MANIFEST.json').read_text());print('Public low-compute package files:',verify(freeze['files']))
 local_only=freeze.get('local_only_files',{})
 if any(not name.endswith('.prof') for name in local_only):raise ValueError('Unexpected publication exclusion')
 present={name:h for name,h in local_only.items() if (ROOT/name).exists()}
 verify(present)
 print('Local-only profiler binaries excluded from public package:',len(local_only),'(present locally:',len(present),')')
 bench=json.loads((records/'benchmark_execution_manifest.json').read_text());print('Measured code files:',verify(bench['code_sha256']))
 if sha(ROOT/'configs/low_compute/benchmark.json')!=bench['benchmark_config_sha256']:raise ValueError('Selection changed')
 fig=json.loads((ROOT/'figures/low_compute/final/manifest.json').read_text());verify(fig['figures']);verify(fig['source_csvs']);verify(fig['original_source_sha256'])
 with (ROOT/'results/summary/low_compute/2026-10-18/process_measurements.csv').open() as h:rows=list(csv.DictReader(h))
 if len(rows)!=96 or sum(r['warmup']=='False' for r in rows)!=80:raise ValueError('Missing timed runs')
 with (ROOT/'results/raw/low_compute/2026-10-18/equivalence/summary.csv').open() as h:eq=list(csv.DictReader(h))
 if len(eq)!=24 or sum(int(r['feature_rows']) for r in eq)!=28800 or any(float(r['max_psi_difference'])!=0 for r in eq):raise ValueError('Equivalence scope mismatch')
 with (ROOT/'docs/low_compute/CLAIM_EVIDENCE.csv').open() as h:claims=list(csv.DictReader(h))
 for row in claims:
  if sha(ROOT/row['source'])!=row['source_sha256'] or sha(ROOT/row['configuration'])!=row['configuration_sha256']:raise ValueError('Claim ledger hash mismatch: '+row['claim_id'])
 print('Claim-source and configuration hashes verified:',len(claims))
 print('PASS: 96 process receipts, 80 timed processes, 24 exact scientific replays. No files changed.')
if __name__=='__main__':main()

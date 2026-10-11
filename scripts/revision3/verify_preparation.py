"""Validate preparation/provenance without running a main evaluation."""
from pathlib import Path
import hashlib,json,sys,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 baseline=json.loads((ROOT/'records/revision3/baseline_inventory.json').read_text())
 changed=[n for n,h in baseline['files'].items() if not (ROOT/n).exists() or sha(ROOT/n)!=h]
 assert not changed,changed
 print(len(baseline['files']),'pre-revision tracked files remain byte-identical')
 for folder in ['synthetic-v1','adult-v1']:
  path=ROOT/'results/raw'/folder;m=json.loads((path/'manifest.json').read_text())
  for name,h in m['result_hashes'].items():assert sha(path/name)==h,name
  assert sha(path/'source_snapshot.zip')==m['source_snapshot_sha256']
  print(folder,len(m['result_hashes']),'original raw hashes and source snapshot verified')
 for folder in ['acs-feasibility','oulad-feasibility-checked','matched-software-validation']:
  path=ROOT/'results/raw/revision3'/folder;m=json.loads((path/'manifest.json').read_text())
  for name,h in m['files'].items():assert sha(path/name)==h,name
  if 'source_snapshot_sha256' in m:assert sha(path/'source_snapshot.zip')==m['source_snapshot_sha256']
  print(folder,'saved files verified')
 # Verify versions at time of source/support execution, not a later edited script.
 snapshots=ROOT/'records/revision3/source_snapshots'
 acs=json.loads((ROOT/'results/raw/revision3/acs-feasibility/manifest.json').read_text())
 assert sha(snapshots/'inspect_support_acs.py.txt')==acs['script_sha256']
 assert sha(snapshots/'matched_acs.py.txt')==acs['group_code_sha256']
 oulad=json.loads((ROOT/'results/raw/revision3/oulad-feasibility-checked/manifest.json').read_text())
 assert sha(snapshots/'inspect_support.py.txt')==oulad['script_sha256']
 assert sha(snapshots/'matched.py.txt')==oulad['group_code_sha256']
 out=ROOT/'figures/revision3/feasibility';stem='01_support_feasibility';m=json.loads((out/f'{stem}.manifest.json').read_text())
 for name,h in m['source_files'].items():assert sha(ROOT/name)==h
 for name,h in m['files'].items():assert sha(out/name)==h
 assert sha(ROOT/'scripts/revision3/plot_support.py')==m['plot_code_sha256']
 assert min(Image.open(out/f'{stem}.png').info['dpi'])>=299
 print('Feasibility figure, CSV, plot code and source tables verified; PNG >=300dpi nominal')
 config=json.loads((ROOT/'configs/revision3/proposed.json').read_text())
 assert not config['main_evaluation_authorized'] and not config['comparison']['freshness_in_main']
 assert config['constructed_controls']['permutations']+1 >= 20*30*2/.05
 print('Main evaluation approval remains false; proposed control permutation resolution sufficient')
 # Verify every original raw source receipt, but never print respondent identifiers.
 for receipt in (ROOT/'data/raw/revision3/acs').rglob('*.receipt.json'):
  m=json.loads(receipt.read_text());p=receipt.with_name('csv_pma.zip');assert sha(p)==m['sha256']
 source=ROOT/'data/raw/revision3/oulad/metadata';m=json.loads((source/'receipt.json').read_text())
 assert sha(source/'source-prefix.bin')==m['prefix_sha256']
 for member in m['members']:assert sha(source/member['name'])==member['sha256']
 print('Local ACS archives and compact original OULAD source bytes verified')
if __name__=='__main__':main()

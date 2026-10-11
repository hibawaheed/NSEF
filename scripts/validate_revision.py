#!/usr/bin/env python3
import gzip,hashlib,json,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=ROOT/'figures/revision2';index=json.loads((out/'index.json').read_text())
for folder in ['revision2','revision2-public']:
 p=ROOT/'results/raw'/folder;m=json.loads((p/'manifest.json').read_text());assert m['failures']==0
 assert m['runs']==len(m['run_hashes'])
 for name,expected in m['run_hashes'].items():assert sha(p/name)==expected
 assert sha(p/'source_snapshot.zip')==m['snapshot_sha256']
 print(folder,m['runs'],'raw runs, hashes and source snapshot verified')
sm=json.loads((ROOT/'results/revision2/manifest.json').read_text())
for name,expected in sm['files'].items():assert sha(ROOT/'results/revision2'/name)==expected
for item in index['figures']:
 name=item['name'];m=json.loads((out/f'{name}.manifest.json').read_text())
 assert sha(ROOT/'results/revision2/streams.csv')==m['source_summary_sha256']
 assert sha(ROOT/'results/revision2/outcomes.csv')==m['outcome_summary_sha256']
 assert sha(ROOT/'configs/revision2.json')==m['config_sha256']
 assert sha(out/f'{name}.csv')==m['csv_sha256']
 for ext,expected in m['formats'].items():assert sha(out/f'{name}.{ext}')==expected
 im=Image.open(out/f'{name}.png');assert min(im.info['dpi'])>=299
 assert im.size==(3990,2430)
assert sha(out/'SubPSI_revision2.pdf')==index['chart_pack_sha256']
info=subprocess.check_output(['pdfinfo',str(out/'SubPSI_revision2.pdf')],text=True)
assert f'Pages:           {len(index["figures"])}' in info
print(len(index['figures']),'figure tables, manifests, images and combined PDF pages verified')
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ['psi_seconds','ks_seconds','repeats']}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
count=0
for p in (ROOT/'results/raw/revision2-smoke').glob('*.json.gz'):
 with gzip.open(p,'rt') as f:a=json.load(f)
 with gzip.open(ROOT/'results/raw/revision2'/p.name,'rt') as f:b=json.load(f)
 assert clean(a)==clean(b),p.name
 count+=1
print(count,'preselected smoke streams reproduced all numerical results in main evaluation (timings and repeat-count metadata excluded)')

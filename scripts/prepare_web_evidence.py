#!/usr/bin/env python3
"""Copy only the deliberately public research artifacts into the static site."""
import gzip,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
a=ROOT/'figures/revision2';b=ROOT/'web/evidence';b.mkdir(parents=True,exist_ok=True)
index=json.loads((a/'index.json').read_text())
for item in index['figures']:
 for ext in ['svg','pdf','csv','manifest.json']:shutil.copy2(a/f'{item["name"]}.{ext}',b)
for filename in ['index.json','SubPSI_revision2.pdf']:shutil.copy2(a/filename,b)
for name in ['streams.csv','outcomes.csv','timing.csv']:
 with gzip.GzipFile(filename=str(b/(name+'.gz')),mode='wb',mtime=0) as f:f.write((ROOT/'results/revision2'/name).read_bytes())
parts=['docs/REVISION2_FINDINGS.md','docs/REVISION2_METHODS.md','docs/REVISION2_PRIOR_WORK.md','records/CHANGELOG.md','records/AI_USE.md']
(b/'study-record.txt').write_text('\n\n'.join((ROOT/p).read_text() for p in parts))
(b/'revision2-config.json').write_bytes((ROOT/'configs/revision2.json').read_bytes())
print(f'Prepared {len(list(b.iterdir()))} public evidence files; no raw visitor or Adult records copied.')

#!/usr/bin/env python3
"""Download original-provider public dataset with attribution and content hashes."""
from pathlib import Path
import urllib.request,zipfile,io,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]
URL='https://archive.ics.uci.edu/static/public/2/adult.zip'
out=ROOT/'data/raw/adult'
if out.exists():
 record=json.loads((ROOT/'records/adult_dataset.json').read_text())
 for name,expected in record['files'].items():
  if hashlib.sha256((out/name).read_bytes()).hexdigest()!=expected: raise ValueError(f'Existing file hash mismatch: {name}')
 print('Existing Adult download verified; no network request needed.')
 raise SystemExit(0)
out.mkdir(parents=True,exist_ok=False)
with urllib.request.urlopen(URL,timeout=90) as response: data=response.read()
(out/'adult.zip').write_bytes(data)
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    for name in ['adult.data','adult.test','adult.names']:
        (out/name).write_bytes(archive.read(name))
record={'source':URL,'landing_page':'https://archive.ics.uci.edu/dataset/2/adult',
 'citation':'Becker, B. & Kohavi, R. (1996). Adult [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5XW20.',
 'license':'CC BY 4.0','license_url':'https://creativecommons.org/licenses/by/4.0/',
 'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(ROOT/'records/adult_dataset.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))

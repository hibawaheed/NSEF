"""Cache primary documentation; failures remain in the manifest."""
from pathlib import Path
import urllib.request,hashlib,json,datetime,subprocess
ROOT=Path(__file__).resolve().parents[2]
out=ROOT/'data/raw/revision3/documentation';out.mkdir(parents=True,exist_ok=True)
sources={**{f'acs_{y}_dictionary.txt':f'https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/'+(f'PUMSDataDict{str(y)[2:]}.txt' if y<2017 else f'PUMS_Data_Dictionary_{y}.txt') for y in range(2015,2020)},
'acs2019_accuracy.pdf':'https://www2.census.gov/programs-surveys/acs/tech_docs/pums/accuracy/2019AccuracyPUMS.pdf',
'folktables_acs.py':'https://raw.githubusercontent.com/socialfoundations/folktables/main/folktables/acs.py',
'folktables.pdf':'https://arxiv.org/pdf/2108.04884',
'msd.pdf':'https://arxiv.org/pdf/2502.02221v2',
'monitoring.pdf':'https://arxiv.org/pdf/2506.05701v3',
'fairfeddrift.pdf':'https://arxiv.org/pdf/2402.07586v4',
'adwin.pdf':'https://www.cs.upc.edu/~gavalda/papers/adwin06.pdf',
'kswin.pdf':'https://arxiv.org/pdf/2007.05432',
'folktables_datasheet.md':'https://raw.githubusercontent.com/socialfoundations/folktables/main/datasheet.md',
'kswin.html':'https://riverml.xyz/latest/api/drift/KSWIN/'}
records=[]
for name,url in sources.items():
 rec={'name':name,'url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  p=out/name
  if not p.exists():
   with urllib.request.urlopen(url,timeout=40) as r:p.write_bytes(r.read())
  rec.update(status='downloaded',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
  if p.suffix=='.pdf':subprocess.run(['pdftotext','-layout',str(p),str(p)+'.txt'],check=True,capture_output=True)
 except Exception as e:rec.update(status='failed',error=str(e))
 records.append(rec);print(name,rec['status'],flush=True)
 (out/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')

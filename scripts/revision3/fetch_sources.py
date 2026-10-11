"""Download immutable public sources for schema/support inspection only."""
import argparse, datetime, hashlib, json, time, urllib.request, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCES={**{f'acs/{y}/csv_pma.zip':f'https://www2.census.gov/programs-surveys/acs/data/pums/{y}/1-Year/csv_pma.zip' for y in range(2015,2020)},
 'oulad/oulad.zip':'https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--only',choices=['acs','oulad','all'],default='all');a=p.parse_args()
 base=ROOT/'data/raw/revision3';base.mkdir(parents=True,exist_ok=True)
 for name,url in SOURCES.items():
  if a.only!='all' and not name.startswith(a.only+'/'):continue
  dest=base/name;receipt=dest.with_suffix('.receipt.json');dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():
   if not receipt.exists() or hashlib.sha256(dest.read_bytes()).hexdigest()!=json.loads(receipt.read_text())['sha256']:raise ValueError(f'Unverified existing source {name}')
   print('Verified cached',name,flush=True);continue
  start=time.perf_counter();tmp=dest.with_suffix('.part')
  req=urllib.request.Request(url,headers={'User-Agent':'SubPSI academic source verification'})
  with urllib.request.urlopen(req,timeout=60) as response, tmp.open('wb') as f:
   headers={k:response.headers.get(k) for k in ['Last-Modified','ETag','Content-Type']}
   while chunk:=response.read(1024*1024):f.write(chunk)
  with zipfile.ZipFile(tmp) as z:
   bad=z.testzip()
   if bad:raise ValueError(f'Corrupt ZIP member {bad}')
   members=[{'name':m.filename,'bytes':m.file_size,'crc':m.CRC} for m in z.infolist()]
  tmp.rename(dest)
  out={'url':url,'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'headers':headers,'members':members,'seconds':time.perf_counter()-start,'purpose':'schema/support inspection, not main evaluation'}
  receipt.write_text(json.dumps(out,indent=2)+'\n');print(name,out['bytes'],out['sha256'],round(out['seconds'],2),'seconds',flush=True)
if __name__=='__main__':main()

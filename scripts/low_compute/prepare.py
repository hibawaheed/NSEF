"""Prepare exact, hash-checked existing replays; never calibrate or alter records."""
from pathlib import Path
import sys,json,gzip,hashlib,time,platform,subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256
from subpsi.revision4_study import historical_pool,evaluation_stream,seed_integer

OUT=ROOT/'configs/low_compute/benchmark.json'; PRIVATE=ROOT/'data/raw/low_compute/2026-10-18'
def main():
 if OUT.exists():raise FileExistsError('Selection already frozen')
 start=time.perf_counter(); cpu=time.process_time()
 c=json.loads((ROOT/'configs/revision4/approved.json').read_text())
 inventory=json.loads((ROOT/'results/raw/revision4/main-approved/evaluation_inventory.json').read_text())
 selection=[next(x for x in inventory if x['condition']==condition and x['repeat']==rep) for rep in range(5) for condition in c['evaluation']['conditions']]
 # Selection saved before profiling or timing. Hash binding is added before any benchmark.
 (ROOT/'records/low_compute/2026-10-18/selected_runs.json').write_text(json.dumps(selection,indent=2)+'\n')
 pool,bins,groups,sources=historical_pool(ROOT,'evaluation')
 for name,h in json.loads((ROOT/'results/raw/revision4/main-approved/evaluation_sources.json').read_text()).items():
  if sha256(ROOT/name)!=h:raise ValueError('Source changed: '+name)
 audit=json.loads((ROOT/'records/revision4/main/evaluation_verification.json').read_text())
 roles={s:set(pd.read_csv(ROOT/f'data/raw/revision4/main-approved/{s}_pool.csv').household_id) for s in ['selection','validation','evaluation']}
 for a,b in [('selection','validation'),('selection','evaluation'),('validation','evaluation')]:
  if roles[a]&roles[b]:raise ValueError('Source-role overlap')
 features=list(bins)+list(c['evaluation']['target']); inputs=[]
 for cell in selection:
  ref,windows=evaluation_stream(pool,c,cell['repeat'],cell['condition'])
  lineage=ROOT/f"data/raw/revision4/main-approved/evaluation/stream-{cell['cell']:03}.csv.gz"
  if sha256(lineage)!=audit['private_lineage_hashes'][str(lineage.relative_to(ROOT))]:raise ValueError('Lineage hash changed')
  actual=pd.concat([ref[['source_id']],*[f[['source_id']] for _,f in windows]]).to_csv(index=True,index_label='draw_id').encode()
  with gzip.open(lineage,'rb') as h:
   if actual!=h.read():raise ValueError('Replay does not reproduce saved records')
  directory=PRIVATE/f"stream-{cell['cell']:03}";directory.mkdir(parents=True,exist_ok=False);files=[]
  for look,frame in [(0,ref),*windows]:
   path=directory/f'batch-{look:02}.npz'
   np.savez(path,ids=np.asarray(frame.index,dtype=str),values=frame[features].to_numpy(dtype=float))
   files.append(dict(look=look,path=str(path.relative_to(ROOT)),sha256=sha256(path),n=len(frame)))
  old={policy:dict(path=f"results/raw/revision4/main-approved/evaluation/stream-{cell['cell']:03}-{policy}.json.gz") for policy in ['fixed_100','fixed_400']}
  for v in old.values():v['sha256']=sha256(ROOT/v['path'])
  inputs.append(dict(**cell,seed=seed_integer(c,'evaluation',0,cell['repeat']),files=files,original=old,lineage_sha256=sha256(lineage)))
 manifest=dict(created_local=datetime.now(ZoneInfo('Asia/Karachi')).isoformat(),base_commit='39014345b53f4ff7fe8481e6aa9a996d00c10b5b',
  registered_title='SubPSI: Detecting Hidden Bias Drift in Machine Learning Through Subgroup-Decomposed Population Stability Analysis.',
  source_config='configs/revision4/approved.json',source_config_sha256=sha256(ROOT/'configs/revision4/approved.json'),source_hashes=sources,
  features=features,bins={f:b.metadata() for f,b in bins.items()},groups=[dict(name=g.name,selectors=g.selectors,level=g.level) for g in groups],
  horizon=20,alpha=.05,channels=1,draws=23999,min_reference=50,pseudocount=.5,inputs=inputs,
  primary=dict(policy='fixed_100',target=100,cells=[x['cell'] for x in selection],prefix=20),
  secondary=dict(policy='fixed_400',target=400,cells=[x['cell'] for x in selection if x['repeat']==0],prefix=20),
  prefixes=[dict(policy='fixed_100',target=100,cells=[140],prefix=n) for n in [5,10]],
  warmups=1,timed_repeats=5,order='A,B,C,D then D,C,B,A alternating by repeat; same input order',
  implementations={'A':'faithful PSI-only extraction from frozen R4 runner','B':'count-reuse PSI iterator','C':'cached-reference KS-only iterator with existing ks_missing/ks_score','D':'count-reuse aggregate PSI; 2 tests, lower scope'},
  timing='Fresh process per implementation/repeat/workload. End-to-end includes imports, loading, exact ID audit, monitoring and identical JSONL result writes. Monitoring excludes loading/validation/output; setup separate. No parallel timing workers.',
  threads=1,uncertainty='Median and min/max of 5 technical repeats on one machine; no statistical-trial count inflation.',
  prefix_note='First 5/10 batches of the existing strongest-change first stream; original horizon=20 and cutoff retained. Cost scaling only; no new detection trials.',
  tolerance='PSI absolute 1e-14, rtol=0; require exact p/adjusted p, RNG mapping, draws, stopping, histograms, schedule, hits, first alerts. Report actual maximum PSI difference.',
  prepare_wall_seconds=time.perf_counter()-start,prepare_cpu_seconds=time.process_time()-cpu,
  source_role_note='Year-namespaced household keys disjoint; not a guarantee of distinct people across years.')
 OUT.write_text(json.dumps(manifest,indent=2)+'\n');print('Prepared',len(inputs),'saved real-record replays; source roles/lineage verified.')
if __name__=='__main__':main()

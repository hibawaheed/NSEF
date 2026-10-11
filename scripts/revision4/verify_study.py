"""Independent saved-result consistency checks and fixed key-run reproductions."""
from pathlib import Path
import gzip,hashlib,json,sys,time
import numpy as np
import pandas as pd
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,write_json
from subpsi.correction import read_table
from subpsi.matched import compare_block
from subpsi.revision4_study import historical_pool,rng,seed_integer,weights

def main():
 raw=ROOT/'results/raw/revision4/main-approved';private=ROOT/'data/raw/revision4/main-approved'
 cfg=json.loads((ROOT/'configs/revision4/approved.json').read_text()); start=time.perf_counter()
 checks={}
 for name,key in [('records/correction/FREEZE.json','evidence_sha256'),('records/revision4/PREPARATION_MANIFEST.json','files')]:
  m=json.loads((ROOT/name).read_text())
  for path,expected in m[key].items():
   if sha256(ROOT/path)!=expected:raise ValueError('Protected file changed: '+path)
  checks[name]=len(m[key])
 old=json.loads((ROOT/'results/summary/revision4/preparation-02/preserved_inventory.json').read_text())
 for path,expected in old.items():
  if sha256(ROOT/path)!=expected:raise ValueError('Original version changed: '+path)
 checks['unchanged_starting_files']=len(old)
 pool,bins,groups,_=historical_pool(ROOT,'selection'); groupmap={g.name:g for g in groups}
 inventory=json.loads((raw/'selection_inventory.json').read_text())
 selected=[r for r in inventory if (r['group'],r['reference_n'],r['incoming_n'],r['scenario']) in [
  ('Everyone',100,50,'unchanged'),('Everyone',800,800,'age_up4'),('SEX=2 & RAC1P=2',400,200,'age_up2')]]
 if len(selected)!=3:raise ValueError('Missing predetermined key cells')
 replay=[]
 for cell in selected:
  path=raw/'selection'/f"cell-{cell['cell']:04}.json.gz"
  with gzip.open(path,'rt') as f:result=json.load(f)
  lineage=np.load(private/'selection'/f"cell-{cell['cell']:04}.npz")
  subset=pool.loc[groupmap[cell['group']].mask(pool)];w=weights(subset,cfg['calibration']['whole_record_multipliers'][cell['scenario']]);w/=w.sum()
  cutoff=.05/(20*60)
  fields=['psi','p','draws','censored','ks_d','ks_p','ks_status','ks_warning','missing_reference','missing_current']
  for repeat in range(100):
   a=rng(cfg,'selection',cell['cell'],repeat,1).choice(len(subset),size=cell['reference_n'],replace=True)
   b=rng(cfg,'selection',cell['cell'],repeat,2).choice(len(subset),size=cell['incoming_n'],replace=True,p=w)
   np.testing.assert_array_equal(a,lineage['reference'][repeat]);np.testing.assert_array_equal(b,lineage['current'][repeat])
   for fi,(feature,binning) in enumerate(bins.items()):
    actual=compare_block(subset.iloc[a][feature],subset.iloc[b][feature],binning,inferential=True,
      seed=[seed_integer(cfg,'selection',cell['cell'],repeat),fi],draws=23999,cutoff=cutoff)
    expected=next(r for r in result['rows'] if r['repeat']==repeat and r['feature']==feature)
    for field in fields:
     if actual[field]!=expected[field]:raise ValueError(f'Replay changed {cell["cell"]} {repeat} {feature} {field}')
  replay.append(dict(cell=cell,raw_sha256=sha256(path),reproduced_repetitions=100,reproduced_feature_comparisons=200))
 checks.update(selection_replays=replay,wall_seconds=time.perf_counter()-start)
 target=ROOT/'records/revision4/main/key_run_verification.json'
 if target.exists():target=ROOT/'data/raw/revision4/verification-replays'/f'key-run-{time.time_ns()}.json'
 target.parent.mkdir(parents=True,exist_ok=True)
 write_json(target,checks)
 print('Verification report:',target)
 print(json.dumps(checks,indent=2))

if __name__=='__main__':main()

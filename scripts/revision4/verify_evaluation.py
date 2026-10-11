"""Full raw/table/tie checks and two prespecified complete-stream reproductions."""
from pathlib import Path
import gzip,json,sys,time
import numpy as np
import pandas as pd
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,write_json
from subpsi.correction import read_table
from subpsi.revision4 import digest,run_frozen_targets
from subpsi.revision4_study import historical_pool,plans,evaluation_stream,seed_integer,stream_summary

def read(path):
 with gzip.open(path,'rt') as handle:return json.load(handle)

def scientific(result):
 return {key:[{k:v for k,v in row.items() if 'seconds' not in k} for row in result[key]] for key in ['tests','decisions','schedule']}

def main():
 raw=ROOT/'results/raw/revision4/main-approved'; private=ROOT/'data/raw/revision4/main-approved';summary=ROOT/'results/summary/revision4/main-approved'
 if not (raw/'evaluation_complete.json').exists():raise ValueError('Full evaluation required')
 started=time.perf_counter();cfg=json.loads((ROOT/'configs/revision4/approved.json').read_text());frozen=json.loads((raw/'frozen_targets.json').read_text())
 identity=json.loads((raw/'identity.json').read_text()); inventory=json.loads((raw/'evaluation_inventory.json').read_text())
 pool,bins,groups,sources=historical_pool(ROOT,'evaluation'); policies=plans(cfg,groups,frozen['selection'])
 target=next(g.name for g in groups if dict(g.selectors)==cfg['evaluation']['target'])
 saved_summary=read_table(summary/'streams.csv'); checked=0;ties=0;warning_count=0;private_hashes={};source_inputs={}
 for stage in ['selection','validation','evaluation']:
  for name,h in json.loads((raw/f'{stage}_sources.json').read_text()).items():
   if sha256(ROOT/name)!=h:raise ValueError('Original source changed: '+name)
   source_inputs[name]=h
 # Household keys are year-namespaced; this does not prove distinct people across years.
 households={s:set(pd.read_csv(private/f'{s}_pool.csv').household_id) for s in ['selection','validation','evaluation']}
 for a,b in [('selection','validation'),('selection','evaluation'),('validation','evaluation')]:
  if households[a]&households[b]:raise ValueError('Source-role overlap')
 for stage in ['selection','validation']:
  for path in (raw/stage).glob('*.json.gz'):
   result=read(path)
   if result['identity_sha256']!=digest(identity):raise ValueError('Cell identity mismatch')
   if result['status']=='assessed':
    lineage=private/stage/path.name.replace('.json.gz','.npz')
    if sha256(lineage)!=result['lineage_sha256']:raise ValueError('Calibration lineage mismatch')
    private_hashes[str(lineage.relative_to(ROOT))]=sha256(lineage)
 for cell in inventory:
  linepath=private/'evaluation'/f"stream-{cell['cell']:03}.csv.gz";line=read_table(linepath)
  if not line.draw_id.is_unique or not line.source_id.isin(pool.index).all():raise ValueError('Invalid stream source/draw identity')
  private_hashes[str(linepath.relative_to(ROOT))]=sha256(linepath)
  outputs={}
  for policy in policies:
   path=raw/'evaluation'/f"stream-{cell['cell']:03}-{policy}.json.gz";result=read(path);outputs[policy]=result
   if result['identity_sha256']!=digest(identity) or result['map_sha256']!=frozen['map_sha256'] or result['cell']!=cell or result['lineage_sha256']!=sha256(linepath):raise ValueError('Stream identity mismatch')
   if len(result['tests'])!=20*30*2 or len(result['schedule'])!=20*30 or len(result['decisions'])!=20*3*2:raise ValueError('Dropped declared test/view/look')
   for row in result['tests']:
    if not row['eligible'] and (row['p']!=1 or row['ks_p']!=1):raise ValueError('Unsupported test missing p=1 placeholder')
    warning_count+=int(row['ks_status']=='conservative_warning')
   expected=pd.DataFrame(stream_summary(result,target,6,20))
   actual=saved_summary.loc[saved_summary.cell.eq(cell['cell'])&saved_summary.policy.eq(policy),list(expected)].reset_index(drop=True)
   for column in expected:
    if column in ['scope','method']:
     if actual[column].tolist()!=expected[column].tolist():raise ValueError('Summary key mismatch')
    else:
     np.testing.assert_allclose(pd.to_numeric(actual[column]).to_numpy(dtype=float),pd.to_numeric(expected[column]).to_numpy(dtype=float),rtol=0,atol=1e-12,equal_nan=True)
   for decision in result['decisions']:
    if decision['cutoff']!=.05/20:raise ValueError('Error budget changed')
    if decision['scope']=='intersection' and decision['family_size']!=60:raise ValueError('Family shrank')
   checked+=1
  if scientific(outputs['global_calibrated'])!=scientific(outputs['group_calibrated']):raise ValueError('Identical frozen maps fail exact scientific parity')
  ties+=1
  if cell['condition']!='unchanged':
   baseline=next(r for r in inventory if r['condition']=='unchanged' and r['repeat']==cell['repeat'])
   base=read_table(private/'evaluation'/f"stream-{baseline['cell']:03}.csv.gz")
   if not line.draw_id.equals(base.draw_id):raise ValueError('Unpaired draw identities')
   memberships=pool.loc[line.source_id,['SEX','RAC1P']].to_numpy();original=pool.loc[base.source_id,['SEX','RAC1P']].to_numpy()
   np.testing.assert_array_equal(memberships,original)
   before=line.draw_id.str.startswith('reference:') | line.draw_id.str.match(r'delivery:[1-5]:')
   nontarget=~((original[:,0]==2)&(original[:,1]==2))
   if not line.loc[before|nontarget,'source_id'].equals(base.loc[before|nontarget,'source_id']):raise ValueError('Unchanged draws modified')
  if (cell['cell']+1)%40==0:print(f'Checked {cell["cell"]+1}/220 stream sets',flush=True)
 if checked!=1100 or ties!=220:raise ValueError('Incomplete study')
 replay=[]
 # Fixed before inspection: first null ordinary policy and first strongest design alternative fixed-400 policy.
 for condition,policy in [('unchanged','ordinary_50'),('age_up4','fixed_400')]:
  cell=next(r for r in inventory if r['condition']==condition and r['repeat']==0)
  reference,windows=evaluation_stream(pool,cfg,0,condition);features=list(bins)+list(cfg['evaluation']['target'])
  actual=run_frozen_targets(reference[features],[(t,d[features]) for t,d in windows],bins=bins,groups=groups,
   plan=policies[policy],alpha=.05,draws=23999,seed=seed_integer(cfg,'evaluation',0,0),inferential=True)
  path=raw/'evaluation'/f"stream-{cell['cell']:03}-{policy}.json.gz";expected=read(path)
  # JSON normalizes tuple hits to lists.
  if json.loads(json.dumps(scientific(actual)))!=scientific(expected):raise ValueError('Key stream replay differs')
  replay.append(dict(condition=condition,policy=policy,repeat=0,feature_tests=1200,raw_sha256=sha256(path)))
 checks=dict(verified_policy_engines=checked,verified_declared_feature_tests=checked*1200,
  exact_global_group_tied_streams=ties,verified_source_inputs=source_inputs,private_lineage_hashes=private_hashes,
  key_stream_replays=replay,ks_warning_count=warning_count,wall_seconds=time.perf_counter()-started,
  limitation='Private year/household key disjointness is not a guarantee of distinct respondents across survey years.')
 target=ROOT/'records/revision4/main/evaluation_verification.json'
 if target.exists():target=ROOT/'data/raw/revision4/verification-replays'/f'evaluation-{time.time_ns()}.json'
 target.parent.mkdir(parents=True,exist_ok=True)
 write_json(target,checks)
 print('Verification report:',target)
 print(json.dumps({k:v for k,v in checks.items() if k not in ['private_lineage_hashes','verified_source_inputs']},indent=2))

if __name__=='__main__':main()

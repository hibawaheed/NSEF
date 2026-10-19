"""Fixed first replay from each condition; profile before optimization."""
from common import *
import cProfile,pstats,csv,gzip
from subpsi.revision4 import run_frozen_targets
from subpsi.low_compute_baseline import run_baseline
out=ROOT/'results/raw/low_compute/2026-10-18/profile';out.mkdir(exist_ok=False)
c=configuration();summary=[];functions=[]
for method,runner in [('joint_original',run_frozen_targets),('baseline_psi',run_baseline)]:
 for cell in [x for x in c['inputs'] if x['repeat']==0]:
  profile=cProfile.Profile();profile.enable();t=time.perf_counter();cpu=time.process_time()
  load=time.perf_counter();it=replays(c,cell);ref=next(it);win=list(it);loading=time.perf_counter()-load
  result=runner(ref,win,seed=cell['seed'],**definitions(c,100))
  tick=time.perf_counter();encoded=json.dumps(result).encode();output=out/f"{method}-{cell['cell']}.json.gz"
  with gzip.open(output,'wb') as h:h.write(encoded)
  writing=time.perf_counter()-tick
  profile.disable();profile.dump_stats(str(out/f"{method}-{cell['cell']}.prof"))
  summary.append(dict(method=method,cell=cell['cell'],condition=cell['condition'],wall_seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu,loading_wall=loading,output_wall=writing,engine_wall=result['metadata']['engine_seconds']))
  for (file,line,function),(cc,nc,tt,ct,callers) in pstats.Stats(profile).stats.items():
   functions.append(dict(method=method,cell=cell['cell'],file=file,line=line,function=function,primitive_calls=cc,calls=nc,self_seconds=tt,cumulative_seconds=ct))
  print(method,cell['condition'],summary[-1]['wall_seconds'],flush=True)
for name,rows in [('runs',summary),('functions',functions)]:
 with (out/f'{name}.csv').open('w') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(pd.DataFrame(functions).groupby(['method','function']).cumulative_seconds.sum().groupby(level=0).nlargest(12).to_string())

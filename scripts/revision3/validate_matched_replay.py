"""Three preselected v2 streams, regenerated without altering their generators.

Software validation only; not a new detection-rate study. Refuses overwrite.
"""
import gzip,hashlib,json,sys,time,tracemalloc,resource,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.revision import generate,count_test,ks_missing
from subpsi.core import NumericBins,adjust_pvalues
from subpsi.matched import declared_groups,run_matched
from subpsi.provenance import sha256,save_snapshot,environment
OUT=ROOT/'results/raw/revision3/matched-software-validation'
NAMES=['null_n250_0000.json.gz','grid_n250_s0.05_m1.4_0000.json.gz','correlation_0000.json.gz']

def main():
 OUT.mkdir(parents=True,exist_ok=False)
 c=json.loads((ROOT/'configs/revision2.json').read_text());checks=[];rawhash={};total=time.perf_counter();profile=[]
 for name in NAMES:
  source=ROOT/'results/raw/revision2'/name
  with gzip.open(source,'rt') as f:old=json.load(f)
  seed,repeat=old['seed'];case=old['case'];streams=np.random.SeedSequence([seed,repeat]).spawn(c['windows']+3)
  d=[generate(c['n_'+r],np.random.default_rng(streams[i]),case) for i,r in enumerate(['reference','design','audit'])]
  ws=[]
  for w in range(1,c['windows']+1):
   progress=0 if w<c['onset'] or case['kind']=='null' else min(1,(w-c['onset']+1)/6) if case['kind']=='gradual' else 1
   ws.append(generate(case['n'],np.random.default_rng(streams[w+2]),case,progress))
  def frame(data,prefix):return pd.DataFrame({k:v for k,v in data.items() if k not in {'y','pred'}},index=[f'{prefix}:{i}' for i in range(len(data['x']))])
  ref,design=frame(d[0],'reference'),frame(d[1],'design');frames=[(i+1,frame(v,f'look{i+1}')) for i,v in enumerate(ws)]
  bins={f:NumericBins.fit(design[f],c['bins']) for f in ['x','x2'] if f in design}
  groups=declared_groups({'A':[0,1],'B':[0,1]})
  s=int(np.random.SeedSequence([seed,repeat,981]).generate_state(1)[0])
  tracemalloc.start();start=time.perf_counter()
  new=run_matched(ref,frames,bins=bins,groups=groups,min_n=c['pool_n'],alpha=c['alpha'],draws=c['permutations'],seed=s,inferential=True)
  seconds=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
  oldrows={(r['window'],r['group'],r['feature']):r for r in old['tests'] if r['policy']=='accumulate'}
  for r in new['tests']:
   gi=next(i for i,g in enumerate(groups) if g.name==r['group']);o=oldrows[r['look'],gi,r['feature']]
   assert (r['n_reference'],r['n_current'],r['eligible'],r['opened_look'])==(o['n_reference'],o['n_current'],o['eligible'],o['start_window'])
   if r['eligible']:assert np.isclose(r['psi'],o['psi'],rtol=0,atol=1e-12)
  for r in new['decisions']:
   if r['scope']=='intersection' and r['method']=='PSI':
    o=next(v for v in old['decisions'] if v['method']=='Accumulated PSI' and v['window']==r['look'])
    assert r['alert']==o['alert']
    assert sorted({next(i for i,g in enumerate(groups) if g.name==n) for n,_ in r['hits']})==o['hits']
  # Cost profile: exact same predetermined aggregate block; 3 repeats, alternate
  # test order. Timings outside tracemalloc; peaks in separate instrumented calls.
  x=ref.x.to_numpy();y=frames[-1][1].x.to_numpy();a,b=bins['x'].counts(x),bins['x'].counts(y)
  funcs={'PSI':lambda:count_test(a,b,seed=71,draws=c['permutations'],stop_above=c['alpha']/c['windows']),
         'KS':lambda:ks_missing(x,y)}
  for repeat_cost in range(3):
   for method in (['PSI','KS'] if repeat_cost%2==0 else ['KS','PSI']):
    start=time.perf_counter();funcs[method]();elapsed=time.perf_counter()-start
    tracemalloc.start();funcs[method]();_,testpeak=tracemalloc.get_traced_memory();tracemalloc.stop()
    profile.append(dict(source=name,method=method,repeat=repeat_cost,reference_n=len(x),current_n=len(y),seconds=elapsed,tracemalloc_peak_bytes=testpeak,input_payload_bytes=int(a.nbytes+b.nbytes if method=='PSI' else x.nbytes+y.nbytes),scope='test only; excludes input preparation, shared scheduler, interpreter and native untracked allocations'))
  checks.append(dict(source=name,source_sha256=sha256(source),checks='all accumulation counts, support, block starts, PSI scores and PSI alert group sets match v2',matched_tests=len(new['tests']),runtime_seconds_with_tracemalloc=seconds,tracemalloc_engine_peak_bytes=peak))
  target=OUT/name
  with gzip.GzipFile(filename=str(target),mode='wb',mtime=0) as z:z.write(json.dumps(new,allow_nan=False).encode())
  rawhash[name]=sha256(target)
  print(name,'matched',len(new['tests']),'group-feature opportunities;',round(seconds,3),'s',flush=True)
 pd.DataFrame(profile).to_csv(OUT/'test_cost_validation.csv',index=False)
 m={'purpose':'software validation only, no main evaluation or new detection-rate estimate','preselected_sources':NAMES,'checks':checks,'files':{**rawhash,'test_cost_validation.csv':sha256(OUT/'test_cost_validation.csv')},'source_snapshot_sha256':save_snapshot(ROOT,OUT),'git_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'environment':environment(),'wall_seconds':time.perf_counter()-total,'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'memory_caveat':'Linux peak RSS covers complete validation process; tracemalloc may miss native allocations. Logical PSI histogram versus KS raw-array bytes are not total deployment memory.'}
 (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 print('Software checks passed; no main natural-data evaluation run.')
if __name__=='__main__':main()

"""Exact comparison to saved Version 4; new timings never add detection trials."""
from common import *
import gzip,hashlib,csv
from contextlib import contextmanager
from subpsi.core import psi_counts
from subpsi.revision4 import run_frozen_targets,FrozenTargetScheduler
from subpsi.low_compute import run_lightweight
import subpsi.low_compute as light
import subpsi.low_compute_baseline as baseline
from subpsi.revision import count_test
sys.path.insert(0,str(ROOT/'tests'))
from test_low_compute import project,SCHEDULE

@contextmanager
def audit_rng(module,records):
    original=module.count_test
    def traced(a,b,*,seed,draws,stop_above):
        factory=np.random.default_rng;real=factory(seed);total=a+b;score=float(psi_counts(a,b));h=hashlib.sha256();extreme=0;done=0
        class Tap:
            def multivariate_hypergeometric(self,*args,**kwargs):
                nonlocal extreme,done
                c=real.multivariate_hypergeometric(*args,**kwargs);h.update(c.tobytes())
                extreme+=int(np.sum(psi_counts(c,total-c)>=score-1e-12));done+=len(c)
                return c
        np.random.default_rng=lambda s:Tap()
        try:result=count_test(a,b,seed=seed,draws=draws,stop_above=stop_above)
        finally:np.random.default_rng=factory
        records.append(dict(seed=seed,a=a.tolist(),b=b.tolist(),extreme=extreme,draws=done,rng_sha256=h.hexdigest(),**{k:v for k,v in result.items() if k!='draws'}))
        return result
    module.count_test=traced
    try:yield
    finally:module.count_test=original

def normalized(v):return json.loads(json.dumps(v))
def old_histograms(ref,windows,kw):
    groups,bins,plan=kw['groups'],kw['bins'],kw['plan'];ids={g.name:tuple(ref.index[g.mask(ref)]) for g in groups}
    s=FrozenTargetScheduler({g:len(a) for g,a in ids.items()},plan);current=pd.concat([f for _,f in windows]);out={}
    for look,(t,f) in enumerate(windows,1):
        for gi,block in enumerate(s.advance(t,{g.name:tuple(f.index[g.mask(f)]) for g in groups})):
            for feature,binning in bins.items():out[look,gi,feature]=(binning.counts(ref.loc[list(ids[block.group]),feature]),binning.counts(current.loc[list(block.ids),feature]))
    return out

def main():
    c=configuration();out=ROOT/'results/raw/low_compute/2026-10-18/equivalence';out.mkdir(exist_ok=False)
    rows=[];start=time.perf_counter()
    for cell in c['inputs']:
        it=replays(c,cell);ref=next(it);windows=list(it)
        for target in ([100,400] if cell['repeat']==0 else [100]):
            policy=f'fixed_{target}';kw=definitions(c,target);kw['seed']=cell['seed'];hist=old_histograms(ref,windows,kw);checks=[]
            def observe(look,gi,f,a,b):
                x,y=hist[look,gi,f];np.testing.assert_array_equal(x,a);np.testing.assert_array_equal(y,b);checks.append((look,gi,f))
            a=[];b=[]
            with audit_rng(baseline,a):unoptimized=baseline.run_baseline(ref,windows,**kw)
            with audit_rng(light,b):optimized=run_lightweight(ref,iter(windows),histogram_observer=observe,**kw)
            if a!=b:raise AssertionError('Permutation count/seed/draw/extreme/p-value mismatch')
            oldpath=ROOT/cell['original'][policy]['path']
            if sha256(oldpath)!=cell['original'][policy]['sha256']:raise ValueError('Old evidence changed')
            with gzip.open(oldpath,'rt') as f:old=json.load(f)
            for name,result in [('baseline',unoptimized),('optimized',optimized)]:
                if normalized(project(old,'PSI'))!=normalized(project(result,'PSI')):raise AssertionError(name+' PSI mismatch')
            ks=run_lightweight(ref,iter(windows),method='KS',**kw)
            if normalized(project(old,'KS'))!=normalized(project(ks,'KS')):raise AssertionError('KS mismatch')
            # Complete schedule/adjusted values/hits equality implies first alerts equal; record them explicitly.
            first={m:min([d['look'] for d in old['decisions'] if d['method']==m and d['scope']=='intersection' and d['alert']],default=None) for m in ['PSI','KS']}
            payload=dict(cell=cell,policy=policy,permutation_traces=a,first_alerts=first,verified_histograms=len(checks),max_psi_difference=0.,all_pvalues_exact=True,all_decisions_exact=True)
            path=out/f"stream-{cell['cell']:03}-{policy}.json.gz"
            with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as f:f.write(json.dumps(payload).encode())
            rows.append(dict(cell=cell['cell'],condition=cell['condition'],repeat=cell['repeat'],policy=policy,feature_rows=len(old['tests']),histograms=len(checks),assessed_tests=len(a),permutation_draws=sum(t['draws'] for t in a),max_psi_difference=0.,pvalues_exact=True,adjusted_exact=True,schedules_exact=True,first_psi_alert=first['PSI'],first_ks_alert=first['KS'],source_csv_or_raw=cell['original'][policy]['path'],trace_sha256=sha256(path)))
        print('Verified',cell['cell'],cell['condition'],flush=True)
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    (out/'completion.json').write_text(json.dumps(dict(verified_runs=len(rows),wall_seconds=time.perf_counter()-start,config_sha256=sha256(CONFIG),scope='20 fixed-100 plus 4 fixed-400 saved runs; not all 220 streams',psi_difference=0,exact=True),indent=2)+'\n')
if __name__=='__main__':main()

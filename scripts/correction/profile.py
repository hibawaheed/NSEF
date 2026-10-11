"""Small alternating-order cost check; no new detection-rate experiments."""
import gzip,json,sys,time,tracemalloc
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.correction import synthetic_inputs
from subpsi.matched import ks_score
from subpsi.revision import count_test,ks_missing
from subpsi.provenance import manifest,save_snapshot,sha256,write_json

NAMES=['null_n250_0000.json.gz','grid_n250_s0.05_m1.4_0000.json.gz','correlation_0000.json.gz']

def main():
    out=ROOT/'results/raw/correction/cost-check';out.mkdir(parents=True,exist_ok=False)
    c=json.loads((ROOT/'configs/revision2.json').read_text());rows=[]
    for name in NAMES:
        with gzip.open(ROOT/'results/raw/revision2'/name,'rt') as f:old=json.load(f)
        with gzip.open(ROOT/'results/raw/correction/software-check'/name,'rt') as f:matched=json.load(f)
        ref,windows,bins,groups,seed=synthetic_inputs(c,old)
        for gi,selection in [(0,'last aggregate block'),(8,'first eligible target block')]:
            g=groups[gi];available=[r for r in matched['tests'] if r['group']==g.name and r['eligible'] and r['feature']=='x']
            if not available:continue
            selected=available[-1] if gi==0 else available[0]
            frames=[d.loc[g.mask(d),'x'] for w,d in windows if selected['opened_look']<=w<=selected['look']]
            x=ref.loc[g.mask(ref),'x'].to_numpy();y=pd.concat(frames).to_numpy()
            a,b=bins['x'].counts(x),bins['x'].counts(y)
            assert len(y)==selected['n_current'] and len(x)==selected['n_reference']
            def psi():return count_test(a,b,seed=[seed,selected['look'],gi,0,0 if selected['opened_look']==selected['look'] else 1],draws=c['permutations'],stop_above=c['alpha']/c['windows'])
            def ks():return ks_score(x,y),ks_missing(x,y)
            for repeat in range(6):
                order=['PSI','KS'] if repeat%2==0 else ['KS','PSI']
                for position,method in enumerate(order):
                    fun=psi if method=='PSI' else ks
                    start=time.perf_counter();fun();elapsed=time.perf_counter()-start
                    tracemalloc.start();fun();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                    rows.append(dict(run=name,selection=selection,group=g.name,look=selected['look'],block_sha256=selected['block_sha256'],method=method,repeat=repeat,order_position=position,
                                     n_reference=len(x),n_current=len(y),seconds=elapsed,python_peak_allocated_bytes=peak,
                                     logical_payload_bytes=int(a.nbytes+b.nbytes if method=='PSI' else x.nbytes+y.nbytes)))
    pd.DataFrame(rows).to_csv(out/'costs.csv',index=False)
    write_json(out/'manifest.json',{**manifest(ROOT,ROOT/'configs/correction/frozen.json'),
               'source_snapshot_sha256':save_snapshot(ROOT,out),'files':{'costs.csv':sha256(out/'costs.csv')},
               'selection':'Same three fixed software-check streams; last aggregate and first supported target block. Six alternating-order repetitions. No condition selection by scores.',
               'scope':'Statistic test only, excluding bin construction and shared input/scheduler. KS includes reported ECDF distance. tracemalloc separately instrumented and can omit native allocations; not total process memory.'})
    print('Cost check complete:',len(rows),'measurements; no additional detection streams.')
if __name__=='__main__':main()

"""Run the approved study once into a new directory; refuse overwrites.

PYTHONPATH=src python scripts/revision3/run_main.py --out results/raw/revision3/main-approved
No remote writes. Raw respondent/draw lineage stays under ignored data/raw/.
"""
import argparse
import datetime
import gzip
import json
import resource
import sys
import time
import traceback
import tracemalloc
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import NumericBins
from subpsi.matched import run_matched
from subpsi.realdata import load_datasets, FrozenLogistic, audit_outcomes, household_pool, constructed_stream
from subpsi.revision import count_test, ks_missing
from subpsi.provenance import sha256, manifest, save_snapshot, write_json

VARIANTS=[('batch50','batch',50),('batch100','batch',100),('accum100','accumulate',100)]
TARGET='SEX=2 & RAC1P=2'


def csv(rows,path):
    pd.DataFrame(rows).to_csv(path,index=False)


def safe_frame(frame,features,groups):
    # Neither labels, model predictions nor row-source IDs enter the monitor.
    cols=list(dict.fromkeys(features+[c for g in groups for c,v in g.selectors]))
    return frame[cols]


def metrics(result,variant,context,onset=6):
    tests=pd.DataFrame(result['tests']); schedule=pd.DataFrame(result['schedule']); out=[]
    for method in ['PSI','KS']:
        for scope,levels in [('aggregate',['aggregate']),('single',['aggregate','single']),('intersection',['aggregate','single','intersection'])]:
            t=tests.loc[tests.level.isin(levels)]; gnames=set(t.group)
            s=schedule.loc[schedule.group.isin(gnames)]
            dec=[d for d in result['decisions'] if d['method']==method and d['scope']==scope]
            hits=[d['look'] for d in dec if d['alert']]
            post=[k for k in hits if k>=onset]
            exact=[d['look'] for d in dec if d['look']>=onset and any(g==TARGET for g,f in d['hits'])]
            target=s.loc[s.group.eq(TARGET)]
            first=s.loc[s.eligible].groupby('group').look.min()
            h=result['metadata']['horizon']
            r={**context,'variant':variant,'method':method,'scope':scope,'any_alert':bool(hits),
               'pre_alert':any(k<onset for k in hits),'post_alert':bool(post),
               'target_post_alert':bool(exact) if scope=='intersection' else None,
               'first_alert_look':min(hits) if hits else None,'first_post_look':min(post) if post else None,
               'first_target_post_look':min(exact) if exact else None,
               'restricted_delay':min(post)-onset if post else h-onset+1,
               'target_restricted_delay':(min(exact)-onset if exact else h-onset+1) if scope=='intersection' else None,
               'coverage':float(t.eligible.mean()),'target_coverage':float(target.eligible.mean()) if len(target) else None,
               'groups_ever_assessed':len(first),'declared_groups':len(gnames),
               'first_assessment_restricted_mean':float(np.mean([first.get(g,h+1) for g in gnames])),
               'assessed_blocks':int(s.eligible.sum()),'unassessed_blocks':int((~s.eligible).sum()),
               'max_age_when_assessed':int(s.loc[s.eligible,'maximum_age'].max()) if s.eligible.any() else None,
               'mean_wait_when_assessed':float(s.loc[s.eligible,'waiting_looks'].mean()) if s.eligible.any() else None,
               'statistic_seconds':float(t[f'{method.lower()}_seconds'].sum()),
               'histogram_setup_seconds':float(t.histogram_setup_seconds.sum()) if method=='PSI' else 0.,
               'shared_collection_seconds':float(schedule.groupby('look').collection_seconds_all_groups.first().sum()),
               'maximum_logical_payload_bytes':int(t[f'{method.lower()}_payload_bytes'].max()) if t.eligible.any() else None,
               'shared_input_frame_bytes':result['metadata']['shared_input_frame_bytes']}
            out.append(r)
    return out


def benchmark(pool,replacement,bins,seed,config):
    """Fixed first unchanged stream, everyone and exact target, first supported block.

Alternate statistic timing order across five repeats; measure allocation peaks
separately to avoid treating tracemalloc-instrumented timings as native timings.
"""
    rows=[]
    for n in config['constructed_controls']['batch_sizes']:
        ref,windows=constructed_stream(pool,replacement,n,seed,'unchanged')
        for group in ['Everyone',TARGET]:
            mask=lambda d: np.ones(len(d),bool) if group=='Everyone' else (d.SEX.eq(2)&d.RAC1P.eq(2)).to_numpy()
            a=ref.loc[mask(ref)]; parts=[]
            for look,d in windows:
                parts.append(d.loc[mask(d)])
                if sum(map(len,parts))>=100: break
            b=pd.concat(parts)
            if min(len(a),len(b))<100: continue
            for fi,(feature,binning) in enumerate(bins.items()):
                x=a[feature].to_numpy(float); y=b[feature].to_numpy(float)
                started=time.perf_counter(); ac=binning.counts(x); bc=binning.counts(y)
                setup=time.perf_counter()-started
                funcs={'PSI':lambda:count_test(ac,bc,seed=[seed,n,fi,99],draws=23999,stop_above=.05/20),
                       'KS':lambda:ks_missing(x,y)}
                for repeat in range(5):
                    for order,method in enumerate(['PSI','KS'] if repeat%2==0 else ['KS','PSI']):
                        started=time.perf_counter(); value=funcs[method](); seconds=time.perf_counter()-started
                        tracemalloc.start(); funcs[method](); _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                        rows.append(dict(batch_n=n,group=group,feature=feature,method=method,repeat=repeat,order=order,
                                         reference_n=len(a),current_n=len(b),through_delivery=look,kernel_seconds=seconds,
                                         setup_histogram_seconds=setup,peak_kernel_allocation_bytes=peak,
                                         logical_payload_bytes=ac.nbytes+bc.nbytes if method=='PSI' else x.nbytes+y.nbytes,
                                         permutations_used=value['draws'] if method=='PSI' else 0))
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
    config_path=ROOT/'configs/revision3/approved.json';config=json.loads(config_path.read_text())
    approval=json.loads((ROOT/'records/revision3/main/approval.json').read_text())
    if not config['main_evaluation_authorized'] or approval['approved_config_sha256']!=sha256(config_path):
        raise ValueError('Missing or changed approved configuration')
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=False)
    private=ROOT/'data/raw/revision3'/out.name;private.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();cpu=time.process_time();m=manifest(ROOT,config_path)
    m.update(status='RUNNING',approval_sha256=sha256(ROOT/'records/revision3/main/approval.json'),
             source_snapshot_sha256=save_snapshot(ROOT,out),output_directory=str(out.relative_to(ROOT)))
    write_json(out/'manifest.json',m)
    try:
        datasets,sources=load_datasets(ROOT,config);m['input_hashes']=sources
        m['load_seconds']=time.perf_counter()-start
        tests=[];schedules=[];decisions=[];audits=[];natural_cost=[];models={};bins_by={}
        for ds in datasets:
            name=ds['name'];setup=time.perf_counter()
            bins={f:NumericBins.fit(ds['design'][f],6) for f in ds['features']};bins_by[name]=bins
            model=FrozenLogistic(ds['model_kind']).fit(ds['fit'])
            models[name]={'model':model.metadata(),'bins':{f:b.metadata() for f,b in bins.items()},
                          'fit_index_sha256':hashlib_ids(ds['fit'].index),'design_index_sha256':hashlib_ids(ds['design'].index),
                          'setup_seconds':time.perf_counter()-setup}
            for variant,policy,minimum in VARIANTS:
                then=time.perf_counter()
                result=run_matched(safe_frame(ds['reference'],ds['features'],ds['groups']),
                    [(year,safe_frame(d,ds['features'],ds['groups'])) for year,d in ds['windows']],
                    bins=bins,groups=ds['groups'],min_n=minimum,policy=policy,inferential=False)
                elapsed=time.perf_counter()-then
                ctx={'dataset':name,'variant':variant}
                tests += [{**ctx,**r} for r in result['tests']]
                schedules += [{**ctx,**r} for r in result['schedule']]
                decisions += [{**ctx,**r} for r in result['decisions']]
                natural_cost.append({**ctx,'engine_seconds':elapsed,**result['metadata']})
            then=time.perf_counter()
            for year,current in ds['audits']:
                audits += [dict(dataset=name,period=year,**r) for r in audit_outcomes(ds['audit_reference'],current,ds['groups'],model)]
            models[name]['audit_seconds']=time.perf_counter()-then
            print('Natural complete:',name,'model fit n=',len(ds['fit']),flush=True)
        csv(tests,out/'natural_tests.csv');csv(schedules,out/'natural_schedule.csv')
        write_json(out/'natural_decisions.json',decisions);csv(audits,out/'natural_outcomes.csv')
        write_json(out/'models_and_bins.json',models);write_json(out/'natural_costs.json',natural_cost)
        m['natural_elapsed_seconds']=time.perf_counter()-start-m['load_seconds']
        acs=datasets[0];pool=household_pool(acs['reference'])
        rep=household_pool(acs['windows'][0][1]);rep=rep.loc[rep.SEX.eq(2)&rep.RAC1P.eq(2)]
        pools={'reference':pool,'replacement':rep};poolinfo={}
        for name,d in pools.items():
            path=private/f'{name}_pool.csv';d[['record_id','household_id','SPORDER','role']].to_csv(path,index=False)
            poolinfo[name]={'n':len(d),'lineage_sha256':sha256(path),'path':str(path.relative_to(ROOT))}
        write_json(out/'source_pools.json',poolinfo)
        summary=[];timings=[];lineage_hashes={};control_start=time.perf_counter()
        for n in config['constructed_controls']['batch_sizes']:
            for repeat,seed in enumerate(config['implementation_freeze']['repeat_seeds']):
                for condition in ['unchanged','substitution']:
                    if time.process_time()-cpu>config['compute']['local_cpu_cap_seconds']:
                        raise TimeoutError('Approved two-hour CPU cap reached; preserve incomplete run')
                    sid=f'n{n}_{condition}_{repeat:02d}';then=time.perf_counter()
                    ref,windows=constructed_stream(pool,rep,n,seed,condition)
                    lineage=pd.concat([ref[['source_id']],*[d[['source_id']] for _,d in windows]])
                    lineage.index.name='draw_id';path=private/f'{sid}.csv.gz';lineage.to_csv(path,compression={'method':'gzip','mtime':0})
                    lineage_hashes[str(path.relative_to(ROOT))]=sha256(path)
                    generation_seconds=time.perf_counter()-then
                    ctx={'stream':sid,'batch_n':n,'condition':condition,'repeat':repeat,'seed':seed}
                    results={};elapsed={}
                    for variant,policy,minimum in VARIANTS:
                        then=time.perf_counter()
                        result=run_matched(safe_frame(ref,acs['features'],acs['groups']),
                            [(look,safe_frame(d,acs['features'],acs['groups'])) for look,d in windows],
                            bins=bins_by['ACS_MA'],groups=acs['groups'],min_n=minimum,policy=policy,
                            alpha=.05,draws=23999,inferential=True,
                            seed=int(np.random.SeedSequence([seed,n,4]).generate_state(1)[0]))
                        elapsed[variant]=time.perf_counter()-then
                        summary += metrics(result,variant,ctx)
                        results[variant]=result
                    path=out/f'{sid}.json.gz'
                    with gzip.GzipFile(filename=str(path),mode='wb',mtime=0) as f:
                        f.write(json.dumps({'context':ctx,'results':results},allow_nan=False).encode())
                    timings.append({**ctx,'generation_lineage_seconds':generation_seconds,
                                    **{f'{k}_engine_seconds':v for k,v in elapsed.items()},
                                    'process_high_water_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
                    print(f'Control {len(timings)}/120 {sid}: {sum(elapsed.values()):.2f}s',flush=True)
        csv(summary,out/'control_stream_metrics.csv');csv(timings,out/'control_timings.csv')
        m['control_elapsed_seconds']=time.perf_counter()-control_start
        csv(benchmark(pool,rep,bins_by['ACS_MA'],config['implementation_freeze']['repeat_seeds'][0],config),out/'alternating_kernel_benchmark.csv')
        m.update(status='COMPLETE',streams=len(timings),private_lineage_hashes=lineage_hashes,
                 elapsed_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
                 process_high_water_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 files={p.name:sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'},
                 interpretation='Natural scores/outcomes descriptive. Conditional resampling controls have known intervention delivery, not natural onset. No new algorithmic novelty claimed.')
        write_json(out/'manifest.json',m)
        print('COMPLETE',len(timings),'streams;',round(m['elapsed_seconds'],2),'seconds;',m['process_high_water_rss_kib'],'KiB high-water RSS',flush=True)
    except BaseException as error:
        m.update(status='FAILED',error=repr(error),traceback=traceback.format_exc(),elapsed_seconds=time.perf_counter()-start)
        write_json(out/'manifest.json',m);raise


def hashlib_ids(ids):
    import hashlib
    return hashlib.sha256(json.dumps(list(ids)).encode()).hexdigest()

if __name__=='__main__':main()

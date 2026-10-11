#!/usr/bin/env python3
import argparse,json,sys,time,traceback,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import NumericBins,compare,decisions,validate_resolution
from subpsi.scenarios import predefined_groups,assert_disjoint,fit_logistic,evaluate,tpr_gap
from subpsi.provenance import manifest,write_json,sha256,save_snapshot,verify_inputs

COLUMNS=['age','workclass','fnlwgt','education','education-num','marital-status','occupation','relationship','race','sex','capital-gain','capital-loss','hours-per-week','native-country','income']


def prepare(config):
    c=config; data=ROOT/'data/raw/adult'; source=json.loads((ROOT/'records/adult_dataset.json').read_text())
    verify_inputs(data,source['files'])
    frames=[]
    for file in ['adult.data','adult.test']:
        f=pd.read_csv(data/file,names=COLUMNS,skipinitialspace=True,comment='|',na_values='?')
        f['id']=[f'{file}:{i}' for i in range(len(f))]; frames.append(f)
    all_data=pd.concat(frames,ignore_index=True); total=len(all_data)
    all_data['income']=all_data.income.str.removesuffix('.')
    duplicate_predictors=all_data.duplicated(subset=COLUMNS[:-1],keep='first')
    all_data=all_data.loc[~duplicate_predictors].copy()
    if all_data[c['model_features']].isna().any().any(): raise ValueError('Unexpected missing numeric model inputs')
    if not set(all_data.sex)<= {'Female','Male'}: raise ValueError('Unexpected group categories')
    if not set(all_data.income)<= {'>50K','<=50K'}: raise ValueError('Unexpected outcomes')
    all_data['y']=(all_data.income=='>50K').astype(int)
    all_data['A']=(all_data.sex=='Female').astype(int)
    all_data['B']=(all_data.age>=c['age_cutoff']).astype(int)
    order=np.random.default_rng(c['split_seed']).permutation(len(all_data)); all_data=all_data.iloc[order].reset_index(drop=True)
    roles={}; offset=0
    for role in ['fit','design','reference','audit']:
        n=c['n_'+role]; roles[role]=all_data.iloc[offset:offset+n].copy(); offset+=n
    roles['pool']=all_data.iloc[offset:].copy()
    assert_disjoint(*roles.values())
    return roles,{'original_rows':total,'duplicate_predictor_rows_removed':int(duplicate_predictors.sum()),'retained_rows':len(all_data),
                  'role_sizes':{k:len(v) for k,v in roles.items()},'source':source,
                  'identity_limit':'No personal subject IDs exist; duplicate predictor rows removed, same-person identity cannot be verified.'}


def sample_windows(pool,c,scenario,repeat):
    rng=np.random.default_rng([c['seed'],c['scenarios'].index(scenario),repeat]); remaining=pool.copy()
    strata=[(a,b) for a in [0,1] for b in [0,1]]
    probs=np.array([((pool.A==a)&(pool.B==b)).mean() for a,b in strata])
    windows=[]
    for w in range(1,c['windows']+1):
        ns=rng.multinomial(c['n_window'],probs); selected=[]
        for (a,b),n in zip(strata,ns):
            candidate=remaining.loc[(remaining.A==a)&(remaining.B==b)]
            if n>len(candidate): raise ValueError('Insufficient unique records in stratum; no fallback resampling')
            weights=np.ones(len(candidate))
            if scenario=='female_hours_tilt' and w>=c['onset_window'] and a==1:
                weights[candidate['hours-per-week'].to_numpy()>c['high_hours_cutoff']]=c['high_hours_weight']
            selected.extend(rng.choice(candidate.index,n,replace=False,p=weights/weights.sum()).tolist())
        current=remaining.loc[selected].copy(); remaining=remaining.drop(index=selected); windows.append(current)
    assert_disjoint(*windows)
    return windows


def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='configs/adult.json'); p.add_argument('--out',required=True); args=p.parse_args()
    cfg=ROOT/args.config; c=json.loads(cfg.read_text()); out=ROOT/args.out; out.mkdir(parents=True,exist_ok=False)
    write_json(out/'config.json',c); meta=manifest(ROOT,cfg); meta['source_snapshot_sha256']=save_snapshot(ROOT,out); meta['kind']='public_semi_synthetic_conditional'; write_json(out/'manifest.json',meta)
    roles,info=prepare(c); write_json(out/'dataset.json',info)
    write_json(out/'roles.json',{k:v.id.tolist() for k,v in roles.items()})
    model=fit_logistic(roles['fit'],c['model_features']); groups=predefined_groups()
    bins={f:NumericBins.fit(roles['design'][f],c['n_bins']) for f in c['monitored_features']}
    baseline=evaluate(model,roles['audit'],groups); basegap=tpr_gap(baseline)
    validate_resolution(c['n_resamples'],len(groups)*len(bins),c['alpha'])
    started=time.perf_counter(); failures=0
    for scenario in c['scenarios']:
        for repeat in range(c['repeats']):
            start=time.perf_counter()
            try:
                frames=sample_windows(roles['pool'],c,scenario,repeat); assert_disjoint(roles['fit'],roles['design'],roles['reference'],roles['audit'],*frames)
                windows=[]
                for w,current in enumerate(frames,1):
                    rows=compare(roles['reference'][list(bins)+['A','B']],current[list(bins)+['A','B']],bins,groups,min_n=c['min_n'],n_resamples=c['n_resamples'],
                                 seed=[c['seed'],c['scenarios'].index(scenario),repeat,w,901],pseudocount=c['pseudocount'])
                    performance=evaluate(model,current,groups); gap=tpr_gap(performance)
                    windows.append({'window':w,'active':w>=c['onset_window'],'tests':rows,'methods':decisions(rows,c['alpha'],c['practical_threshold']),
                                    'performance':performance,'tpr_gap':gap,'tpr_gap_change':gap-basegap if gap is not None and basegap is not None else None,
                                    'source_ids':current.id.tolist(),'input_sha256':hashlib.sha256(current.to_csv(index=False).encode()).hexdigest()})
                result={'scenario':scenario,'repeat':repeat,'model':model,'bins':{f:b.metadata() for f,b in bins.items()},
                        'baseline_performance':baseline,'baseline_tpr_gap':basegap,'windows':windows,'runtime_seconds':time.perf_counter()-start}
                write_json(out/f'{scenario}_{repeat:04}.json',result)
            except Exception as exc:
                failures+=1; write_json(out/f'failure_{scenario}_{repeat:04}.json',{'error':repr(exc),'traceback':traceback.format_exc()})
            if (repeat+1)%10==0 or repeat==0: print(scenario,repeat+1,'/',c['repeats'],f'{time.perf_counter()-started:.1f}s',flush=True)
    files=[p for s in c['scenarios'] for p in out.glob(s+'_*.json')]
    meta.update({'runtime_seconds':time.perf_counter()-started,'planned_runs':len(c['scenarios'])*c['repeats'],'failures':failures,
                 'result_hashes':{p.name:sha256(p) for p in sorted(files)},'config_saved_sha256':sha256(out/'config.json'),
                 'support_hashes':{n:sha256(out/n) for n in ['dataset.json','roles.json']}})
    write_json(out/'manifest.json',meta)
    if failures: raise SystemExit(f'{failures} runs failed; inspect logs')

if __name__=='__main__': main()

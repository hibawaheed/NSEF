#!/usr/bin/env python3
"""Checkpointed repeated synthetic runs. Never overwrite an existing run."""
import argparse,json,sys,time,traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import NumericBins,compare,decisions,validate_resolution
from subpsi.scenarios import generate,predefined_groups,assert_disjoint,fit_logistic,evaluate,tpr_gap
from subpsi.provenance import manifest,write_json,sha256,save_snapshot


def one_run(config,scenario,repeat):
    c=config; sid=c['scenarios'].index(scenario)
    entropy=[c['seed'],sid,repeat]
    streams=np.random.SeedSequence(entropy).spawn(4+2*c['windows'])
    frames=[generate(c[n],np.random.default_rng(streams[i]),scenario,share=c['affected_share'],magnitude=c['magnitude'],role=role)
            for i,(n,role) in enumerate([('n_fit','fit'),('n_design','design'),('n_reference','reference'),('n_audit','audit')])]
    fit,design,reference,audit=frames
    groups=predefined_groups(); model=fit_logistic(fit)
    bins={f:NumericBins.fit(design[f],c['n_bins']) for f in ['signal','nuisance']}
    validate_resolution(c['n_resamples'],len(groups)*len(bins),c['alpha'])
    baseline=evaluate(model,audit,groups); basegap=tpr_gap(baseline)
    windows=[]
    for w in range(1,c['windows']+1):
        current=generate(c['n_window'],np.random.default_rng(streams[4+2*(w-1)]),scenario,
                         active=w>=c['onset_window'],share=c['affected_share'],magnitude=c['magnitude'],role=f'window{w}')
        assert_disjoint(*frames,current)
        rows=compare(reference[list(bins)+['A','B']],current[list(bins)+['A','B']],bins,groups,min_n=c['min_n'],n_resamples=c['n_resamples'],
                     seed=streams[5+2*(w-1)].generate_state(4).tolist(),pseudocount=c['pseudocount'])
        performance=evaluate(model,current,groups); gap=tpr_gap(performance)
        windows.append({'window':w,'active':w>=c['onset_window'],'tests':rows,
                        'methods':decisions(rows,c['alpha'],c['practical_threshold']),
                        'performance':performance,'tpr_gap':gap,'tpr_gap_change':None if gap is None or basegap is None else gap-basegap,
                        'input_sha256':__import__('hashlib').sha256(current.to_csv(index=False).encode()).hexdigest()})
    return {'scenario':scenario,'repeat':repeat,'seed_entropy':entropy,'model':model,
            'bins':{f:b.metadata() for f,b in bins.items()},'baseline_performance':baseline,'baseline_tpr_gap':basegap,
            'role_hashes':{name:__import__('hashlib').sha256(frame.to_csv(index=False).encode()).hexdigest() for name,frame in zip(['fit','design','reference','audit'],frames)},'windows':windows}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',default='configs/synthetic.json'); parser.add_argument('--out',required=True)
    args=parser.parse_args(); cfg=ROOT/args.config; c=json.loads(cfg.read_text()); out=ROOT/args.out
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'config.json',c); meta=manifest(ROOT,cfg); meta['source_snapshot_sha256']=save_snapshot(ROOT,out); meta['kind']='synthetic_exploratory'; write_json(out/'manifest.json',meta)
    started=time.perf_counter(); failures=[]
    for scenario in c['scenarios']:
        for repeat in range(c['repeats']):
            target=out/f'{scenario}_{repeat:04}.json'; start=time.perf_counter()
            try:
                result=one_run(c,scenario,repeat); result['runtime_seconds']=time.perf_counter()-start; write_json(target,result)
            except Exception as exc:
                failure={'scenario':scenario,'repeat':repeat,'error':repr(exc),'traceback':traceback.format_exc()}; failures.append(failure)
                write_json(out/f'failure_{scenario}_{repeat:04}.json',failure)
            if (repeat+1)%10==0 or repeat==0: print(scenario,repeat+1,'/',c['repeats'],f'{time.perf_counter()-started:.1f}s',flush=True)
    meta.update({'runtime_seconds':time.perf_counter()-started,'planned_runs':len(c['scenarios'])*c['repeats'],'failures':len(failures),
                 'result_hashes':{p.name:sha256(p) for p in sorted(out.glob('S*.json'))},'config_saved_sha256':sha256(out/'config.json')})
    write_json(out/'manifest.json',meta)
    if failures: raise SystemExit(f'{len(failures)} runs failed; inspect failure logs')

if __name__=='__main__': main()

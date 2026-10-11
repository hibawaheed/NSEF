"""Run only the user-requested correction. Refuses to overwrite any result."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from subpsi.correction import AttemptBins, TrainingMajority, restore_model, matched_v2, stream_metrics
from subpsi.core import NumericBins
from subpsi.matched import run_matched
from subpsi.realdata import load_datasets, audit_outcomes
from subpsi.provenance import manifest, sha256, write_json, save_snapshot

CFG = ROOT/'configs/correction/frozen.json'


def natural(c, out):
    cfg = ROOT/c['oulad']['original_config']
    if sha256(cfg) != c['oulad']['original_config_sha256']:
        raise ValueError('Original config changed')
    original_config = json.loads(cfg.read_text())
    datasets, sources = load_datasets(ROOT, original_config)
    d = datasets[1]; original = ROOT/c['oulad']['original_results']
    saved = json.loads((original/'models_and_bins.json').read_text())['OULAD_BBB']
    design_counts = {str(k):int(v) for k,v in d['design'].num_of_prev_attempts.value_counts().items()}
    if design_counts != c['oulad']['design_counts']:
        raise ValueError('Historical design evidence changed')
    old_bins = {f:NumericBins(tuple(float(x) for x in m['edges'])) for f,m in saved['bins'].items()}
    bins = {**old_bins, 'num_of_prev_attempts':AttemptBins()}
    model = restore_model(saved['model'])
    baseline = TrainingMajority().fit(d['fit'].label)
    if {str(i):v for i,v in enumerate(baseline.counts)} != c['oulad']['expected_training_labels']:
        raise ValueError('Training label counts changed')
    rows = []; schedules = []; decisions = []; counts = []
    features = d['features'] + list(original_config['oulad']['group_levels'])
    for name, policy, minimum in c['oulad']['policies']:
        r = run_matched(d['reference'][features], [(t,f[features]) for t,f in d['windows']],
                        bins=bins, groups=d['groups'], min_n=minimum, policy=policy, inferential=False)
        rows.extend({'variant':name, 'dataset':d['name'], **v} for v in r['tests'])
        schedules.extend({'variant':name, **v} for v in r['schedule'])
        decisions.extend({'variant':name, **v} for v in r['decisions'])
    for period, frame in [('design_2013J',d['design']), ('reference_2013J',d['reference']), ('monitor_2014J',d['windows'][0][1])]:
        for group in d['groups']:
            for version, bs in [('original_v3',old_bins), ('corrected',bins)]:
                for feature,b in bs.items():
                    for bi,n in enumerate(b.counts(frame.loc[group.mask(frame),feature])):
                        counts.append(dict(period=period,group=group.name,version=version,feature=feature,bin=bi,count=int(n),
                                           label=b.metadata().get('labels', [str(i) for i in range(b.size)])[bi]))
    outcomes = []
    for name, predictor in [('Frozen logistic',model), ('Training-majority baseline',baseline)]:
        for period, frame in d['audits']:
            outcomes.extend({'model':name,'time':period,**r} for r in audit_outcomes(d['audit_reference'],frame,d['groups'],predictor,minimum=20))
    for filename, data in [('natural_tests.csv',rows),('natural_schedule.csv',schedules),('bin_counts.csv',counts),('outcomes.csv',outcomes)]:
        pd.DataFrame(data).to_csv(out/filename,index=False)
    write_json(out/'natural_decisions.json',decisions)
    # Check unaffected scores, block IDs and frozen-model audit counts against V3.
    previous = pd.read_csv(original/'natural_tests.csv').query("dataset == 'OULAD_BBB'")
    now = pd.DataFrame(rows)
    keys = ['variant','group','feature','time']
    joined = now.merge(previous,on=keys,validate='one_to_one',suffixes=('_new','_old'))
    if len(joined) != len(now) or len(now) != len(previous):
        raise ValueError('Natural comparison lost rows')
    for field in ['n_reference','n_current','eligible','block_sha256','ks_d']:
        a,b = joined[field+'_new'],joined[field+'_old']
        if not (a.eq(b) | (a.isna() & b.isna())).all():
            if field!='ks_d' or not np.allclose(a,b,rtol=0,atol=1e-14,equal_nan=True):
                raise ValueError(f'Unchanged natural field differs: {field}')
    credits = joined.feature.eq('studied_credits')
    if not np.allclose(joined.loc[credits,'psi_new'],joined.loc[credits,'psi_old'],rtol=0,atol=1e-14,equal_nan=True):
        raise ValueError('Unchanged credit PSI differs')
    original_outcomes = pd.read_csv(original/'natural_outcomes.csv').query("dataset == 'OULAD_BBB'").rename(columns={'period':'time'})
    new_outcomes = pd.DataFrame(outcomes).query("model == 'Frozen logistic'")
    audit = new_outcomes.merge(original_outcomes,on=['group','metric','time'],validate='one_to_one',suffixes=('_new','_old'))
    for field in [x for x in new_outcomes if x.endswith(('numerator','denominator'))]:
        if not audit[field+'_new'].eq(audit[field+'_old']).all():
            raise ValueError('Frozen model audit changed')
    changes = joined[keys+['eligible_new','n_reference_new','n_current_new','psi_old','psi_new','ks_d_old','ks_d_new']]
    changes.to_csv(out/'old_vs_corrected.csv',index=False)
    write_json(out/'models_and_bins.json',{'frozen_model':model.metadata(),'training_majority':baseline.metadata(),
                                         'old_bins':saved['bins'],'corrected_bins':{f:b.metadata() for f,b in bins.items()}})
    return {'sources':sources,'original_models_sha256':sha256(original/'models_and_bins.json'),
            'checks':'Unchanged block IDs, counts, eligibility, KS, credit PSI and all frozen-model outcome counts match original V3',
            'label':'Post-result correction; natural descriptive comparisons, no drift-detection accuracy',
            'design_counts':design_counts}


def benchmark(c, out, smoke=False):
    cfg = ROOT/c['v2']['config']; original = ROOT/c['v2']['original_results']
    if sha256(cfg) != c['v2']['config_sha256']:
        raise ValueError('Original V2 configuration changed')
    v2 = json.loads(cfg.read_text()); old_manifest = json.loads((original/'manifest.json').read_text())
    cases = json.loads((original/'cases.json').read_text())
    names = [f'{case["id"]}_{rep:04}.json.gz' for case in cases for rep in range(case['repeats'])]
    if set(names)!=set(old_manifest['run_hashes']) or len(names)!=c['v2']['streams']:
        raise ValueError('Declared V2 benchmark mismatch')
    if smoke:
        names=['null_n250_0000.json.gz','grid_n250_s0.05_m1.4_0000.json.gz','correlation_0000.json.gz']
    start=time.perf_counter(); cpu=time.process_time(); rows=[]; hashes={}; warnings=[]; timings=[]
    for i,name in enumerate(names):
        if datetime.now().astimezone() > datetime.fromisoformat(c['deadline_local']) or time.perf_counter()-start > c['maximum_benchmark_seconds']:
            write_json(out/'INCOMPLETE.json',{'reason':'Time box reached; no full benchmark claim permitted','completed':len(hashes),'files':hashes})
            raise RuntimeError('Bounded correction period exhausted')
        source=original/name
        if sha256(source)!=old_manifest['run_hashes'][name]:
            raise ValueError('Original raw V2 result changed')
        with gzip.open(source,'rt') as f: old=json.load(f)
        started=time.perf_counter(); result=matched_v2(v2,old)
        timings.append({'run':name,'wall_seconds':time.perf_counter()-started})
        result.update({'case':old['case'],'repeat':old['repeat'],'seed':old['seed'], 'original_sha256':sha256(source)})
        with gzip.GzipFile(filename=str(out/name),mode='wb',mtime=0) as f:
            f.write(json.dumps(result,allow_nan=False,separators=(',',':')).encode())
        hashes[name]=sha256(out/name)
        rows.extend({'run':name,**r} for r in stream_metrics(result,v2,old))
        warnings.extend({'run':name, 'look':r['look'],'group':r['group'],'feature':r['feature'],'warning':r['ks_warning']} for r in result['tests'] if r.get('ks_warning'))
        if (i+1)%25==0 or i+1==len(names):
            print(f'{i+1}/{len(names)} streams; {time.perf_counter()-start:.1f}s; historical PSI parity passed',flush=True)
    pd.DataFrame(rows).to_csv(out/'streams.csv',index=False)
    pd.DataFrame(timings).to_csv(out/'engine_timings.csv',index=False)
    pd.DataFrame(warnings,columns=['run','look','group','feature','warning']).to_csv(out/'ks_warnings.csv',index=False)
    return {'run_hashes':hashes,'runs':len(hashes),'smoke':smoke,'cpu_seconds':time.process_time()-cpu,
            'original_manifest_sha256':sha256(original/'manifest.json'), 'all_original_psi_parity_checks_passed':True,
            'label':'Retrospective matched comparator on original mathematical simulations; no new human records; not prospectively untouched validation',
            'ks_warnings':len(warnings)}


def main():
    p=argparse.ArgumentParser(); p.add_argument('study',choices=['oulad','v2']);p.add_argument('--out',required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args()
    out=ROOT/a.out;out.mkdir(parents=True,exist_ok=False);c=json.loads(CFG.read_text())
    meta=manifest(ROOT,CFG);meta['source_snapshot_sha256']=save_snapshot(ROOT,out)
    write_json(out/'config.json',c);write_json(out/'started.json',meta);start=time.perf_counter()
    try:
        detail=natural(c,out) if a.study=='oulad' else benchmark(c,out,a.smoke)
        write_json(out/'manifest.json',{**meta,**detail,'wall_seconds':time.perf_counter()-start,
                   'peak_process_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name not in {'manifest.json'}}})
        print('COMPLETE',a.study,detail.get('checks',detail.get('runs')),flush=True)
    except Exception:
        write_json(out/'FAILED.json',{'traceback':traceback.format_exc(),'elapsed_seconds':time.perf_counter()-start})
        raise

if __name__=='__main__':main()

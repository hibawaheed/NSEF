"""Complete, fixed-cell reporting for the bounded retrospective comparison."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.realdata import wilson, paired_interval
from subpsi.provenance import manifest, sha256, write_json, save_snapshot

BINARY=['stream_alert','pre_alert','post_alert','target_detected','target_ever_assessed']
CONTINUOUS=['restricted_delay','target_restricted_delay','target_first_assessment_restricted',
            'target_assessed_fraction','eligible_fraction','maximum_block_age','test_seconds',
            'maximum_logical_payload_bytes','shared_input_frame_bytes']


def stratified_interval(frame, metric, method=None):
    """Resample paired stream repeats *within* each fixed cell, then equal weight.

    method=None returns PSI minus KS. Individual intervals use the same draws.
    """
    rng=np.random.default_rng(948271); samples=[]; estimates=[]
    for _,cell in frame.groupby('id',sort=True):
        p=cell.pivot(index='repeat',columns='method',values=metric).sort_index().astype(float)
        if p.isna().any().any(): raise ValueError('Incomplete method pairs')
        v=(p.PSI-p.KS if method is None else p[method]).to_numpy(float)
        estimates.append(v.mean());samples.append(v[rng.integers(len(v),size=(2000,len(v)))].mean(axis=1))
    means=np.mean(samples,axis=0);lo,hi=np.quantile(means,[.025,.975])
    return {'estimate':float(np.mean(estimates)),'low':float(lo),'high':float(hi),
            'interval':'fixed-cell stratified paired bootstrap, 2000 resamples',
            'degenerate':bool(np.all(means==means[0]))}


def summarize(raw, out):
    m=json.loads((raw/'manifest.json').read_text())
    if m['runs']!=1820 or m['smoke'] or not m['all_original_psi_parity_checks_passed']:
        raise ValueError('Cannot summarize incomplete/smoke benchmark as evidence')
    for name,expected in m['files'].items():
        if sha256(raw/name)!=expected: raise ValueError('Raw result hash changed')
    d=pd.read_csv(raw/'streams.csv')
    if len(d)!=3640 or d.duplicated(['run','method']).any(): raise ValueError('Invalid stream pairs')
    cases=json.loads((ROOT/'results/raw/revision2/cases.json').read_text())
    rows=[]; paired=[]
    for case in cases:
        cell=d[d.id.eq(case['id'])]
        for method in ['PSI','KS']:
            part=cell[cell.method.eq(method)]
            if len(part)!=case['repeats']: raise ValueError('Missing declared repetitions')
            for metric in BINARY+CONTINUOUS:
                v=part[metric].astype(float);binary=metric in BINARY
                lo,hi=wilson(int(v.sum()),len(v)) if binary else (None,None)
                rows.append({**case,'method':method,'metric':metric,'n_streams':len(v),
                             'successes':int(v.sum()) if binary else None,'estimate':v.mean(),
                             'low':lo,'high':hi,'minimum':v.min(),'maximum':v.max(),
                             'interval':'95% Wilson' if binary else 'descriptive mean; paired differences reported separately'})
        for metric in BINARY+CONTINUOUS:
            p=cell.pivot(index='repeat',columns='method',values=metric).sort_index()
            result=paired_interval(p.PSI,p.KS)
            paired.append({**case,'metric':metric,**result,'contrast':'PSI minus KS',
                           'interval':'paired stream bootstrap, 2000 resamples; identical pairs can give degenerate intervals'})
    pd.DataFrame(rows).to_csv(out/'all_cells.csv',index=False)
    pd.DataFrame(paired).to_csv(out/'paired_cells.csv',index=False)
    aggregate=[]
    for n in [250,1000]:
        for kind in ['null','shift']:
            subset=d[d.n.eq(n)&d.kind.eq(kind)]
            for metric in ['stream_alert'] if kind=='null' else ['post_alert','target_detected','target_restricted_delay','eligible_fraction']:
                for method in ['PSI','KS','PSI minus KS']:
                    if kind=='null' and method!='PSI minus KS':
                        v=subset.loc[subset.method.eq(method),metric];lo,hi=wilson(int(v.sum()),len(v))
                        result={'estimate':v.mean(),'low':lo,'high':hi,'interval':'95% Wilson','degenerate':False}
                    else:
                        result=stratified_interval(subset,metric,None if method=='PSI minus KS' else method)
                    part=subset[subset.method.eq('PSI' if method=='PSI minus KS' else method)]
                    aggregate.append({'n':n,'kind':kind,'metric':metric,'method':method,'n_streams':len(part),
                                      'successes':int(part[metric].sum()) if metric in BINARY and method!='PSI minus KS' else None,**result})
    pd.DataFrame(aggregate).to_csv(out/'benchmark_aggregate.csv',index=False)
    # Direct comparison with the old reporting table, without rewriting it.
    old=pd.read_csv(ROOT/'results/revision2/streams.csv')
    old=old[old.run.str.startswith('revision2/') & old.method.eq('Accumulated PSI')].copy()
    old['run']=old.run.str.removeprefix('revision2/')
    pair=d[d.method.eq('PSI')].merge(old,on='run',validate='one_to_one',suffixes=('_new','_old'))
    for col in ['stream_alert','pre_alert','post_alert','target_detected','restricted_delay','target_ever_assessed','target_assessed_fraction','eligible_fraction']:
        if not np.allclose(pair[col+'_new'].astype(float),pair[col+'_old'].astype(float),rtol=0,atol=1e-14):
            raise ValueError('Old reported metric differs: '+col)
    # Retain every natural group, both features and all three outcome metrics.
    ou=ROOT/'results/raw/correction/oulad'
    inputs=pd.read_csv(ou/'natural_tests.csv').query("variant=='accum100'")
    outcomes=pd.read_csv(ou/'outcomes.csv')
    new=[]
    for feature,part in inputs.groupby('feature',sort=False):
        selected=part[['group','time','feature','psi','ks_d','status','n_reference','n_current']]
        new.append(selected.merge(outcomes,on=['group','time'],validate='one_to_many'))
    joined=pd.concat(new,ignore_index=True)
    if len(joined)!=108: raise ValueError('Lost natural pairs')
    joined.to_csv(out/'oulad_input_outcome_pairs.csv',index=False)
    sources={'v2_manifest':sha256(raw/'manifest.json'),'oulad_manifest':sha256(ou/'manifest.json')}
    write_json(out/'manifest.json',{**manifest(ROOT,ROOT/'configs/correction/frozen.json'),'inputs':sources,
                                   'source_snapshot_sha256':save_snapshot(ROOT,out),
                                   'files':{p.name:sha256(p) for p in out.glob('*.csv')},
                                   'original_v2_report_parity':'All 1820 accumulated-PSI stream endpoints match the saved V2 table'})
    print(pd.DataFrame(aggregate).query("metric in ['stream_alert','post_alert']").to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',default='results/raw/correction/v2-matched');p.add_argument('--out',default='results/summary/correction');a=p.parse_args()
    out=ROOT/a.out;out.mkdir(parents=True,exist_ok=False);summarize(ROOT/a.raw,out)

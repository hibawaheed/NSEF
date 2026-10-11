"""Complete-stream summaries; no natural detection accuracy or p-values."""
import argparse,gzip,json,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.realdata import wilson,paired_interval
from subpsi.provenance import sha256,manifest,write_json,save_snapshot


def join_input_outcome(pairs,outcomes):
    keys=['dataset','period','group','level']
    if pairs.duplicated(keys+['feature']).any() or outcomes.duplicated(keys+['metric']).any():
        raise ValueError('Duplicate input-feature or outcome-metric key')
    # Each feature has one input row and three distinct outcome metrics per view.
    parts=[part.merge(outcomes,on=keys,how='left',validate='one_to_many')
           for _,part in pairs.groupby('feature',sort=False)]
    joined=pd.concat(parts,ignore_index=True)
    if len(joined)!=3*len(pairs) or joined.metric.isna().any():
        raise ValueError('Missing outcome metric in input/outcome pairing')
    return joined


def summarize(raw,out):
    raw=Path(raw);out=Path(out);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    source=json.loads((raw/'manifest.json').read_text())
    if source['status']!='COMPLETE' or source['streams']!=120:raise ValueError('Incomplete approved experiment')
    for name,h in source['files'].items():
        if sha256(raw/name)!=h:raise ValueError('Changed raw result: '+name)
    config=ROOT/'configs/revision3/approved.json';c=json.loads(config.read_text())
    d=pd.read_csv(raw/'control_stream_metrics.csv')
    keys=['batch_n','condition','variant','method','scope']
    proportions=[];descriptive=[]
    binary=['any_alert','pre_alert','post_alert','target_post_alert']
    continuous=['coverage','target_coverage','restricted_delay','target_restricted_delay',
                'first_assessment_restricted_mean','groups_ever_assessed','mean_wait_when_assessed',
                'max_age_when_assessed','statistic_seconds','histogram_setup_seconds',
                'maximum_logical_payload_bytes','shared_collection_seconds','shared_input_frame_bytes']
    for key,x in d.groupby(keys,sort=False):
        ctx=dict(zip(keys,key))
        if len(x)!=30 or x.repeat.nunique()!=30:raise ValueError('Missing or duplicate stream')
        for metric in binary:
            values=x[metric].dropna().astype(bool)
            if not len(values):continue
            k=int(values.sum());lo,hi=wilson(k,len(values))
            proportions.append(dict(**ctx,metric=metric,successes=k,n=len(values),estimate=k/len(values),low=lo,high=hi,
                                    interval='95% Wilson across complete conditional streams'))
        for metric in continuous:
            values=x[metric].dropna()
            descriptive.append(dict(**ctx,metric=metric,n=len(values),mean=values.mean() if len(values) else None,
                                    minimum=values.min() if len(values) else None,maximum=values.max() if len(values) else None))
    pd.DataFrame(proportions).to_csv(out/'control_proportions.csv',index=False)
    pd.DataFrame(descriptive).to_csv(out/'control_descriptive.csv',index=False)
    paired=[]
    # Always align by complete stream/repeat, never bootstrap individual looks.
    for (n,condition,scope),cell in d.groupby(['batch_n','condition','scope'],sort=False):
        contrasts=[]
        for variant in ['batch50','batch100','accum100']:
            contrasts.append((f'{variant}: PSI minus KS',cell.query('variant == @variant and method == "PSI"'),cell.query('variant == @variant and method == "KS"')))
        for method in ['PSI','KS']:
            contrasts.append((f'{method}: accum100 minus batch100',cell.query('method == @method and variant == "accum100"'),cell.query('method == @method and variant == "batch100"')))
            contrasts.append((f'{method}: accum100 minus batch50',cell.query('method == @method and variant == "accum100"'),cell.query('method == @method and variant == "batch50"')))
        for contrast,a,b in contrasts:
            a=a.sort_values('repeat');b=b.sort_values('repeat')
            if a.stream.tolist()!=b.stream.tolist():raise ValueError('Unpaired comparison')
            for metric in binary+['coverage','target_coverage','restricted_delay','target_restricted_delay','first_assessment_restricted_mean']:
                if a[metric].isna().all() and b[metric].isna().all():continue
                stats=paired_interval(a[metric].to_numpy(float),b[metric].to_numpy(float),
                                      seed=c['implementation_freeze']['bootstrap_seed'],draws=2000)
                paired.append(dict(batch_n=n,condition=condition,scope=scope,contrast=contrast,metric=metric,**stats,
                                   interpretation='conditional empirical paired-stream interval; degenerate intervals do not establish equivalence'))
    pd.DataFrame(paired).to_csv(out/'paired_differences.csv',index=False)
    coverage=[];warnings=[]
    for path in sorted(raw.glob('n*.json.gz')):
        record=json.loads(gzip.decompress(path.read_bytes()));ctx=record['context']
        for variant,result in record['results'].items():
            schedule=pd.DataFrame(result['schedule'])
            for group,s in schedule.groupby('group',sort=False):
                ready=s.loc[s.eligible];first=ready.look.min() if len(ready) else None
                coverage.append(dict(**ctx,variant=variant,group=group,coverage=s.eligible.mean(),
                                     first_assessment_look=first,first_assessment_restricted=first if first is not None else 21,
                                     never_assessed=first is None,eligible_blocks=len(ready),unassessed_blocks=len(s)-len(ready),
                                     reference_n=int(s.n_reference.iloc[0]),
                                     maximum_age_when_assessed=ready.maximum_age.max() if len(ready) else None,
                                     mean_wait_when_assessed=ready.waiting_looks.mean() if len(ready) else None,
                                     total_ready_current_records=int(ready.n_current.sum()),final_unassessed_records=int(s.iloc[-1].n_current) if not s.iloc[-1].eligible else 0))
            warnings += [dict(**ctx,variant=variant,group=t['group'],look=t['look'],feature=t['feature'],warning=t['ks_warning'])
                         for t in result['tests'] if t.get('ks_warning')]
    pd.DataFrame(coverage).to_csv(out/'control_group_coverage.csv',index=False)
    pd.DataFrame(warnings,columns=['stream','batch_n','condition','repeat','seed','variant','group','look','feature','warning']).to_csv(out/'ks_warnings.csv',index=False)
    nt=pd.read_csv(raw/'natural_tests.csv');no=pd.read_csv(raw/'natural_outcomes.csv')
    # All methods' support and same-record comparisons, with unsupported cases retained.
    agree=[]
    for (dataset,period,group,feature),x in nt.groupby(['dataset','time','group','feature'],sort=False):
        a=x.set_index('variant');eligible=a.eligible.all()
        agree.append(dict(dataset=dataset,period=period,group=group,feature=feature,
                          all_policies_assessed=bool(eligible),same_record_block=a.block_sha256.nunique()==1,
                          psi_identical=bool(eligible and a.psi.nunique()==1),ks_identical=bool(eligible and a.ks_d.nunique()==1)))
    pd.DataFrame(agree).to_csv(out/'natural_policy_agreement.csv',index=False)
    pairs=nt.loc[nt.variant.eq('batch100'),['dataset','time','group','feature','level','status','psi','ks_d','n_reference','n_current']].rename(columns={'time':'period','status':'input_status'})
    pairs=join_input_outcome(pairs,no)
    pairs['pair_status']=np.where(pairs.input_status.ne('assessed'),'input_unsupported',np.where(pairs.gap_status.eq('assessed'),'descriptive_pair',pairs.gap_status))
    pairs.to_csv(out/'input_outcome_pairs.csv',index=False)
    m=manifest(ROOT,config);m.update(status='COMPLETE',raw_manifest_sha256=sha256(raw/'manifest.json'),raw_directory=str(raw.relative_to(ROOT)),
        source_snapshot_sha256=save_snapshot(ROOT,out),elapsed_seconds=time.perf_counter()-start,
        files={p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'})
    write_json(out/'manifest.json',m)
    print('Summaries complete;',len(d),'method-stream rows;',len(coverage),'group-stream rows;',len(warnings),'KS warnings.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--out',required=True);a=p.parse_args();summarize(ROOT/a.raw,ROOT/a.out)

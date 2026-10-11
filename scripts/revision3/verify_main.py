"""Read-only verification of the main study, plus deterministic numerical replays."""
import argparse,gzip,hashlib,json,runpy,sys,time,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import NumericBins,adjust_pvalues
from subpsi.matched import run_matched
from subpsi.realdata import load_datasets,household_pool,constructed_stream
from subpsi.provenance import sha256


def without_timing(value):
    if isinstance(value,dict):return {k:without_timing(v) for k,v in value.items() if 'seconds' not in k}
    if isinstance(value,list):return [without_timing(v) for v in value]
    return value


def verify(raw,tables,figures,replay=True):
    checked=0
    for directory in [raw,tables,figures]:
        m=json.loads((directory/'manifest.json').read_text());assert m['status']=='COMPLETE'
        for p,h in m['files'].items():assert sha256(directory/p)==h,(directory,p)
        checked+=len(m['files'])
        assert sha256(directory/'source_snapshot.zip')==m['source_snapshot_sha256']
        with zipfile.ZipFile(directory/'source_snapshot.zip') as archive:
            for path,expected in m['source_hashes'].items():
                assert hashlib.sha256(archive.read(path)).hexdigest()==expected,path
    m=json.loads((raw/'manifest.json').read_text())
    for p,h in {**m['input_hashes'],**m['private_lineage_hashes']}.items():assert sha256(ROOT/p)==h,p
    config=json.loads((ROOT/'configs/revision3/approved.json').read_text());assert m['config_sha256']==sha256(ROOT/'configs/revision3/approved.json')
    approval=json.loads((ROOT/'records/revision3/main/approval.json').read_text());assert approval['approved_config_sha256']==m['config_sha256']
    # Preparation source and v1/v2 files are byte-preserved.
    prep=json.loads((ROOT/'records/revision3/delivery_manifest.json').read_text())
    for p,h in prep['files'].items():assert sha256(ROOT/p)==h,p
    baseline=json.loads((ROOT/'records/revision3/baseline_inventory.json').read_text())
    entries=baseline['files']
    for p,h in entries.items():assert sha256(ROOT/p)==h,p
    paths=sorted(raw.glob('n*.json.gz'));assert len(paths)==120
    contexts=[];opportunities=0;unsupported=0
    for path in paths:
        data=json.loads(gzip.decompress(path.read_bytes()));ctx=data['context'];contexts.append(ctx)
        assert ctx['seed']==config['implementation_freeze']['repeat_seeds'][ctx['repeat']]
        for variant,result in data['results'].items():
            minimum=50 if variant=='batch50' else 100
            assert len(result['tests'])==1200 and len(result['schedule'])==600 and len(result['decisions'])==120
            for t in result['tests']:
                assert t['eligible']==(min(t['n_reference'],t['n_current'])>=minimum)
                assert t['status']==('assessed' if t['eligible'] else 'insufficient_support')
                if not t['eligible']:assert t['psi'] is None and t['p']==1 and t['ks_p']==1;unsupported+=1
                opportunities+=1
            for dec in result['decisions']:
                levels={'aggregate'} if dec['scope']=='aggregate' else {'aggregate','single'} if dec['scope']=='single' else {'aggregate','single','intersection'}
                tests=[t for t in result['tests'] if t['look']==dec['look'] and t['level'] in levels]
                adjusted=adjust_pvalues([t['p'] if dec['method']=='PSI' else t['ks_p'] for t in tests])
                hits=[[t['group'],t['feature']] for t,p in zip(tests,adjusted) if t['eligible'] and p<=.05/20]
                assert hits==dec['hits'] and bool(hits)==dec['alert'] and dec['family_size']==len(tests)
                assert adjusted.tolist()==dec['adjusted_pvalues']
            # Two statistics have exactly one shared block and one support decision per feature.
            tests=pd.DataFrame(result['tests'])
            assert tests.groupby(['look','group']).block_sha256.nunique().eq(1).all()
    counts=pd.DataFrame(contexts).groupby(['batch_n','condition']).size();assert counts.eq(30).all() and len(counts)==4
    summaries=pd.read_csv(raw/'control_stream_metrics.csv');assert len(summaries)==2160
    coverage=summaries.pivot(index=['stream','variant','scope'],columns='method',values='coverage');assert coverage.PSI.equals(coverage.KS)
    proportions=pd.read_csv(tables/'control_proportions.csv');assert proportions.n.eq(30).all()
    assert (proportions.successes/proportions.n==proportions.estimate).all() or np.allclose(proportions.successes/proportions.n,proportions.estimate)
    natural=pd.read_csv(raw/'natural_tests.csv');assert natural['p'].isna().all() and natural.ks_p.isna().all()
    assert all(d['alert'] is None and d['cutoff'] is None for d in json.loads((raw/'natural_decisions.json').read_text()))
    assert natural.groupby(['dataset','time','variant']).eligible.sum().to_dict()=={(dataset,year,v):n for dataset,years,n in [('ACS_MA',[2017,2018,2019],36),('OULAD_BBB',[2014],8)] for year in years for v in ['batch50','batch100','accum100']}
    agreement=pd.read_csv(tables/'natural_policy_agreement.csv');assessed=agreement.loc[agreement.all_policies_assessed]
    assert assessed[['same_record_block','psi_identical','ks_identical']].all().all()
    outcomes=pd.read_csv(raw/'natural_outcomes.csv')
    for _,r in outcomes.iterrows():
        for period in ['baseline','current']:
            for prefix in ['','complement_']:
                num,den=r[f'{period}_{prefix}numerator'],r[f'{period}_{prefix}denominator'];rate=r[f'{period}_{prefix}rate']
                assert 0<=num<=den
                assert (pd.isna(rate) if den<20 else np.isclose(rate,num/den))
        if r.gap_status=='assessed':
            assert np.isclose(r.gap_change,(r.current_rate-r.current_complement_rate)-(r.baseline_rate-r.baseline_complement_rate))
    # No respondent identifiers or predictions are written to chart CSVs.
    for path in figures.glob('*.csv'):
        columns=set(pd.read_csv(path,nrows=0).columns)
        assert not columns.intersection({'record_id','household_id','SERIALNO','SPORDER','id_student','source_id','draw_id','pred'})
    print(f'Verified {checked} artifact hashes, all input/private-lineage hashes, {len(entries)} baseline files and all {len(prep["files"])} preparation deliverables.')
    print(f'Verified {len(paths)} streams, {opportunities} test opportunities, {unsupported} unsupported opportunities, all Holm decisions, matched support, descriptive natural outputs and outcome denominators.')
    if replay:
        functions=runpy.run_path(str(ROOT/'scripts/revision3/run_main.py'));safe_frame=functions['safe_frame']
        datasets,_=load_datasets(ROOT,config);acs=datasets[0]
        pool=household_pool(acs['reference']);rep=household_pool(acs['windows'][0][1]);rep=rep.loc[rep.SEX.eq(2)&rep.RAC1P.eq(2)]
        bins={f:NumericBins.fit(acs['design'][f],6) for f in acs['features']}
        # First repeat in every design cell, fixed without looking at alerts.
        for n in [250,1000]:
            for condition in ['unchanged','substitution']:
                sid=f'n{n}_{condition}_00';saved=json.loads(gzip.decompress((raw/f'{sid}.json.gz').read_bytes()))
                seed=config['implementation_freeze']['repeat_seeds'][0]
                ref,windows=constructed_stream(pool,rep,n,seed,condition)
                for variant,policy,minimum in functions['VARIANTS']:
                    result=run_matched(safe_frame(ref,acs['features'],acs['groups']),[(look,safe_frame(d,acs['features'],acs['groups'])) for look,d in windows],
                        bins=bins,groups=acs['groups'],min_n=minimum,policy=policy,alpha=.05,draws=23999,inferential=True,
                        seed=int(np.random.SeedSequence([seed,n,4]).generate_state(1)[0]))
                    assert without_timing(result)==without_timing(saved['results'][variant]),(sid,variant)
                print('Exact numerical replay passed:',sid,flush=True)
    print('PASS: main-study verification; no remote writes.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',default='results/raw/revision3/main-approved');p.add_argument('--tables',default='results/summary/revision3/main-approved-checked');p.add_argument('--figures',default='figures/revision3/main-approved-checked');p.add_argument('--no-replay',action='store_true');a=p.parse_args()
    verify(ROOT/a.raw,ROOT/a.tables,ROOT/a.figures,replay=not a.no_replay)

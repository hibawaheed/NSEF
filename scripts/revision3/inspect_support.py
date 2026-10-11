"""Schema, keys and support only. No drift statistics or model predictions."""
import argparse,datetime,hashlib,json,sys,zipfile,time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.matched import declared_groups
from subpsi.provenance import sha256,environment

def role(key,period):
    v=int(hashlib.sha256(f'r3-role-31721|{key}'.encode()).hexdigest()[:16],16)/2**64
    return ('fit' if v<.5 else 'design' if v<.75 else 'calibration') if period==2015 else ('reference' if v<.5 else 'audit') if period==2016 else ('monitor' if v<.5 else 'audit')

def support_rows(df,groups,dataset,period,role_name,label):
    rows=[]
    for g in groups:
        x=df.loc[g.mask(df)];y=label.loc[x.index]
        rows.append(dict(dataset=dataset,period=period,role=role_name,group=g.name,level=g.level,n=len(x),positive_n=int(y.sum()),negative_n=int((~y).sum()),support50=len(x)>=50,support100=len(x)>=100,label_support20=min(y.sum(),(~y).sum())>=20))
    return rows

def acs(out):
    groups=declared_groups({'SEX':[1,2],'RAC1P':list(range(1,10))});summary=[];rows=[];receipts=[]
    for year in range(2015,2020):
        p=ROOT/f'data/raw/revision3/acs/{year}/csv_pma.zip';receipt=json.loads(p.with_suffix('.receipt.json').read_text());assert sha256(p)==receipt['sha256'];receipts.append(receipt)
        with zipfile.ZipFile(p) as z:
            member=next(n for n in z.namelist() if n.endswith('.csv'))
            with z.open(member) as f:header=pd.read_csv(f,nrows=0).columns.tolist()
            wanted={'SERIALNO','SPORDER','ST','AGEP','SCHL','SEX','RAC1P','ESR','PWGTP','FAGEP','FSCHLP','FESRP','FRACP','FSEXP'}
            wanted.update(c for c in header if c.upper().startswith('PWGTP'))
            with z.open(member) as f:raw=pd.read_csv(f,usecols=lambda c:c in wanted,dtype={'SERIALNO':str})
            member_hash=hashlib.sha256(z.read(member)).hexdigest()
        assert not raw.duplicated(['SERIALNO','SPORDER']).any()
        assert raw.ST.eq(25).all()
        # Explicit proposed age restriction; upstream code and README disagree.
        df=raw.loc[raw.AGEP.between(16,90)].copy()
        if df.ESR.isna().any():raise ValueError('Unexpected missing adult ESR')
        df['record_id']=[f'{year}:{s}:{o}' for s,o in zip(df.SERIALNO,df.SPORDER)]
        df['household_id']=[f'{year}:{s}' for s in df.SERIALNO]
        df.index=df.record_id
        df['role']=[role(k,year) for k in df.household_id]
        assert df.groupby('household_id').role.nunique().max()==1
        y=df.ESR.eq(1)
        rows.extend(support_rows(df,groups,'ACS_MA',year,'all_eligible',y))
        for name,sub in df.groupby('role'):rows.extend(support_rows(sub,groups,'ACS_MA',year,name,y))
        # Row-level keys/lineage are private ignored artifacts, never chart exports.
        private=ROOT/'data/raw/revision3/lineage';private.mkdir(exist_ok=True)
        df[['record_id','household_id','role']].to_csv(private/f'acs_{year}_proposed_roles.csv',index=False)
        summary.append(dict(year=year,raw_rows=len(raw),eligible_rows=len(df),excluded_age=len(raw)-len(df),households=df.SERIALNO.nunique(),duplicate_person_keys=int(raw.duplicated(['SERIALNO','SPORDER']).sum()),columns=header,selected_missing={c:int(df[c].isna().sum()) for c in ['AGEP','SCHL','SEX','RAC1P','ESR']},codes={c:sorted(df[c].dropna().unique().astype(int).tolist()) for c in ['SEX','RAC1P','SCHL','ESR']},allocation_counts={c:int(df[c].eq(1).sum()) for c in ['FAGEP','FSCHLP','FESRP','FRACP','FSEXP']},replicate_weight_columns=sum(c.upper().startswith('PWGTP') and c.upper()!='PWGTP' for c in header),nonpositive_weights=int(df.PWGTP.le(0).sum()),member=member,member_sha256=member_hash,role_lineage_sha256=sha256(private/f'acs_{year}_proposed_roles.csv')))
        print('ACS',year,len(raw),'raw;',len(df),'age 16–90;',df.groupby('role').size().to_dict(),flush=True)
    pd.DataFrame(rows).to_csv(out/'acs_support.csv',index=False)
    (out/'acs_schema.json').write_text(json.dumps({'summary':summary,'sources':receipts},indent=2)+'\n')

def oulad(out):
    source=ROOT/'data/raw/revision3/oulad/metadata'
    receipt=json.loads((source/'receipt.json').read_text())
    assert sha256(source/'source-prefix.bin')==receipt['prefix_sha256']
    for m in receipt['members']:assert sha256(source/m['name'])==m['sha256']
    info=pd.read_csv(source/'studentInfo.csv',na_values=['?']);reg=pd.read_csv(source/'studentRegistration.csv',na_values=['?']);courses=pd.read_csv(source/'courses.csv')
    hashes={m['name']:m['sha256'] for m in receipt['members']}
    keys=['code_module','code_presentation','id_student'];assert not info.duplicated(keys).any() and not reg.duplicated(keys).any()
    counts=info.groupby(keys[:2]).size().rename('n').reset_index();counts.to_csv(out/'oulad_cohort_inventory.csv',index=False)
    table=counts.pivot(index='code_module',columns='code_presentation',values='n').fillna(0)
    candidates=sorted(table.index[(table['2013J']>=500)&(table['2014J']>=500)])
    if not candidates:raise ValueError('No eligible same-season pair')
    module=candidates[0]
    pair=info.loc[info.code_module.eq(module)&info.code_presentation.isin(['2013J','2014J'])].merge(reg,on=keys,how='left',validate='one_to_one',indicator=True)
    assert pair['_merge'].eq('both').all()
    old_ids=set(pair.loc[pair.code_presentation.eq('2013J'),'id_student']);new_ids=set(pair.loc[pair.code_presentation.eq('2014J'),'id_student']);repeat=old_ids&new_ids
    # At day 0: already registered and not withdrawn before/on start.
    eligibility=pair.date_registration.le(0)&(pair.date_unregistration.isna()|pair.date_unregistration.gt(0))
    eligible=pair.loc[eligibility].copy()
    excluded_repeat=eligible.code_presentation.eq('2014J')&eligible.id_student.isin(old_ids)
    excluded_repeat_n=int(excluded_repeat.sum());eligible=eligible.loc[~excluded_repeat].copy()
    def assign(i,p):
        v=int(hashlib.sha256(f'r3-oulad-31721|{i}'.encode()).hexdigest()[:16],16)/2**64
        return ('fit' if v<.4 else 'design' if v<.6 else 'reference' if v<.8 else 'audit') if p=='2013J' else ('monitor' if v<.5 else 'audit')
    eligible['role']=[assign(i,p) for i,p in zip(eligible.id_student,eligible.code_presentation)]
    groups=declared_groups({'gender':['F','M'],'disability':['N','Y']});rows=[]
    for period,sub in eligible.groupby('code_presentation'):
        y=sub.final_result.isin(['Pass','Distinction']);rows.extend(support_rows(sub,groups,'OULAD_'+module,period,'all_eligible',y))
        for role_name,rs in sub.groupby('role'):rows.extend(support_rows(rs,groups,'OULAD_'+module,period,role_name,y))
    pd.DataFrame(rows).to_csv(out/'oulad_support.csv',index=False)
    private=ROOT/'data/raw/revision3/lineage';private.mkdir(exist_ok=True)
    eligible[keys+['role']].to_csv(private/'oulad_proposed_roles.csv',index=False)
    record={'source':receipt,'member_hashes':hashes,'raw_rows':len(info),'unique_students':int(info.id_student.nunique()),'repeat_enrolment_rows':int(info.id_student.duplicated().sum()),'selected_module':module,'selection_rule':'alphabetically first module with >=500 in each 2013J/2014J, chosen without outcomes','pair_raw_rows':len(pair),'pair_repeated_students':len(repeat),'excluded_day0_ineligible':int((~eligibility).sum()),'excluded_later_repeat_rows':excluded_repeat_n,'retained_rows':len(eligible),'unknown_results':sorted(set(eligible.final_result)-{'Pass','Distinction','Fail','Withdrawn'}),'missing':{c:int(eligible[c].isna().sum()) for c in ['gender','disability','num_of_prev_attempts','studied_credits','final_result']},'presentations':courses.loc[courses.code_module.eq(module)].to_dict('records'),'role_lineage_sha256':sha256(private/'oulad_proposed_roles.csv'),'time_basis':'presentation year and J season; day 0 prediction; no invented timestamps; no VLE clicks read'}
    (out/'oulad_schema.json').write_text(json.dumps(record,indent=2)+'\n')
    print('OULAD',module,'pair:',len(pair),'retained:',len(eligible),'repeated people:',len(repeat),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',choices=['acs','oulad'],required=True);p.add_argument('--out',required=True);a=p.parse_args()
    out=ROOT/a.out;out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    (acs if a.dataset=='acs' else oulad)(out)
    m={'purpose':'schema/support only; no main evaluation','accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha256(Path(__file__)),'group_code_sha256':sha256(ROOT/'src/subpsi/matched.py'),'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'runtime_seconds':time.perf_counter()-start,'environment':environment()}
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
if __name__=='__main__':main()

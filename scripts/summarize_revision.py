#!/usr/bin/env python3
import gzip,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from subpsi.revision import METHODS
from subpsi.provenance import sha256,write_json


def main():
    out=ROOT/'results/revision2';out.mkdir(exist_ok=True,parents=True);summary=[];rates=[];meta={};runtime=[]
    c=json.loads((ROOT/'configs/revision2.json').read_text());onset=c['onset']
    for folder in ['revision2','revision2-public']:
        path=ROOT/'results/raw'/folder
        man=json.loads((path/'manifest.json').read_text());meta[folder]=sha256(path/'manifest.json')
        if man.get('failures')!=0: raise ValueError('Incomplete or failed run set')
        for filename,expected in man['run_hashes'].items():
            p=path/filename
            if sha256(p)!=expected: raise ValueError('Changed raw result')
            with gzip.open(p,'rt') as f:r=json.load(f)
            case=r['case']; sid=f'{folder}/{filename}'
            for method in METHODS:
                ds=[d for d in r['decisions'] if d['method']==method];post=[d for d in ds if d['window']>=onset];pre=[d for d in ds if d['window']<onset]
                hit=[d['window'] for d in post if d['alert']];target=[d['window'] for d in post if 8 in d['hits']]
                row={'run':sid,'case':case['id'],'kind':case['kind'],'n':case['n'],'share':case.get('share'),'magnitude':case.get('magnitude'),'cancel':case.get('cancel'),'split':r.get('split'),'repeat':r['repeat'],'method':method,
                     'stream_alert':any(d['alert'] for d in ds),'pre_alert':any(d['alert'] for d in pre),'post_alert':bool(hit),'target_detected':bool(target),'delay':min(hit)-onset if hit else None,'target_delay':min(target)-onset if target else None,
                     'restricted_delay':min(hit)-onset if hit else c['windows']-onset+1,'target_ever_assessed':any(8 in d['eligible_groups'] for d in post),'target_assessed_fraction':np.mean([8 in d['eligible_groups'] for d in post]),
                     'eligible_fraction':np.mean([len(d['eligible_groups'])/9 for d in post]),'target_first_assessment':next((d['window']-onset for d in post if 8 in d['eligible_groups']),None)}
                summary.append(row)
            for g in range(9):
                for metric in ['TPR','FPR','Accuracy']:
                    rr=[v for v in r['outcomes'] if v['group']==g and v['metric']==metric and v['window']>=onset]
                    vals=[v['current_rate'] for v in rr if v['current_rate'] is not None];base=rr[0]['reference_rate']
                    rates.append({'run':sid,'case':case['id'],'group':g,'metric':metric,'reference_rate':base,'current_rate':np.mean(vals) if vals else None,'change':np.mean(vals)-base if vals and base is not None else None,'minimum_current_denominator':min(v['current_n'] for v in rr)})
            for method,field in [('PSI','psi_seconds'),('KS','ks_seconds')]:
                ts=[t[field] for t in r['tests'] if t['policy']=='batch']
                runtime.append({'run':sid,'case':case['id'],'test':method,'seconds':sum(ts),'scope':'all ordinary group-feature tests across stream; excludes accumulation, audits and shared setup'})
    pd.DataFrame(summary).to_csv(out/'streams.csv',index=False);pd.DataFrame(rates).to_csv(out/'outcomes.csv',index=False);pd.DataFrame(runtime).to_csv(out/'timing.csv',index=False)
    write_json(out/'manifest.json',{'raw_manifests':meta,'files':{p.name:sha256(p) for p in out.glob('*.csv')},'config_sha256':sha256(ROOT/'configs/revision2.json')})
    df=pd.DataFrame(summary)
    print(df.groupby(['kind','method'])[['stream_alert','post_alert','target_detected','target_ever_assessed']].mean().round(3).to_string())
if __name__=='__main__':main()

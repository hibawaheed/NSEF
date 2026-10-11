"""Post-run implementation diagnostics; no tuned replacements or extra main runs."""
import argparse,json,sys,time
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.realdata import load_datasets,household_pool
from subpsi.core import NumericBins,psi_counts
from subpsi.matched import ks_score
from subpsi.provenance import manifest,sha256,write_json,save_snapshot


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='results/summary/revision3/postrun-diagnostics');args=parser.parse_args()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=False)
    config=ROOT/'configs/revision3/approved.json';datasets,sources=load_datasets(ROOT,json.loads(config.read_text()))
    rows=[];start=time.perf_counter()
    for ds in datasets:
        bins={f:NumericBins.fit(ds['design'][f],6) for f in ds['features']}
        for role,period,d in [('design',2015 if ds['name']=='ACS_MA' else 2013,ds['design']),('reference',2016 if ds['name']=='ACS_MA' else 2013,ds['reference']),*[('monitor',p,d) for p,d in ds['windows']]]:
            for feature,b in bins.items():
                encoded=b.encode(d[feature]);counts=b.counts(d[feature])
                for i,n in enumerate(counts):
                    vals=d[feature].iloc[encoded==i]
                    rows.append(dict(dataset=ds['name'],role=role,period=period,feature=feature,bin=i,n=int(n),
                                     missing_bin=i==b.size-1,distinct_nonmissing_values=int(vals.nunique()),
                                     left=str(b.edges[i]) if i<len(b.edges)-1 else 'missing',
                                     right=str(b.edges[i+1]) if i<len(b.edges)-1 else 'missing',
                                     is_only_occupied_finite_bin=bool(n and sum(counts[:-1]>0)==1)))
    pd.DataFrame(rows).to_csv(out/'bin_occupancy.csv',index=False)
    acs=datasets[0];a=household_pool(acs['reference']);a=a.loc[a.SEX.eq(2)&a.RAC1P.eq(2)]
    b=household_pool(acs['windows'][0][1]);b=b.loc[b.SEX.eq(2)&b.RAC1P.eq(2)]
    scores=[]
    for f in acs['features']:
        binning=NumericBins.fit(acs['design'][f],6)
        scores.append(dict(feature=f,reference_pool_n=len(a),substitution_pool_n=len(b),
                           psi=float(psi_counts(binning.counts(a[f]),binning.counts(b[f]))),**ks_score(a[f],b[f])))
    pd.DataFrame(scores).to_csv(out/'target_source_pool_distances.csv',index=False)
    m=manifest(ROOT,config);m.update(status='COMPLETE',purpose='Post-run bin occupancy and source-substitution integrity diagnostics. Descriptive only; settings not changed.',input_hashes=sources,source_snapshot_sha256=save_snapshot(ROOT,out),elapsed_seconds=time.perf_counter()-start,
        files={p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'})
    write_json(out/'manifest.json',m);print(pd.DataFrame(scores).to_string(index=False))
    print('Diagnostics complete; original study unchanged.')
if __name__=='__main__':main()

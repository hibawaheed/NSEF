#!/usr/bin/env python3
import gzip,json,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'scripts'))
from run_adult import prepare,sample_windows
from subpsi.scenarios import fit_logistic,predict
from subpsi.revision import run_stream
from subpsi.provenance import manifest,write_json,save_snapshot,sha256

def convert(frame,model):
    return {'A':frame.A.to_numpy(),'B':frame.B.to_numpy(),'x':frame['hours-per-week'].to_numpy(float),'x2':frame['education-num'].to_numpy(float),'y':frame.y.to_numpy(),'pred':predict(model,frame)}

def main():
    c=json.loads((ROOT/'configs/revision2.json').read_text());out=ROOT/'results/raw/revision2-public';out.mkdir(parents=True,exist_ok=False)
    meta=manifest(ROOT,ROOT/'configs/revision2.json');meta['snapshot_sha256']=save_snapshot(ROOT,out);write_json(out/'config.json',c);write_json(out/'manifest.json',meta)
    base=json.loads((ROOT/'configs/adult.json').read_text());base.update(windows=c['windows'],onset_window=c['onset'],n_window=500,seed=c['seed']+15001)
    start=time.perf_counter();hashes={}
    for split in c['public_split_seeds']:
        base['split_seed']=split;roles,info=prepare(base);model=fit_logistic(roles['fit'],base['model_features'])
        write_json(out/f'roles_{split}.json',{'info':info,'ids':{k:v.id.tolist() for k,v in roles.items()},'model':model})
        for scenario in base['scenarios']:
            for repeat in range(c['public_repeats_per_split']):
                frames=sample_windows(roles['pool'],base,scenario,repeat)
                result=run_stream(convert(roles['reference'],model),convert(roles['design'],model),convert(roles['audit'],model),[convert(f,model) for f in frames],c,split+repeat*1001+base['scenarios'].index(scenario)*99999)
                result.update(case={'id':scenario,'kind':'public_null' if scenario=='null' else 'public_tilt','n':500,'share':None},repeat=repeat,split=split,source_ids=[f.id.tolist() for f in frames])
                name=f'{split}_{scenario}_{repeat:04}.json.gz';p=out/name
                with gzip.GzipFile(filename=str(p),mode='wb',mtime=0) as z:z.write(json.dumps(result,allow_nan=False,separators=(',',':')).encode())
                hashes[name]=sha256(p)
                if (repeat+1)%5==0: print(split,scenario,repeat+1,'/',c['public_repeats_per_split'],round(time.perf_counter()-start,1),'s',flush=True)
    meta.update(runs=len(hashes),run_hashes=hashes,runtime_seconds=time.perf_counter()-start,failures=0);write_json(out/'manifest.json',meta)
if __name__=='__main__':main()

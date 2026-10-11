#!/usr/bin/env python3
import argparse,gzip,json,sys,time,traceback,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from subpsi.revision import synthetic_run
from subpsi.provenance import manifest,write_json,save_snapshot,sha256

def cases(c):
    out=[]
    for n in c['batch_sizes']: out.append({'id':f'null_n{n}','kind':'null','n':n,'share':.1,'repeats':c['null_repeats']})
    for n in c['batch_sizes']:
        for s in c['shares']:
            for m in c['magnitudes']: out.append({'id':f'grid_n{n}_s{s}_m{m}','kind':'shift','n':n,'share':s,'magnitude':m,'repeats':c['grid_repeats']})
    for cancel in c['cancellation']: out.append({'id':f'cancel_{cancel}','kind':'cancellation','cancel':cancel,'n':1000,'share':.25,'magnitude':1.6,'repeats':c['robustness_repeats']})
    for k,m in [('gradual',1.4),('missing',.4),('benign',1.4),('outcome',1.),('composition',1.),('correlation',1.)]:
        out.append({'id':k,'kind':k,'n':1000,'share':.1,'magnitude':m,'repeats':c['robustness_repeats']})
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--smoke',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
    cfg=ROOT/'configs/revision2.json';c=json.loads(cfg.read_text());cs=cases(c)
    if a.smoke:
        cs=[cs[0],cs[13],cs[-4],cs[-3],cs[-1]]
        for x in cs: x['repeats']=1
    out=ROOT/a.out;out.mkdir(parents=True,exist_ok=a.resume)
    if a.resume:
        meta=json.loads((out/'manifest.json').read_text())
        if meta['config_sha256']!=sha256(cfg): raise ValueError('Configuration changed; cannot resume')
        for name,hashed in meta['source_hashes'].items():
            if name.endswith('.py') and sha256(ROOT/name)!=hashed: raise ValueError('Source changed; cannot resume')
    else:
        write_json(out/'config.json',c);write_json(out/'cases.json',cs);meta=manifest(ROOT,cfg);meta['snapshot_sha256']=save_snapshot(ROOT,out);write_json(out/'manifest.json',meta)
    start=time.perf_counter();failed=[];hashes={};done=0
    for i,case in enumerate(cs):
        t=time.perf_counter()
        for repeat in range(case['repeats']):
            f=out/f'{case["id"]}_{repeat:04}.json.gz'
            if not f.exists():
                try:
                    result=synthetic_run(c,case,repeat,c['seed']+int(hashlib.sha256(case['id'].encode()).hexdigest()[:7],16))
                    with gzip.GzipFile(filename=str(f),mode='wb',mtime=0) as z:z.write(json.dumps(result,allow_nan=False,separators=(',',':')).encode())
                except Exception as e:
                    failed.append({'case':case['id'],'repeat':repeat,'error':str(e),'trace':traceback.format_exc()});write_json(out/'failures.json',failed);raise
            hashes[f.name]=sha256(f);done+=1
            if (repeat+1)%10==0:print(case['id'],repeat+1,'/',case['repeats'],round(time.perf_counter()-start,1),'s',flush=True)
        print('CASE COMPLETE',case['id'],round(time.perf_counter()-t,1),'s',flush=True)
    meta.update({'runs':done,'failures':len(failed),'run_hashes':hashes,'runtime_seconds':time.perf_counter()-start,'smoke':a.smoke});write_json(out/'manifest.json',meta)
if __name__=='__main__':main()

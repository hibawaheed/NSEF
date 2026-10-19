"""One fresh, sequential benchmark process. No cProfile or RNG tracing here."""
import time
PROCESS_START_W=time.perf_counter();PROCESS_START_C=time.process_time()
from common import *
import argparse,resource,os,gc,hashlib
from subpsi.low_compute_baseline import run_baseline
from subpsi.low_compute import iter_monitor

TEST_COMMON=['group','feature','level','look','time','block_sha256','n_current','n_reference','eligible','opened_look','status','policy']
def scientific_look(value,method):
    fields=TEST_COMMON+(['psi','p','draws','censored'] if method=='PSI' else ['ks_p','ks_d','ks_status'])
    return dict(tests=[{k:r[k] for k in fields} for r in value['tests']],
        schedule=[{k:v for k,v in r.items() if 'seconds' not in k} for r in value['schedule']],
        decisions=[d for d in value['decisions'] if d['method']==method])

def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=list('ABCD'),required=True);p.add_argument('--workload',required=True);p.add_argument('--repeat',type=int,required=True);p.add_argument('--out',required=True);a=p.parse_args()
    c=configuration();work={'primary':c['primary'],'secondary':c['secondary'],'prefix5':c['prefixes'][0],'prefix10':c['prefixes'][1]}[a.workload]
    record=ROOT/a.out
    if record.exists():raise FileExistsError(record)
    manifest=json.loads((ROOT/'records/low_compute/2026-10-18/benchmark_execution_manifest.json').read_text())
    for name,h in manifest['code_sha256'].items():
        if sha256(ROOT/name)!=h:raise ValueError('Benchmark code changed after freeze: '+name)
    if sha256(CONFIG)!=manifest['benchmark_config_sha256']:raise ValueError('Benchmark selection changed')
    startup_w=time.perf_counter()-PROCESS_START_W;startup_c=time.process_time()-PROCESS_START_C
    start=time.perf_counter();cpu=time.process_time();rows=[]
    directory=ROOT/f'data/raw/low_compute/2026-10-18/benchmark_outputs/{a.workload}/{a.repeat}/{a.variant}';directory.mkdir(parents=True,exist_ok=False)
    for cell in [x for x in c['inputs'] if x['cell'] in work['cells']]:
        w0=time.perf_counter();c0=time.process_time();loadw=loadc=outw=outc=0.;output_bytes=0;digest=hashlib.sha256()
        def incoming():
            nonlocal loadw,loadc
            for file in cell['files'][:work['prefix']+1]:
                w,cc=time.perf_counter(),time.process_time();f=frame(c,file);loadw+=time.perf_counter()-w;loadc+=time.process_time()-cc
                yield f if file['look']==0 else (file['look'],f)
        inputs=incoming();kw=definitions(c,work['target'],aggregate=a.variant=='D');kw.update(seed=cell['seed'],allow_prefix=work['prefix']<20)
        method='KS' if a.variant=='C' else 'PSI';stats={}
        with (directory/f"stream-{cell['cell']:03}.jsonl").open('wb',buffering=8192) as output:
            def write(value):
                nonlocal outw,outc,output_bytes
                w,cc=time.perf_counter(),time.process_time();data=(json.dumps(scientific_look(value,method),sort_keys=True,separators=(',',':'))+'\n').encode();output.write(data);digest.update(data);output_bytes+=len(data);outw+=time.perf_counter()-w;outc+=time.process_time()-cc
            if a.variant=='A':
                ref=next(inputs);windows=list(inputs);ew,ec=time.perf_counter(),time.process_time()
                result=run_baseline(ref,windows,**kw);enginew=time.perf_counter()-ew;enginec=time.process_time()-ec;stats=result['metadata']
                for look in range(1,work['prefix']+1):write({key:[r for r in result[key] if r['look']==look] for key in ['tests','schedule','decisions']})
                frame_bytes=int(ref.memory_usage(index=True,deep=True).sum())+sum(int(f.memory_usage(index=True,deep=True).sum()) for _,f in windows)+stats['current_frame_bytes']
                del result,ref,windows
            else:
                ref=next(inputs);ew,ec=time.perf_counter(),time.process_time();lw0,lc0=loadw,loadc
                engine=iter_monitor(ref,inputs,method=method,stats=stats,**kw);del ref
                for value in engine:write(value)
                enginew=time.perf_counter()-ew-(loadw-lw0)-outw;enginec=time.process_time()-ec-(loadc-lc0)-outc;frame_bytes=None
            w,cc=time.perf_counter(),time.process_time();output.flush();os.fsync(output.fileno());outw+=time.perf_counter()-w;outc+=time.process_time()-cc
        lat=stats.pop('batch_latency_wall');prefix=work['prefix']
        row=dict(variant=a.variant,workload=a.workload,repeat=a.repeat,warmup=a.repeat==-1,cell=cell['cell'],condition=cell['condition'],source_repeat=cell['repeat'],policy=work['policy'],batches=prefix,reference_n=10000,incoming_records=1000*prefix,
          elapsed_wall=time.perf_counter()-w0,elapsed_cpu=time.process_time()-c0,loading_wall=loadw,loading_cpu=loadc,output_wall=outw,output_cpu=outc,
          engine_wall=enginew,engine_cpu=enginec,setup_wall=stats.get('setup_wall',0),setup_cpu=stats.get('setup_cpu',0),validation_wall=stats.get('validation_wall',0),validation_cpu=stats.get('validation_cpu',0),accounting_wall=stats.get('accounting_wall',0),accounting_cpu=stats.get('accounting_cpu',0),
          batch_latency_median_wall=float(np.median(lat)),batch_latency_max_wall=max(lat),batch_latencies_wall=lat,
          persistent_histogram_array_bytes=stats.get('persistent_histogram_array_bytes'),detector_state_accounted_bytes=stats.get('detector_state_accounted_bytes_end'),validation_accounted_bytes=stats.get('validation_accounted_bytes_end'),pending_ks_array_bytes=stats.get('peak_pending_ks_array_bytes'),retained_frame_logical_bytes=frame_bytes,
          output_bytes=output_bytes,output_sha256=digest.hexdigest(),input_reference_sha256=cell['files'][0]['sha256'],code_manifest_sha256=sha256(ROOT/'records/low_compute/2026-10-18/benchmark_execution_manifest.json'),stage_measurements={k:v for k,v in stats.items() if k.endswith(('_wall','_cpu'))})
        row['monitoring_wall']=enginew-row['setup_wall']-row['validation_wall']-row['accounting_wall'];row['monitoring_cpu']=enginec-row['setup_cpu']-row['validation_cpu']-row['accounting_cpu']
        rows.append(row);gc.collect()
    receipt=dict(variant=a.variant,workload=a.workload,repeat=a.repeat,warmup=a.repeat==-1,rows=rows,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       startup_wall=startup_w,startup_cpu=startup_c,execution_wall=time.perf_counter()-start,execution_cpu=time.process_time()-cpu,
       complete_wall=time.perf_counter()-PROCESS_START_W,complete_cpu=time.process_time()-PROCESS_START_C,python=sys.version,config_sha256=sha256(CONFIG))
    record.write_text(json.dumps(receipt,indent=2)+'\n');print(a.workload,a.variant,a.repeat,round(receipt['complete_wall'],3),receipt['process_peak_rss_kib'],flush=True)
if __name__=='__main__':main()

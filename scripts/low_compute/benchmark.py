"""One warm-up + five alternating repeats; fresh processes; never parallel."""
from common import *
import os,subprocess,platform
from datetime import datetime
from zoneinfo import ZoneInfo
import scipy
RECORDS=ROOT/'records/low_compute/2026-10-18'
RAW=ROOT/'results/raw/low_compute/2026-10-18/benchmark'

def main():
 if not (ROOT/'results/raw/low_compute/2026-10-18/equivalence/completion.json').exists():raise ValueError('Equivalence first')
 if RAW.exists():raise FileExistsError('Never overwrite timing evidence')
 paths=[*sorted((ROOT/'src/subpsi').glob('*.py')),*sorted((ROOT/'scripts/low_compute').glob('*.py'))]
 execution=dict(created_local=datetime.now(ZoneInfo('Asia/Karachi')).isoformat(),benchmark_config_sha256=sha256(CONFIG),
   code_sha256={str(p.relative_to(ROOT)):sha256(p) for p in paths},base_commit=configuration()['base_commit'],git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
   python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,platform=platform.platform(),machine=platform.machine(),cpu_model=next((x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name')),None),
   affinity=sorted(os.sched_getaffinity(0)),cpu_count=os.cpu_count(),threads={x:'1' for x in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},
   order='ABCD warm-up; timed r0 ABCD, r1 DCBA, r2 ABCD, r3 DCBA, r4 ABCD',
   process_rss='Linux ru_maxrss KiB; includes imports, input validation, all monitoring, output, retained audit IDs and permutation temporaries.',
   end_to_end='Worker start before imports through fsync outputs and cleanup; excludes subprocess-launch overhead (parent separately records it), original-source archive preparation, calibration/model fitting, equivalence tracing and cProfile.',
   source_preparation='configs/low_compute/benchmark.json prepare_*_seconds; role/lineage validation retained there',
   scope='Timing only; never count technical repeats as new detection trials')
 path=RECORDS/'benchmark_execution_manifest.json'
 if path.exists():raise FileExistsError(path)
 path.write_text(json.dumps(execution,indent=2)+'\n');RAW.mkdir()
 env=os.environ.copy();env.update(execution['threads']);env['PYTHONHASHSEED']='0'
 parent=[]
 for work in ['primary','secondary','prefix5','prefix10']:
  for rep in [-1,0,1,2,3,4]:
   for variant in ('DCBA' if rep%2==1 and rep>=0 else 'ABCD'):
    output=RAW/f'{work}-{rep}-{variant}.json';started=time.perf_counter()
    subprocess.run([sys.executable,str(ROOT/'scripts/low_compute/worker.py'),'--variant',variant,'--workload',work,'--repeat',str(rep),'--out',str(output.relative_to(ROOT))],cwd=ROOT,env=env,check=True)
    parent.append(dict(workload=work,repeat=rep,variant=variant,parent_wall=time.perf_counter()-started,receipt_sha256=sha256(output)))
    pd.DataFrame(parent).to_csv(RAW/'process_wall.csv',index=False)
 (RAW/'completion.json').write_text(json.dumps(dict(finished_local=datetime.now(ZoneInfo('Asia/Karachi')).isoformat(),processes=len(parent),execution_manifest_sha256=sha256(path)),indent=2)+'\n')
if __name__=='__main__':main()

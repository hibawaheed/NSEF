"""Execute the approved, bounded R4 workflow in resumable immutable cells."""
import argparse
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.matched import compare_block
from subpsi.provenance import sha256, source_hashes, environment, write_json, save_snapshot
from subpsi.revision4 import digest, select_targets, run_frozen_targets, wilson_lower
from subpsi.revision4_study import (historical_pool, inventory, support_map, rng,
    seed_integer, weights, source_distances, plans, evaluation_stream, stream_summary)

RAW = ROOT/'results/raw/revision4/main-approved'
PRIVATE = ROOT/'data/raw/revision4/main-approved'
SUMMARY = ROOT/'results/summary/revision4/main-approved'
CONFIG = ROOT/'configs/revision4/approved.json'
SUPPORT = ROOT/'results/summary/revision4/preparation-02/acs_candidate_support.csv'


def stamp(): return datetime.now(timezone.utc).isoformat()


def atomic(path, data):
    temp = path.with_suffix(path.suffix+'.tmp')
    write_json(temp,data); temp.replace(path)


def compressed(path, data):
    temp = path.with_suffix(path.suffix+'.tmp')
    with gzip.GzipFile(filename=str(temp),mode='wb',mtime=0) as handle:
        handle.write(json.dumps(data,allow_nan=False,separators=(',',':')).encode())
    temp.replace(path)


def read_compressed(path):
    with gzip.open(path,'rt') as handle: return json.load(handle)


class Budget:
    def __init__(self, config):
        self.config = config
        self.path = RAW/'budget.json'
        self.before = json.loads(self.path.read_text())['cpu_seconds'] if self.path.exists() else 0.
        self.start = time.process_time(); self.wall = time.perf_counter()

    def check(self):
        seconds = self.before+time.process_time()-self.start
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        atomic(self.path,dict(updated_utc=stamp(),cpu_seconds=seconds,peak_rss_kib=rss))
        if seconds >= self.config['compute']['total_local_cpu_cap_seconds']:
            raise RuntimeError('Approved total CPU cap reached; preserve partial results')
        if rss >= self.config['compute']['working_memory_limit_gib']*1024**2:
            raise RuntimeError('Approved memory budget exceeded')
        if datetime.now(timezone.utc).date().isoformat() >= self.config['results_freeze']:
            raise RuntimeError('Planned freeze date reached')


def setup():
    c = json.loads(CONFIG.read_text())
    if c['status'] != 'APPROVED_FROZEN' or not c['new_calibration_authorized'] or not c['new_evaluation_authorized']:
        raise ValueError('Approved protocol required')
    for path in [RAW,PRIVATE,SUMMARY]: path.mkdir(parents=True,exist_ok=True)
    identity = dict(config_sha256=sha256(CONFIG),code_sha256=source_hashes(ROOT),
                    support_sha256=sha256(SUPPORT))
    frozen = RAW/'identity.json'
    if frozen.exists():
        if json.loads(frozen.read_text()) != identity:
            raise ValueError('Code/config/support changed; refuse to mix cells')
    else:
        write_json(frozen,identity)
        write_json(RAW/'started.json',dict(created_utc=stamp(),git_head=subprocess.check_output(
            ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),environment=environment(),
            source_snapshot_sha256=save_snapshot(ROOT,RAW),
            label='Constructed sampling experiments using genuine whole public records; no natural detection-accuracy claim'))
    return c,identity,Budget(c)


def verified_pool(stage):
    pool,bins,groups,sources = historical_pool(ROOT,stage)
    source_path = RAW/f'{stage}_sources.json'
    if source_path.exists() and json.loads(source_path.read_text()) != sources:
        raise ValueError('Source mismatch on resume')
    if not source_path.exists(): write_json(source_path,sources)
    private_path = PRIVATE/f'{stage}_pool.csv'
    content = pool.to_csv(index=False).encode()
    import hashlib
    if private_path.exists() and sha256(private_path) != hashlib.sha256(content).hexdigest():
        raise ValueError('Private source pool changed')
    if not private_path.exists(): private_path.write_bytes(content)
    return pool,bins,groups


def frozen_inventory(stage,cells):
    path = RAW/f'{stage}_inventory.json'
    if path.exists() and json.loads(path.read_text()) != cells:
        raise ValueError('Ordered cell inventory changed')
    if not path.exists(): write_json(path,cells)


def calibration(stage,c,identity,budget):
    if stage == 'validation':
        targets = json.loads((RAW/'frozen_targets.json').read_text())
        if targets['map_sha256'] != digest(targets['selection']):
            raise ValueError('Frozen map changed')
    else: targets = None
    pool,bins,groups = verified_pool(stage)
    supported = support_map(pd.read_csv(SUPPORT),c)
    cells = inventory(c,groups,stage,targets['selection'] if targets else None)
    frozen_inventory(stage,cells)
    directory = RAW/stage; private = PRIVATE/stage
    directory.mkdir(exist_ok=True); private.mkdir(exist_ok=True)
    groups_by_name = {g.name:g for g in groups}
    records = []; distances = []; distances_seen = set(); started = time.perf_counter()
    threshold = c['monitoring']['alpha_per_statistic_policy_scope']/(c['monitoring']['horizon']*len(groups)*len(bins))
    for cell in cells:
        budget.check(); filename = f"cell-{cell['cell']:04}.json.gz"; path = directory/filename
        subset = pool.loc[groups_by_name[cell['group']].mask(pool)]
        if path.exists():
            result = read_compressed(path)
            if result['identity_sha256'] != digest(identity) or result['cell'] != cell:
                raise ValueError('Saved cell identity changed')
            if result['status']=='assessed' and sha256(private/filename.replace('.json.gz','.npz')) != result['lineage_sha256']:
                raise ValueError('Saved private lineage changed')
        else:
            cpu = time.process_time(); wall = time.perf_counter()
            result = dict(identity_sha256=digest(identity),cell=cell,started_utc=stamp(),rows=[],
                          status='assessed' if supported[cell['group']] else 'historical_calibration_shortage')
            if supported[cell['group']]:
                k = c['calibration'][stage+'_repeats_per_cell']
                references = []; currents = []
                w = weights(subset,c['calibration']['whole_record_multipliers'][cell['scenario']]); w /= w.sum()
                # All column values travel through positional whole-row selection.
                for rep in range(k):
                    budget.check()
                    a = rng(c,stage,cell['cell'],rep,1).choice(len(subset),size=cell['reference_n'],replace=True)
                    b = rng(c,stage,cell['cell'],rep,2).choice(len(subset),size=cell['incoming_n'],replace=True,p=w)
                    references.append(a); currents.append(b)
                    ref,cur = subset.iloc[a],subset.iloc[b]
                    for fi,(feature,binning) in enumerate(bins.items()):
                        stats = compare_block(ref[feature].to_numpy(),cur[feature].to_numpy(),binning,
                            inferential=True,seed=[seed_integer(c,stage,cell['cell'],rep),fi],
                            draws=c['monitoring']['permutations'],cutoff=threshold)
                        result['rows'].append(dict(repeat=rep,feature=feature,
                            unique_reference_sources=len(np.unique(a)),unique_current_sources=len(np.unique(b)),**stats))
                lineage = private/filename.replace('.json.gz','.npz')
                np.savez_compressed(lineage,reference=np.asarray(references,dtype=np.int32),
                                    current=np.asarray(currents,dtype=np.int32),
                                    pool_global_positions=np.flatnonzero(groups_by_name[cell['group']].mask(pool)))
                result['lineage_sha256'] = sha256(lineage)
            result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-wall,
                          finished_utc=stamp(),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            compressed(path,result)
        for method,field in [('PSI','p'),('KS','ks_p')]:
            reps = c['calibration'][stage+'_repeats_per_cell'] if result['status']=='assessed' else 0
            successes = sum(any(r[field] <= threshold for r in result['rows'] if r['repeat']==rep) for rep in range(reps))
            records.append(dict(**cell,method=method,successes=successes,repeats=reps,status=result['status'],
                rate=successes/reps if reps else None,lower=wilson_lower(successes,reps) if reps else None,
                upper=1-wilson_lower(reps-successes,reps) if reps else None,
                cutoff=threshold,raw_file=str(path.relative_to(ROOT)),raw_sha256=sha256(path)))
        if cell['reference_n']==c['calibration']['planning_reference_n'] and (cell['group'],cell['scenario']) not in distances_seen and supported[cell['group']]:
            distances_seen.add((cell['group'],cell['scenario']))
            distances.extend(dict(stage=stage,group=cell['group'],scenario=cell['scenario'],**r)
                             for r in source_distances(subset,bins,c['calibration']['whole_record_multipliers'][cell['scenario']]))
        if (cell['cell']+1)%15==0 or cell==cells[-1]:
            print(f"{stage}: {cell['cell']+1}/{len(cells)} cells, {time.perf_counter()-started:.1f}s",flush=True)
    pd.DataFrame(records).to_csv(SUMMARY/f'{stage}_cells.csv',index=False)
    pd.DataFrame(distances).to_csv(SUMMARY/f'{stage}_source_distances.csv',index=False)
    if stage=='selection':
        calibrated = select_targets([r for r in records if r['status']=='assessed'],
            groups=[g.name for g in groups],grid=c['calibration']['incoming_grid'],
            design_scenarios=c['calibration']['design_alternatives'],
            reference_n=c['calibration']['planning_reference_n'],historically_supported=supported,
            criterion=c['calibration']['criterion'])
        frozen = dict(selection=calibrated,map_sha256=digest(calibrated),frozen_utc=stamp(),
            config_sha256=sha256(CONFIG),selection_table_sha256=sha256(SUMMARY/'selection_cells.csv'),
            identity_sha256=digest(identity),validation_started=False,evaluation_started=False)
        path = RAW/'frozen_targets.json'
        if path.exists():
            previous = json.loads(path.read_text())
            if previous['map_sha256'] != frozen['map_sha256']:
                raise ValueError('Replayed selection changes frozen map')
        else: write_json(path,frozen)
        pd.DataFrame(calibrated['group_targets']).to_csv(SUMMARY/'selected_targets.csv',index=False)
        print('Frozen maps:',json.dumps(calibrated),flush=True)
    write_json(RAW/f'{stage}_complete.json',dict(finished_utc=stamp(),cells=len(cells),
        table_sha256=sha256(SUMMARY/f'{stage}_cells.csv'),identity_sha256=digest(identity)))
    budget.check()


def evaluation(c,identity,budget):
    if not (RAW/'validation_complete.json').exists(): raise ValueError('Validation must finish first')
    frozen = json.loads((RAW/'frozen_targets.json').read_text()); targets = frozen['selection']
    if digest(targets)!=frozen['map_sha256']: raise ValueError('Frozen map changed')
    pool,bins,groups = verified_pool('evaluation'); policies = plans(c,groups,targets)
    e = c['evaluation']; m = c['monitoring']
    cells = [dict(cell=i,condition=cond,repeat=rep) for i,(cond,rep) in enumerate(
        (cond,rep) for cond in e['conditions'] for rep in range(e['null_streams'] if cond=='unchanged' else e['alternative_streams_per_condition']))]
    frozen_inventory('evaluation',cells)
    directory = RAW/'evaluation'; directory.mkdir(exist_ok=True)
    private = PRIVATE/'evaluation'; private.mkdir(exist_ok=True)
    target = next(g.name for g in groups if dict(g.selectors)==e['target'])
    features = list(bins)+list(e['target']); rows=[]; coverage=[]; costs=[]
    for cell in cells:
        budget.check()
        ref,windows = evaluation_stream(pool,c,cell['repeat'],cell['condition'])
        line = pd.concat([ref[['source_id']],*[d[['source_id']] for _,d in windows]])
        lineage = private/f"stream-{cell['cell']:03}.csv.gz"
        content=line.to_csv(index=True,index_label='draw_id').encode()
        if lineage.exists():
            with gzip.open(lineage,'rb') as handle:
                if handle.read()!=content: raise ValueError('Stream lineage changed')
        else:
            with gzip.GzipFile(filename=str(lineage),mode='wb',mtime=0) as handle: handle.write(content)
        for name,plan in policies.items():
            budget.check(); path=directory/f"stream-{cell['cell']:03}-{name}.json.gz"
            if path.exists():
                result=read_compressed(path)
                if result['identity_sha256']!=digest(identity) or result['map_sha256']!=frozen['map_sha256'] or result['cell']!=cell or result['lineage_sha256']!=sha256(lineage):
                    raise ValueError('Saved stream identity changed')
            else:
                cpu=time.process_time(); wall=time.perf_counter()
                result=run_frozen_targets(ref[features],[(t,d[features]) for t,d in windows],bins=bins,
                    groups=groups,plan=plan,alpha=m['alpha_per_statistic_policy_scope'],
                    draws=m['permutations'],seed=seed_integer(c,'evaluation',0,cell['repeat']),inferential=True,channels=m['channels'])
                result.update(identity_sha256=digest(identity),map_sha256=frozen['map_sha256'],cell=cell,
                    policy_name=name,lineage_sha256=sha256(lineage),finished_utc=stamp(),
                    cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-wall,
                    peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
                compressed(path,result)
            extra=dict(**cell,policy=name,raw_file=str(path.relative_to(ROOT)),raw_sha256=sha256(path))
            rows.extend(dict(**extra,**s) for s in stream_summary(result,target,e['onset'],e['end']))
            for group in groups:
                sch=[s for s in result['schedule'] if s['group']==group.name];ready=[s for s in sch if s['eligible']]
                coverage.append(dict(**extra,group=group.name,level=group.level,n_reference=sch[0]['n_reference'],
                    incoming_target=dict(plan.targets)[group.name],planning_reference_n=c['calibration']['planning_reference_n'],
                    ever_assessed=bool(ready),assessments=len(ready),assessment_fraction=len(ready)/e['end'],
                    first_assessment=min(s['look'] for s in ready) if ready else None,
                    never_assessed=not bool(ready),final_unfinished=not sch[-1]['eligible'],
                    pending_records=sch[-1]['n_current'] if not sch[-1]['eligible'] else 0,
                    mean_assessed_block_n=float(np.mean([s['n_current'] for s in ready])) if ready else None,
                    mean_assessed_wait=float(np.mean([s['waiting_looks'] for s in ready])) if ready else None,
                    max_retained_group_records=max(s['n_current'] for s in sch)))
            tests=result['tests']
            costs.append(dict(**extra,cpu_seconds=result['cpu_seconds'],wall_seconds=result['wall_seconds'],
                engine_seconds=result['metadata']['engine_seconds'],peak_process_rss_kib=result['peak_rss_kib'],
                psi_kernel_seconds=sum(t['psi_seconds'] for t in tests),ks_kernel_seconds=sum(t['ks_seconds'] for t in tests),
                psi_max_payload_bytes=max(t['psi_payload_bytes'] or 0 for t in tests),
                ks_max_payload_bytes=max(t['ks_payload_bytes'] or 0 for t in tests),
                ks_warnings=sum(t['ks_status']=='conservative_warning' for t in tests),
                reference_distinct_sources=int(ref.source_id.nunique()),
                current_distinct_sources=int(pd.concat([d for _,d in windows]).source_id.nunique())))
        print(f"evaluation: {cell['cell']+1}/{len(cells)} paired streams (all 5 policies)",flush=True)
    for name,data in [('streams',rows),('coverage',coverage),('costs',costs)]:
        pd.DataFrame(data).to_csv(SUMMARY/f'{name}.csv',index=False)
    write_json(RAW/'evaluation_complete.json',dict(finished_utc=stamp(),streams=len(cells),
        policy_engines=len(cells)*len(policies),identity_sha256=digest(identity),map_sha256=frozen['map_sha256']))
    budget.check()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['selection','validation','evaluation','all']);args=parser.parse_args()
    c,identity,budget=setup()
    try:
        for stage in (['selection','validation','evaluation'] if args.stage=='all' else [args.stage]):
            if stage=='evaluation': evaluation(c,identity,budget)
            else: calibration(stage,c,identity,budget)
    except Exception:
        atomic(RAW/'last_failure.json',dict(utc=stamp(),stage=args.stage,traceback=traceback.format_exc()))
        raise
    finally: budget.check()


if __name__=='__main__': main()

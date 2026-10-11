"""Support/provenance checks and arithmetic on existing counts; no calibration.

Never overwrites an output directory. Private unit-role maps remain under the
already ignored data/raw tree. No evaluation feature distributions are analysed.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.core import NumericBins
from subpsi.correction import AttemptBins, read_table
from subpsi.provenance import sha256, write_json, environment, save_snapshot
from subpsi.realdata import load_datasets, household_pool
from subpsi.revision4 import (representation_audit, augment_saved_outcomes,
                             calibration_role, validate_role_separation)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out',default='results/summary/revision4/preparation')
    p.add_argument('--private-out',default='data/raw/revision4/preparation-lineage')
    args = p.parse_args()
    out = ROOT/args.out; private = ROOT/args.private_out
    if out.exists() or private.exists():
        raise FileExistsError('Choose unused public AND private output directories')
    out.mkdir(parents=True); private.mkdir(parents=True)
    start = time.perf_counter(); stamp = datetime.now(timezone.utc).isoformat()
    write_json(out/'started.json',dict(utc=stamp,purpose='support checks and existing-count reporting only'))
    freeze_path = ROOT/'records/correction/FREEZE.json'
    freeze = json.loads(freeze_path.read_text())
    for name,expected in freeze['evidence_sha256'].items():
        if sha256(ROOT/name) != expected:
            raise ValueError(f'Frozen correction changed: {name}')
    baseline = {}
    names = subprocess.check_output(['git','ls-tree','-r','--name-only','7ddcc02c4bf458b68617bbd5b1f184cbfb82e1c5'],cwd=ROOT,text=True).splitlines()
    for name in names:
        baseline[name] = sha256(ROOT/name)
    write_json(out/'preserved_inventory.json',baseline)
    config = json.loads((ROOT/'configs/revision3/approved.json').read_text())
    datasets,sources = load_datasets(ROOT,config)
    acs,oulad = datasets
    checks = {}
    all_roles = pd.concat([f[['record_id','household_id','role']] for f in acs['frames'].values()])
    checks['acs_original_household_roles'] = validate_role_separation(all_roles,'household_id')
    od = pd.concat(list(oulad['frames'].values()))
    checks['oulad_student_roles'] = validate_role_separation(od[['id_student','role']],'id_student')
    calibration = household_pool(acs['frames'][2015].query("role == 'calibration'"))
    # Only IDs/group memberships are used for new calibration support inspection.
    roles = calibration[['record_id','household_id','SEX','RAC1P']].copy()
    roles['role'] = roles.household_id.map(calibration_role)
    checks['r4_candidate_calibration_roles'] = validate_role_separation(roles,'household_id')
    roles[['record_id','household_id','role']].to_csv(private/'acs_candidate_roles.csv',index=False)
    evaluation = household_pool(acs['reference'])
    overlap = set(roles.household_id).intersection(evaluation.household_id)
    if overlap: raise ValueError('Calibration/evaluation household role overlap')
    checks['calibration_evaluation_household_overlap'] = len(overlap)
    support = []
    for g in acs['groups']:
        row = dict(group=g.name,level=g.level,
                   design_people=int(g.mask(acs['design']).sum()),
                   calibration_people=int(g.mask(acs['frames'][2015].query("role == 'calibration'")).sum()),
                   calibration_households=int(g.mask(roles).sum()),
                   evaluation_source_households=int(g.mask(evaluation).sum()))
        for stage in ['selection','validation']:
            frame = roles.loc[roles.role.eq(stage)]
            row[stage+'_households'] = int(g.mask(frame).sum())
            # Proposed age>=60 stratum support ONLY; no distances, p-values or power.
            subgroup = calibration.loc[frame.index[g.mask(frame)]]
            row[stage+'_age_ge60'] = int(subgroup.AGEP.ge(60).sum())
            row[stage+'_age_lt60'] = int(subgroup.AGEP.lt(60).sum())
        support.append(row)
    pd.DataFrame(support).to_csv(out/'acs_candidate_support.csv',index=False)
    audits = []
    for ds in datasets:
        for feature in ds['features']:
            for rule,b in [('v3_quantile',NumericBins.fit(ds['design'][feature],6))] + (
                [('corrected_counts',AttemptBins())] if feature=='num_of_prev_attempts' else []):
                audits.append(dict(dataset=ds['name'],feature=feature,rule=rule,
                                   **representation_audit(ds['design'][feature],b)))
    write_json(out/'representation_audit.json',audits)
    flat = [{k:(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in r.items()} for r in audits]
    pd.DataFrame(flat).to_csv(out/'representation_audit.csv',index=False)
    source_outcomes = ROOT/'results/raw/correction/oulad/outcomes.csv'
    augment_saved_outcomes(read_table(source_outcomes)).to_csv(out/'oulad_outcomes_extended.csv',index=False)
    beforeafter = ROOT/'results/raw/correction/oulad/old_vs_corrected.csv'
    read_table(beforeafter).to_csv(out/'oulad_before_after.csv',index=False)
    sources[str(source_outcomes.relative_to(ROOT))] = sha256(source_outcomes)
    sources[str(beforeafter.relative_to(ROOT))] = sha256(beforeafter)
    write_json(out/'role_checks.json',checks)
    manifest = dict(started_utc=stamp,finished_utc=datetime.now(timezone.utc).isoformat(),
                    purpose='PREPARATION ONLY: support counts, historical representation, saved-outcome arithmetic',
                    main_evaluation_run=False,calibration_run=False,
                    git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    git_status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(),
                    source_snapshot_sha256=save_snapshot(ROOT,out),environment=environment(),
                    source_hashes=sources,verified_correction_freeze_sha256=sha256(freeze_path),
                    verified_frozen_files=len(freeze['evidence_sha256']),preserved_base_files=len(baseline),
                    private_lineage_sha256=sha256(private/'acs_candidate_roles.csv'),
                    wall_seconds=time.perf_counter()-start,peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    files={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
    write_json(out/'manifest.json',manifest)
    print(json.dumps({k:manifest[k] for k in ['purpose','verified_frozen_files','preserved_base_files','wall_seconds','peak_process_rss_kib']}))
    print(pd.DataFrame(support)[['group','selection_households','validation_households']].to_string(index=False))


if __name__ == '__main__': main()

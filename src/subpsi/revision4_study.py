"""Approved R4 stage-isolated sampling and reporting helpers.

Sampling changes whole-record probabilities, never recorded fields. Delivery
indices describe constructed experiments, not invented survey chronology.
"""
import hashlib
import json
import zipfile

import numpy as np
import pandas as pd

from .core import NumericBins
from .matched import declared_groups
from .provenance import sha256
from .realdata import acs_role, household_pool, validate_schema
from .revision4 import (CollectionPlan, calibration_role, digest,
                        validate_draw_lineage, draw_whole_records)


def historical_pool(root, stage):
    """Read only the requested survey year, with original receipt/role checks."""
    if stage not in {'selection', 'validation', 'evaluation'}:
        raise ValueError('Unknown stage')
    year = 2016 if stage == 'evaluation' else 2015
    cfg_path = root/'configs/revision3/approved.json'
    cfg = json.loads(cfg_path.read_text())['acs']
    path = root/f'data/raw/revision3/acs/{year}/csv_pma.zip'
    receipt = json.loads(path.with_suffix('.receipt.json').read_text())
    if sha256(path) != receipt['sha256']:
        raise ValueError('Source archive changed')
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.endswith('.csv'))
        with z.open(member) as handle:
            d = pd.read_csv(handle, usecols=['SERIALNO','SPORDER','ST','AGEP','SCHL','SEX','RAC1P','ESR'],
                            dtype={'SERIALNO':str})
    if not d.ST.eq(25).all() or d.duplicated(['SERIALNO','SPORDER']).any():
        raise ValueError('Unexpected state or duplicate person')
    d = d.loc[d.AGEP.between(*cfg['age_inclusive'])].copy()
    if not d.ESR.isin(range(1,7)).all():
        raise ValueError('Unknown outcome')
    d['record_id'] = [f'{year}:{s}:{o}' for s,o in zip(d.SERIALNO,d.SPORDER)]
    d['household_id'] = [f'{year}:{s}' for s in d.SERIALNO]
    d.index = d.record_id
    d['role'] = [acs_role(k,year) for k in d.household_id]
    old = root/f'data/raw/revision3/lineage/acs_{year}_proposed_roles.csv'
    if hashlib.sha256(d[['record_id','household_id','role']].to_csv(index=False).encode()).hexdigest() != sha256(old):
        raise ValueError('Original roles changed')
    d['label'] = d.ESR.eq(1).astype(int)
    validate_schema(d,cfg['features'],cfg['group_levels'])
    pool = household_pool(d.loc[d.role.eq('reference' if year == 2016 else 'calibration')])
    if stage != 'evaluation':
        pool = pool.loc[pool.household_id.map(calibration_role).eq(stage)].copy()
    if not pool.household_id.is_unique:
        raise ValueError('Multiple representatives per household')
    saved_path = root/'results/raw/revision3/main-approved/models_and_bins.json'
    saved = json.loads(saved_path.read_text())['ACS_MA']['bins']
    bins = {f:NumericBins(tuple(float(x) for x in b['edges'])) for f,b in saved.items()}
    sources = {str(p.relative_to(root)):sha256(p) for p in [path,old,cfg_path,saved_path]}
    return pool,bins,declared_groups(cfg['group_levels']),sources


def rng(config, stage, cell, repeat, channel):
    return np.random.default_rng(np.random.SeedSequence([
        config['randomization']['base_seed'],config['randomization']['namespaces'][stage],
        cell,repeat,channel]))


def seed_integer(config, stage, cell, repeat, channel=4):
    return int(rng(config,stage,cell,repeat,channel).integers(0,2**32,dtype=np.uint64))


def weights(pool, multiplier):
    if not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError('Positive fixed multiplier required')
    return np.where(pool.AGEP.ge(60),float(multiplier),1.)


def source_distances(pool, bins, multiplier):
    """Exact empirical-source distances, not sample estimates or power claims.

    PSI uses unsmoothed positive-mass bins; joint-zero bins contribute zero.
    KS is the maximum difference between the weighted empirical CDFs.
    """
    p = np.ones(len(pool))/len(pool); q = weights(pool,multiplier); q /= q.sum()
    out = []
    for feature,b in bins.items():
        enc = b.encode(pool[feature]); a = np.bincount(enc,weights=p,minlength=b.size)
        c = np.bincount(enc,weights=q,minlength=b.size); mask = a > 0
        psi = float(np.sum((c[mask]-a[mask])*np.log(c[mask]/a[mask])))
        values = pool[feature].to_numpy(float)
        if not np.isfinite(values).all():
            raise ValueError('This source-distance diagnostic requires finite features')
        _, inverse = np.unique(values,return_inverse=True)
        ecdf = np.cumsum(np.bincount(inverse,weights=p-q))
        out.append(dict(feature=feature,source_psi=psi,source_ks=float(np.max(np.abs(ecdf))),
                        source_households=len(pool),age_ge60=int(pool.AGEP.ge(60).sum())))
    return out


def support_map(table, config):
    cal = config['calibration']; out = {}
    for row in table.to_dict('records'):
        out[row['group']] = all(row[s+'_households'] >= cal['minimum_unique_households_each_stage']
            and min(row[s+'_age_ge60'],row[s+'_age_lt60']) >= cal['minimum_each_age_stratum_each_stage']
            for s in ['selection','validation'])
    return out


def inventory(config, groups, stage, targets=None):
    """Ordered cells fixed without querying feature-based results.

    Include all declared unsupported groups. Selection order is group, reference
    size, incoming size, condition. Validation sizes depend only on frozen maps.
    """
    if stage not in {'selection','validation'}:
        raise ValueError('Calibration stage required')
    cal = config['calibration']; rows = []
    for group in groups:
        references = cal['reference_grid'] if stage == 'selection' else [cal['planning_reference_n']]
        if stage == 'selection':
            sizes = cal['incoming_grid']
        else:
            if targets is None:
                raise ValueError('Frozen targets required before validation inventory')
            keyed = {r['group']:r['target'] for r in targets['group_targets']}
            sizes = sorted({keyed[group.name],targets['global_target']})
        for reference in references:
            for size in sizes:
                for condition in cal[stage+'_conditions']:
                    rows.append(dict(cell=len(rows),stage=stage,group=group.name,level=group.level,
                                     reference_n=reference,incoming_n=size,scenario=condition))
    return rows


def plans(config, groups, targets):
    m = config['monitoring']; keyed = {r['group']:r['target'] for r in targets['group_targets']}
    if set(keyed) != {g.name for g in groups}:
        raise ValueError('Incomplete map')
    out = {}
    for name in m['policies']:
        count = {'ordinary_50':50,'fixed_100':100,'fixed_400':400,
                 'global_calibrated':targets['global_target']}.get(name)
        pairs = tuple((g.name,keyed[g.name] if name == 'group_calibrated' else count) for g in groups)
        out[name] = CollectionPlan(pairs,m['min_reference'],m['horizon'],
                                   'batch' if name == 'ordinary_50' else 'accumulate')
    return out


def evaluation_stream(pool, config, repeat, condition):
    """Identical reference/base draws across conditions; whole target replacements.

    Reference and base channels use cell=0 for pairing. Replacement uses the
    fixed condition ordinal. No reference/current draw ID overlap; repeated
    source records are allowed and privately auditable as resampling.
    """
    e = config['evaluation']; conditions = e['conditions']
    if condition not in conditions:
        raise ValueError('Unknown prespecified condition')
    ref = draw_whole_records(pool,e['reference_draw_n'],rng(config,'evaluation',0,repeat,1),prefix='reference')
    validate_draw_lineage(ref,pool)
    target = np.ones(len(pool),bool)
    for k,v in e['target'].items(): target &= pool[k].eq(v).to_numpy()
    replacements = pool.loc[target]
    if replacements.empty:
        raise ValueError('Empty declared target pool')
    base_rng = rng(config,'evaluation',0,repeat,2)
    change_rng = rng(config,'evaluation',conditions.index(condition),repeat,3)
    w = weights(replacements,config['calibration']['whole_record_multipliers'][condition])
    windows = []
    for look in range(1,e['end']+1):
        current = draw_whole_records(pool,e['batch_size'],base_rng,prefix=f'delivery:{look}')
        selected = np.ones(len(current),bool)
        for k,v in e['target'].items(): selected &= current[k].eq(v).to_numpy()
        if condition != 'unchanged' and look >= e['onset'] and selected.any():
            changed = draw_whole_records(replacements,int(selected.sum()),change_rng,prefix='replacement',weights=w)
            current.loc[selected,:] = changed.to_numpy()
        validate_draw_lineage(current,pool)
        windows.append((look,current))
    return ref,windows


def stream_summary(result, target, onset=6, horizon=20):
    """Misses receive full post-onset restricted delay; not dropped from means."""
    rows = []
    for scope in ['aggregate','single','intersection']:
        for method in ['PSI','KS']:
            ds = [r for r in result['decisions'] if r['scope']==scope and r['method']==method]
            hits = [r['look'] for r in ds if r['look'] >= onset and any(h[0]==target for h in r['hits'])]
            schedules = [s for s in result['schedule'] if s['group']==target]
            ready = [s for s in schedules if s['eligible']]
            rows.append(dict(scope=scope,method=method,whole_stream_alert=any(r['alert'] for r in ds),
                pre_onset_alert=any(r['alert'] for r in ds if r['look']<onset),
                exact_target_detection=bool(hits),first_detection=min(hits) if hits else None,
                restricted_delay=min(hits)-onset if hits else horizon-onset+1,
                ever_assessed=bool(ready),first_assessment=min(s['look'] for s in ready) if ready else None,
                assessment_fraction=len(ready)/horizon))
    return rows

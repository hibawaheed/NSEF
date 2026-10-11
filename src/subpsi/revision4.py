"""Revision 4 preparation. No new real-data calibration is run by this module.

The earlier frozen engines remain unchanged. Selection accepts historical summary
counts only; collection accepts metadata only; one block feeds both statistics.
"""
from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from statistics import NormalDist
import time

import numpy as np
import pandas as pd

from .core import NumericBins, adjust_pvalues, validate_resolution
from .matched import Block, compare_block


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def integer(value, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(f'Integer >= {minimum} required')
    return int(value)


def representation_audit(design, binning):
    """Historical design only. Effective bins = inverse Simpson concentration.

    Missingness is counted separately; collapse refers to observed numeric values.
    A constant feature is reported, not diagnosed as a binning error.
    """
    a = np.asarray(design, float)
    if a.ndim != 1 or not len(a):
        raise ValueError('Nonempty historical design vector required')
    counts = binning.counts(a)
    observed = a[~np.isnan(a)]
    distinct = np.unique(observed)
    numeric = counts[:-1]
    occupied = int(np.count_nonzero(numeric))
    p = numeric / len(observed) if len(observed) else None
    collapse = len(distinct) > 1 and occupied == 1
    status = ('no_observed_values' if not len(distinct) else 'constant_design'
              if len(distinct) == 1 else 'collapsed_nonconstant' if collapse else 'represented')
    return dict(n_design=len(a), n_observed=len(observed), n_missing=int(counts[-1]),
                distinct_historical_values=distinct.tolist(), n_distinct_observed=len(distinct),
                configured_numeric_bins=binning.size-1, occupied_bins=int(np.count_nonzero(counts)),
                occupied_numeric_bins=occupied, counts=counts.tolist(),
                effective_bin_count=float(1 / np.sum(p*p)) if p is not None else None,
                effective_bin_definition='1 / sum(observed-bin proportion squared); missing excluded',
                largest_bin_proportion=float(p.max()) if p is not None else None,
                nonconstant_collapse=collapse, status=status, bins=binning.metadata())


def outcome_metrics(tp, positives, fp, negatives, *, minimum=20):
    """Descriptive reporting from saved confusion counts; no fitting or selection.

    Balanced accuracy weights the two class-specific correct rates equally. It
    has two denominators, not one pooled denominator. Reporting requires both
    class denominators >= minimum; raw counts remain available when suppressed.
    """
    tp, positives, fp, negatives = [integer(x) for x in (tp, positives, fp, negatives)]
    integer(minimum, 1)
    if tp > positives or fp > negatives:
        raise ValueError('Numerator exceeds class denominator')
    total, correct = positives+negatives, tp+negatives-fp
    specs = [('Accuracy', correct, total, total >= minimum, correct/total if total else None),
             ('TPR', tp, positives, positives >= minimum, tp/positives if positives else None),
             ('FPR', fp, negatives, negatives >= minimum, fp/negatives if negatives else None),
             ('Balanced accuracy', None, None, min(positives, negatives) >= minimum,
              .5*(tp/positives + 1-fp/negatives) if positives and negatives else None)]
    return [dict(metric=m, numerator=n, denominator=d, positives=positives, negatives=negatives,
                 tp=tp, fp=fp, tn=negatives-fp, fn=positives-tp, n=total,
                 value=v if ok else None, mathematically_defined=v is not None,
                 status='assessed' if ok else 'insufficient_denominator') for m,n,d,ok,v in specs]


def augment_saved_outcomes(table, *, minimum=20):
    """Re-express old audit counts, including complements and unsupported groups."""
    rows = []
    for (model, stamp, group, level), frame in table.groupby(['model','time','group','level'], sort=False):
        if len(frame) != 3 or set(frame.metric) != {'TPR','FPR','Accuracy'}:
            raise ValueError('One saved TPR/FPR/Accuracy row per audit group required')
        keyed = frame.set_index('metric')
        for period in ['baseline', 'current']:
            for subset, prefix in [('group',''), ('complement','complement_')]:
                key = f'{period}_{prefix}'
                def saved(metric, field):
                    v = keyed.loc[metric, key+field]
                    if not np.isfinite(v) or int(v) != v:
                        raise ValueError('Saved audit counts must be finite integers')
                    return int(v)
                tp, pos = saved('TPR','numerator'), saved('TPR','denominator')
                fp, neg = saved('FPR','numerator'), saved('FPR','denominator')
                if (saved('Accuracy','numerator'), saved('Accuracy','denominator')) != (tp+neg-fp,pos+neg):
                    raise ValueError('Inconsistent saved confusion counts')
                for row in outcome_metrics(tp,pos,fp,neg,minimum=minimum):
                    rows.append(dict(model=model, time=stamp, group=group, level=level,
                                     period=period, subset=subset, **row))
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class CollectionPlan:
    targets: tuple
    min_reference: int
    horizon: int
    policy: str = 'accumulate'

    def __post_init__(self):
        # Copy nested values into immutable tuples even when constructed from lists.
        object.__setattr__(self, 'targets', tuple(tuple(x) for x in self.targets))
        integer(self.min_reference, 1); integer(self.horizon, 1)
        if self.policy not in {'accumulate','batch'} or not self.targets:
            raise ValueError('Nonempty declared policy required')
        names = [g for g,_ in self.targets]
        if any(not isinstance(g,str) or not g for g in names) or len(set(names)) != len(names):
            raise ValueError('Unique named groups required')
        for _, n in self.targets:
            integer(n, 1)
        object.__setattr__(self, 'targets', tuple((g,int(n)) for g,n in self.targets))
        object.__setattr__(self, 'min_reference', int(self.min_reference))
        object.__setattr__(self, 'horizon', int(self.horizon))

    def metadata(self):
        return dict(targets=dict(self.targets), min_reference=self.min_reference,
                    horizon=self.horizon, policy=self.policy)

    @property
    def sha256(self):
        return digest(self.metadata())


class FrozenTargetScheduler:
    """Count-only whole-batch collector, with a separate fixed reference gate.

    No score, p-value, outcome, feature array or reset-on-alert API is accepted.
    Completed blocks reset together for all features/statistics. Every declared
    delivery consumes a look, including empty or unsupported deliveries.
    """
    def __init__(self, reference_counts, plan):
        if set(reference_counts) != set(dict(plan.targets)):
            raise ValueError('Reference counts must include every declared group')
        self.plan = plan
        self.reference_counts = {g:integer(reference_counts[g]) for g,_ in plan.targets}
        self.buffers = {g:[] for g,_ in plan.targets}
        self.opened = {g:None for g,_ in plan.targets}
        self.seen, self.look, self.last_time = set(), 0, None

    def advance(self, timestamp, memberships):
        if self.look >= self.plan.horizon:
            raise ValueError('Declared horizon exhausted; cannot reset alpha')
        integer(timestamp)
        if self.last_time is not None and timestamp <= self.last_time:
            raise ValueError('Strictly increasing integer time required')
        if set(memberships) != set(self.buffers):
            raise ValueError('All declared groups required, including absent groups')
        members = {g:tuple(ids) for g,ids in memberships.items()}
        incoming = set()
        for ids in members.values():
            if any(not isinstance(i,str) for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('Unique string draw IDs required within a group')
            incoming.update(ids)
        if self.seen.intersection(incoming):
            raise ValueError('Draw IDs repeated across delivery batches')
        # All validation precedes mutation; overlapping groups may share a draw.
        self.look += 1; self.last_time = int(timestamp); self.seen.update(incoming)
        blocks = []
        for group, target in self.plan.targets:
            if self.opened[group] is None:
                self.opened[group] = (self.look, int(timestamp))
            pool = self.buffers[group]
            pool.extend((int(timestamp), i) for i in members[group])
            ready = self.reference_counts[group] >= self.plan.min_reference and len(pool) >= target
            blocks.append(Block(group,self.look,int(timestamp),tuple(i for _,i in pool),ready,
                                self.reference_counts[group],*self.opened[group],
                                pool[0][0] if pool else None,pool[-1][0] if pool else None,0,0))
            if ready or self.plan.policy == 'batch':
                self.buffers[group] = []; self.opened[group] = None
        return blocks


def run_frozen_targets(reference, windows, *, bins, groups, plan, alpha=.05,
                       draws=23999, seed=0, inferential=False, channels=1):
    """Both statistics share exact inputs; primary and secondary scopes separate.

    This offline research runner retains input frames and ID bookkeeping. Kernel
    payload measures do not describe total memory. Peak RSS must be profiled by
    the caller. No training/outcome labels enter the collector or statistical API.
    """
    start = time.perf_counter()
    if len(windows) != plan.horizon or tuple(g.name for g in groups) != tuple(g for g,_ in plan.targets):
        raise ValueError('Plan group order and horizon must match declared inputs')
    if not bins or any(not isinstance(b,NumericBins) for b in bins.values()):
        raise ValueError('Matched numeric/ordered features required')
    integer(draws, 1); integer(channels, 1)
    if not 0 < alpha < 1:
        raise ValueError('Invalid alpha')
    frames = [reference, *(f for _,f in windows)]
    for frame in frames:
        if not frame.index.is_unique or any(not isinstance(i,str) for i in frame.index):
            raise ValueError('Unique string draw IDs required')
        for f, binning in bins.items():
            binning.encode(frame[f])
    all_current = pd.concat(frames[1:])
    if not all_current.index.is_unique or set(reference.index).intersection(all_current.index):
        raise ValueError('Draw IDs cross reference/current or batch boundaries')
    family = len(groups)*len(bins); cutoff = alpha/(plan.horizon*channels)
    if inferential:
        validate_resolution(draws, family, cutoff)
    ref_ids = {g.name:tuple(reference.index[g.mask(reference)]) for g in groups}
    scheduler = FrozenTargetScheduler({g:len(ids) for g,ids in ref_ids.items()},plan)
    rows, decisions, schedule = [], [], []
    targets = dict(plan.targets)
    for w, (timestamp, frame) in enumerate(windows,1):
        tick = time.perf_counter()
        blocks = scheduler.advance(timestamp,{g.name:tuple(frame.index[g.mask(frame)]) for g in groups})
        collection_seconds = time.perf_counter()-tick
        look_rows = []
        for gi, (group, block) in enumerate(zip(groups,blocks)):
            meta = dict(**block.metadata(), incoming_target=targets[group.name],
                        min_reference=plan.min_reference, plan_sha256=plan.sha256,
                        historical_shortage=block.reference_n < plan.min_reference,
                        collecting_current=len(block.ids) < targets[group.name])
            schedule.append(dict(**meta, collection_seconds_all_groups=collection_seconds))
            for fi,(feature,binning) in enumerate(bins.items()):
                row = dict(**meta, feature=feature,level=group.level,policy=plan.policy,
                           status='assessed' if block.ready else 'insufficient_support',
                           psi=None,p=1. if inferential else None,ks_p=1. if inferential else None,
                           ks_d=None,draws=0,censored=False,ks_status='insufficient_support',
                           psi_seconds=0.,ks_seconds=0.,histogram_setup_seconds=0.,
                           psi_payload_bytes=None,ks_payload_bytes=None)
                if block.ready:
                    row.update(compare_block(reference.loc[list(ref_ids[group.name]),feature].to_numpy(),
                                             all_current.loc[list(block.ids),feature].to_numpy(),binning,
                                             inferential=inferential,seed=[seed,w,gi,fi,0 if plan.policy=='batch' or block.opened_look==w else 1],
                                             draws=draws,cutoff=cutoff))
                look_rows.append(row)
        for scope,levels in [('aggregate',{'aggregate'}),('single',{'aggregate','single'}),
                             ('intersection',{'aggregate','single','intersection'})]:
            selected = [r for r in look_rows if r['level'] in levels]
            for method,field in [('PSI','p'),('KS','ks_p')]:
                adjusted = adjust_pvalues([r[field] for r in selected]) if inferential else [None]*len(selected)
                hits = [(r['group'],r['feature']) for r,p in zip(selected,adjusted)
                        if inferential and r['eligible'] and p <= cutoff]
                decisions.append(dict(look=w,time=int(timestamp),scope=scope,method=method,
                                      policy=plan.policy,plan_sha256=plan.sha256,
                                      alert=bool(hits) if inferential else None,hits=hits,
                                      family_size=len(selected),cutoff=cutoff if inferential else None,
                                      assessed=sum(r['eligible'] for r in selected),
                                      adjusted_pvalues=list(adjusted)))
        rows.extend(look_rows)
    return dict(tests=rows,decisions=decisions,schedule=schedule,
                metadata=dict(plan=plan.metadata(),plan_sha256=plan.sha256,alpha_per_method=alpha/channels,
                              family_size=family,cutoff=cutoff if inferential else None,draws=draws,seed=seed,
                              engine_seconds=time.perf_counter()-start,inferential=inferential,
                              reference_frame_bytes=int(reference.memory_usage(index=True,deep=True).sum()),
                              current_frame_bytes=int(all_current.memory_usage(index=True,deep=True).sum()),
                              memory_note='Frames plus buffers, seen-ID set and temporary arrays; measure full-process RSS separately.'))


def wilson_lower(successes, repeats, confidence=.95):
    """Lower endpoint of a two-sided, pointwise Wilson interval, not simultaneous."""
    k,n = integer(successes), integer(repeats,1)
    if k > n or not 0 < confidence < 1:
        raise ValueError('Invalid binomial counts or confidence')
    z = NormalDist().inv_cdf((1+confidence)/2); p = k/n
    return (p+z*z/(2*n)-z*sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)


def select_targets(cells, *, groups, grid, design_scenarios, reference_n,
                   historically_supported, criterion=.8, confidence=.95):
    """Pure lookup from selection-stage summaries; validation cannot retune it.

    Success means ANY monitored feature in the exact target passes the declared
    conservative family/horizon cutoff. Both statistics use the SAME draws.
    Every grid/scenario/stat cell is required for supported groups. Stress/null
    rows are ignored for selection. A separate stage must check the frozen map.
    Global calibration uses the exact same cells and a worst-supported-group
    rule; no extra calibration records or favorable group exclusions are allowed.
    """
    names, sizes, scenarios = tuple(groups), tuple(grid), tuple(design_scenarios)
    integer(reference_n,1)
    if (not names or len(set(names)) != len(names) or not sizes or
        tuple(sorted(set(sizes))) != sizes or not scenarios or len(set(scenarios)) != len(scenarios) or
        set(historically_supported) != set(names) or not 0 < criterion < 1):
        raise ValueError('Explicit unique groups, increasing grid, scenarios and support map required')
    for n in sizes: integer(n,1)
    if any(not isinstance(v,(bool,np.bool_)) for v in historically_supported.values()):
        raise ValueError('Historical support flags must be boolean')
    keyed = {}
    for row in cells:
        if row.get('stage') != 'selection':
            raise ValueError('Only selection-stage cells may choose targets')
        if row['scenario'] not in scenarios or row['reference_n'] != reference_n:
            continue
        key = (row['group'],row['incoming_n'],row['scenario'],row['method'])
        if key in keyed:
            raise ValueError('Duplicate calibration cell')
        if key[0] not in names or key[1] not in sizes or key[3] not in {'PSI','KS'}:
            raise ValueError('Undeclared design cell')
        keyed[key] = wilson_lower(row['successes'],row['repeats'],confidence)
    support = [g for g in names if historically_supported[g]]
    bounds, records = {}, []
    for g in names:
        eligible = historically_supported[g]
        for n in sizes:
            if eligible:
                keys = [(g,n,s,m) for s in scenarios for m in ['PSI','KS']]
                if any(k not in keyed for k in keys):
                    raise ValueError('Missing design cell for supported group')
                bounds[g,n] = min(keyed[k] for k in keys)
        passed = [n for n in sizes if eligible and bounds[g,n] >= criterion]
        records.append(dict(group=g,target=min(passed) if passed else max(sizes),
                            status='criterion_met_selection_only' if passed else
                            'target_not_met_within_grid' if eligible else 'historical_calibration_shortage'))
    global_pass = [n for n in sizes if support and all(bounds[g,n] >= criterion for g in support)]
    return dict(group_targets=records,global_target=min(global_pass) if global_pass else max(sizes),
                global_status='criterion_met_selection_only' if global_pass else 'criterion_unmet_fallback',
                confidence=confidence,criterion=criterion,reference_n=reference_n,
                selection_input_sha256=digest(sorted(cells,key=lambda r:json.dumps(r,sort_keys=True))),
                limitations='Pointwise selected estimates are optimistic; independent validation required. No stream-power guarantee.')


def calibration_role(household_id):
    """Proposed R4 support split. Hashing is allowed now; calibration is not."""
    code = hashlib.sha256(f'r4-calibration-20261011|{household_id}'.encode()).digest()
    return 'selection' if int.from_bytes(code[:8],'big') < 2**63 else 'validation'


def validate_role_separation(lineage, unit_column, role_column='role'):
    if lineage.empty or lineage[[unit_column,role_column]].isna().any().any():
        raise ValueError('Nonempty complete private lineage required')
    if (lineage.groupby(unit_column)[role_column].nunique() > 1).any():
        raise ValueError('Source unit appears in conflicting roles')
    return dict(units=int(lineage[unit_column].nunique()),rows=len(lineage),conflicts=0)


def draw_whole_records(pool, n, rng, *, prefix, weights=None):
    """Conditional iid draws with replacement, NOT n new source people.

    Source units must already satisfy the household/student rule. All columns,
    including outcomes and group codes, travel together. Private source/draw IDs
    permit exact auditing; callers must never export them into public figures.
    """
    integer(n,1)
    if pool.empty or not pool.index.is_unique or 'source_id' in pool:
        raise ValueError('Unique nonempty source pool without reserved source_id column required')
    if not isinstance(prefix,str) or not prefix:
        raise ValueError('Explicit draw namespace required')
    probs = np.ones(len(pool)) if weights is None else np.asarray(weights,float)
    if probs.shape != (len(pool),) or not np.isfinite(probs).all() or np.any(probs <= 0):
        raise ValueError('Strictly positive finite whole-record weights required')
    chosen = rng.choice(len(pool),size=n,replace=True,p=probs/probs.sum())
    result = pool.iloc[chosen].copy()
    result['source_id'] = result.index.to_numpy()
    result.index = [f'{prefix}:{i}' for i in range(n)]
    return result


def validate_draw_lineage(draw, pool):
    """Check every released field against its source, with repeats made explicit."""
    if not draw.index.is_unique or 'source_id' not in draw or not pool.index.is_unique:
        raise ValueError('Unique draw IDs, unique pool IDs and private source_id required')
    if not draw.source_id.isin(pool.index).all() or set(draw.columns) != set(pool.columns)|{'source_id'}:
        raise ValueError('Unknown source or altered column schema')
    expected = pool.loc[list(draw.source_id)].reset_index(drop=True)
    actual = draw[list(pool.columns)].reset_index(drop=True)
    if not actual.equals(expected):
        raise ValueError('A drawn feature, group or outcome differs from its source')
    return dict(draws=len(draw),distinct_source_units=int(draw.source_id.nunique()),
                repeated_source_draws=int(len(draw)-draw.source_id.nunique()))

"""Count-reuse SubPSI beside the unchanged research engine.

Integer counts are accumulated before the original smoothing/count_test call.
The original ID-auditing scheduler remains a separately measured validation
layer: exact ID state and pending ID tuples are NOT constant-memory. Feature
arrays are discarded per batch for PSI; KS retains the pending raw values it
needs. No statistical pre-screen, new bins, or seed remapping is introduced.
"""
import sys,time,warnings
from contextlib import contextmanager
import numpy as np
from .core import NumericBins,psi_counts,adjust_pvalues,validate_resolution
from .revision import count_test,ks_missing
from .matched import ks_score
from .revision4 import FrozenTargetScheduler,integer


class Costs:
    def __init__(self):self.values={}
    @contextmanager
    def section(self,name):
        w,c=time.perf_counter(),time.process_time()
        try:yield
        finally:
            self.values[name+'_wall']=self.values.get(name+'_wall',0.)+time.perf_counter()-w
            self.values[name+'_cpu']=self.values.get(name+'_cpu',0.)+time.process_time()-c


def deep_bytes(value,seen=None):
    """Python/owned-array accounting, not RSS or allocator/temporary accounting."""
    if seen is None:seen=set()
    if id(value) in seen:return 0
    seen.add(id(value));n=sys.getsizeof(value)
    if isinstance(value,dict):n+=sum(deep_bytes(k,seen)+deep_bytes(v,seen) for k,v in value.items())
    elif isinstance(value,(list,tuple,set)):n+=sum(deep_bytes(v,seen) for v in value)
    elif hasattr(value,'__dict__'):n+=deep_bytes(value.__dict__,seen)
    return n


def group_masks(frame,groups):
    """Reuse each declared selector, including pandas missing-value semantics."""
    selectors={}
    for group in groups:
        for key in group.selectors:
            if key not in selectors:
                col,value=key
                selectors[key]=frame[col].isna().to_numpy() if value is None else (frame[col]==value).fillna(False).to_numpy(dtype=bool)
    result=[]
    for group in groups:
        mask=np.ones(len(frame),bool)
        for key in group.selectors:mask &= selectors[key]
        result.append(mask)
    return result


def _validate_ids(frame,seen):
    ids=list(frame.index)
    if any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Unique string draw IDs required')
    if seen.intersection(ids):raise ValueError('Draw IDs cross reference/current or batch boundaries')
    return ids


def decisions(rows,plan,look,timestamp,method,cutoff,inferential):
    field='p' if method=='PSI' else 'ks_p';out=[]
    for scope,levels in [('aggregate',{'aggregate'}),('single',{'aggregate','single'}),('intersection',{'aggregate','single','intersection'})]:
        selected=[r for r in rows if r['level'] in levels]
        adjusted=adjust_pvalues([r[field] for r in selected]) if inferential else [None]*len(selected)
        hits=[(r['group'],r['feature']) for r,p in zip(selected,adjusted) if inferential and r['eligible'] and p<=cutoff]
        out.append(dict(look=look,time=int(timestamp),scope=scope,method=method,policy=plan.policy,
            plan_sha256=plan.sha256,alert=bool(hits) if inferential else None,hits=hits,
            family_size=len(selected),cutoff=cutoff if inferential else None,
            assessed=sum(r['eligible'] for r in selected),adjusted_pvalues=list(adjusted)))
    return out


def iter_monitor(reference,windows,*,bins,groups,plan,alpha=.05,draws=23999,seed=0,
                 inferential=False,channels=1,method='PSI',trace=None,stats=None,allow_prefix=False,histogram_observer=None):
    """Yield one completed look at a time. Input/output storage belongs to caller.

    Exact validation of each arrival precedes that look's state mutation. A bad
    future arrival raises; previously yielded results are a valid prefix only,
    not a successfully completed declared run. Callers must mark completion only
    after exhausting this iterator. Prefix mode is for cost scaling, retains H.
    """
    if stats is None:stats={}
    costs=Costs();start=time.perf_counter();cpu=time.process_time()
    if tuple(g.name for g in groups)!=tuple(g for g,_ in plan.targets):raise ValueError('Plan group order must match')
    if not bins or any(not isinstance(b,NumericBins) for b in bins.values()):raise ValueError('Numeric/ordered bins required')
    if method not in {'PSI','KS'}:raise ValueError('One method required')
    integer(draws,1);integer(channels,1)
    if not 0<alpha<1:raise ValueError('Invalid alpha')
    cutoff=alpha/(plan.horizon*channels)
    if inferential:validate_resolution(draws,len(groups)*len(bins),cutoff)
    with costs.section('validation'):
        seen=set(_validate_ids(reference,set()))
    with costs.section('setup'):
        enc={f:b.encode(reference[f]) for f,b in bins.items()}
        masks=group_masks(reference,groups)
        ref_counts={(gi,f):np.bincount(enc[f][mask],minlength=b.size) for gi,mask in enumerate(masks) for f,b in bins.items()}
        counts={k:np.zeros_like(a) for k,a in ref_counts.items()}
        nr={g.name:int(m.sum()) for g,m in zip(groups,masks)}
        scheduler=FrozenTargetScheduler(nr,plan)
        # Cache raw references for KS, without retaining a second whole frame.
        refs={(gi,f):reference[f].to_numpy(float)[mask].copy() for gi,mask in enumerate(masks) for f in bins} if method=='KS' else {}
        pending={k:[] for k in ref_counts} if method=='KS' else {}
        stats['persistent_histogram_array_bytes']=sum(a.nbytes for a in [*ref_counts.values(),*counts.values()])
        stats['detector_state_accounted_bytes']=deep_bytes((bins,ref_counts,counts,refs,pending))
        del reference,enc,masks
    stats.update(peak_pending_ks_array_bytes=0,max_batch_frame_bytes=0)
    targets=dict(plan.targets);last=0
    for look,(timestamp,frame) in enumerate(windows,1):
        batch_start=time.perf_counter()
        with costs.section('validation'):
            ids=_validate_ids(frame,seen)
            # Validation + reusable encoding. No per-group feature re-encoding.
            encoded={f:b.encode(frame[f]) for f,b in bins.items()}
        with costs.section('grouping'):
            masks=group_masks(frame,groups)
            memberships={g.name:tuple(frame.index[mask]) for g,mask in zip(groups,masks)}
        with costs.section('collection'):
            blocks=scheduler.advance(timestamp,memberships)  # validates time/H/IDs before mutation
            seen.update(ids)
        with costs.section('histograms'):
            for gi,mask in enumerate(masks):
                for f,b in bins.items():
                    if method=='PSI':counts[gi,f]+=np.bincount(encoded[f][mask],minlength=b.size)
                    else:pending[gi,f].append(frame[f].to_numpy(float)[mask].copy())
        rows=[];schedule=[]
        for gi,(group,block) in enumerate(zip(groups,blocks)):
            with costs.section('provenance'):
                meta=dict(**block.metadata(),incoming_target=targets[group.name],min_reference=plan.min_reference,
                    plan_sha256=plan.sha256,historical_shortage=block.reference_n<plan.min_reference,
                    collecting_current=len(block.ids)<targets[group.name])
                schedule.append(meta)
            for fi,(feature,binning) in enumerate(bins.items()):
                row=dict(**meta,feature=feature,level=group.level,policy=plan.policy,
                    status='assessed' if block.ready else 'insufficient_support',psi=None,
                    p=1. if inferential else None,ks_p=1. if inferential else None,ks_d=None,
                    draws=0,censored=False,ks_status='insufficient_support')
                seed_key=[seed,look,gi,fi,0 if plan.policy=='batch' or block.opened_look==look else 1]
                if method=='PSI':
                    a,b=ref_counts[gi,feature],counts[gi,feature]
                    if histogram_observer is not None:histogram_observer(look,gi,feature,a.copy(),b.copy())
                    if int(b.sum())!=len(block.ids):raise AssertionError('Integer count conservation failed')
                    if block.ready:
                        with costs.section('psi_test'):
                            result=count_test(a,b,seed=seed_key,draws=draws,stop_above=cutoff) if inferential else dict(psi=float(psi_counts(a,b)),p=None,draws=0,censored=False)
                        row.update(**result,missing_reference=int(a[-1]),missing_current=int(b[-1]))
                        if trace is not None:trace(a.copy(),b.copy(),seed_key,dict(result))
                elif block.ready:
                    with costs.section('ks_test'):
                        a=refs[gi,feature];b=np.concatenate(pending[gi,feature])
                        row.update(ks_score(a,b))
                        with warnings.catch_warnings(record=True) as caught:
                            warnings.simplefilter('always');p=ks_missing(a,b) if inferential else None
                        row.update(ks_p=1. if caught and inferential else p,ks_status='conservative_warning' if caught else 'assessed',
                            ks_warning='; '.join(str(w.message) for w in caught) or None,
                            missing_reference=int(np.isnan(a).sum()),missing_current=int(np.isnan(b).sum()))
                rows.append(row)
            if block.ready or plan.policy=='batch':
                for feature in bins:
                    if method=='PSI':counts[gi,feature].fill(0)
                    else:pending[gi,feature]=[]
        with costs.section('adjustment'):
            ds=decisions(rows,plan,look,timestamp,method,cutoff,inferential)
        # Accounting measured separately from monitor kernel; RSS includes it.
        with costs.section('accounting'):
            stats['max_batch_frame_bytes']=max(stats['max_batch_frame_bytes'],int(frame.memory_usage(index=True,deep=True).sum()))
            stats['peak_pending_ks_array_bytes']=max(stats['peak_pending_ks_array_bytes'],sum(a.nbytes for parts in pending.values() for a in parts))
        last=look
        stats.setdefault('batch_latency_wall',[]).append(time.perf_counter()-batch_start)
        yield dict(tests=rows,schedule=schedule,decisions=ds)
        del frame,encoded,masks,memberships,blocks,rows,schedule,ds
    if last!=plan.horizon and not (allow_prefix and 0<last<=plan.horizon):raise ValueError('Declared horizon not fully delivered')
    with costs.section('accounting'):
        stats['validation_accounted_bytes_end']=deep_bytes((seen,scheduler))
        stats['detector_state_accounted_bytes_end']=deep_bytes((bins,ref_counts,counts,refs,pending))
    stats.update(costs.values,engine_wall=time.perf_counter()-start,engine_cpu=time.process_time()-cpu,looks=last,
                 validation_note='Exact seen draw IDs and original pending-ID scheduler retained in RAM; grows with stream length.')


def run_lightweight(reference,windows,**kwargs):
    """Convenience collector for equivalence/tests; benchmark uses iterator sink."""
    out=dict(tests=[],schedule=[],decisions=[]);stats={}
    for look in iter_monitor(reference,windows,stats=stats,**kwargs):
        for key in out:out[key].extend(look[key])
    out['metadata']=stats
    return out

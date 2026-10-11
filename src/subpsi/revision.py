"""Revision 2: finite-horizon tests, count-triggered blocks, and outcome audits.

All groups and test families are fixed before evaluation. Tests concern distributions,
not causal bias. Equal alpha/H spending is a union bound, not a new statistical method.
"""
import time
import numpy as np
from scipy.special import expit
from scipy.stats import ks_2samp, fisher_exact
from .core import NumericBins, psi_counts, adjust_pvalues

GROUP_NAMES=['Everyone','A=0','A=1','B=0','B=1','A=0 & B=0','A=0 & B=1','A=1 & B=0','A=1 & B=1']
METHODS=['Overall PSI','Intersection PSI','Overall KS','Intersection KS','Accumulated PSI','Per-batch PSI','Fixed PSI 0.1','Outcome audit','Combined monitor']


def masks(d):
    a,b=d['A'],d['B']
    return [np.ones(len(a),bool),a==0,a==1,b==0,b==1]+[(a==i)&(b==j) for i in [0,1] for j in [0,1]]


def generate(n,rng,case,progress=0):
    share=case.get('share',.1); kind=case['kind']; mag=case.get('magnitude',1.0)
    a=rng.binomial(1,.5 if kind=='cancellation' else 2*share,n)
    b=rng.binomial(1,.5,n); target=(a==1)&(b==1); parity=np.where(a==b,1,-1)
    z=rng.normal(.8*parity if kind=='cancellation' else 0,1,n)
    nuisance=rng.normal(size=n); x=z.copy(); y=rng.binomial(1,expit(2*z))
    if kind=='benign': x=nuisance.copy()
    if kind=='correlation':
        x2=.8*z+.6*nuisance
        if progress: x2=np.where(target,-.8*z+.6*nuisance,x2)
        # Marginal x and x2 distributions stay N(0,1); fixed predictor uses their sum.
        y=(z+.8*z+.6*nuisance>0).astype(int)
        return {'A':a,'B':b,'x':x,'x2':x2,'y':y,'pred':(x+x2>0).astype(int)}
    if progress:
        if kind in ['shift','gradual','benign']: x+=mag*progress*target
        elif kind=='cancellation': x-=mag*progress*np.where(parity==1,1,-case.get('cancel',1))
        elif kind=='missing': x[target & (rng.random(n)<mag*progress)]=np.nan
        elif kind=='outcome':
            change=target & (rng.random(n)<mag*progress); y[change]=1-y[change]
        elif kind=='composition':
            # Generated in separate branch below to preserve conditional feature distributions.
            a=rng.binomial(1,.8,n); target=(a==1)&(b==1)
    if kind=='composition': x=z+.8*a; y=rng.binomial(1,expit(2*x))
    pred=(np.nan_to_num(z if kind=='benign' else x,nan=0)>=0).astype(int)
    return {'A':a,'B':b,'x':x,'y':y,'pred':pred}


def count_test(a,b,*,seed,draws=9999,stop_above=.05):
    """Conservative shortcut: once final Monte Carlo p must exceed stop_above,
    return 1. This can only increase the p-value relative to the fixed draw budget.
    Chunk size remains fixed, so disabling stopping consumes identical RNG draws.
    """
    a=np.asarray(a,int); b=np.asarray(b,int); total=a+b
    if min(a.sum(),b.sum())<1: return {'psi':None,'p':1.,'draws':0,'censored':False}
    score=float(psi_counts(a,b)); rng=np.random.default_rng(seed); extreme=0; done=0
    while done<draws:
        size=min(64,draws-done)
        c=rng.multivariate_hypergeometric(total,int(a.sum()),size=size)
        extreme+=int(np.sum(psi_counts(c,total-c)>=score-1e-12)); done+=size
        if (extreme+1)/(draws+1)>stop_above:
            return {'psi':score,'p':1.,'draws':done,'censored':True}
    return {'psi':score,'p':(extreme+1)/(draws+1),'draws':done,'censored':False}


def ks_missing(a,b):
    """Bonferroni combines missing-rate Fisher and nonmissing KS (2 fixed tests).
    KS's continuous-null p is conservative at ties; asymptotic fallback is not used.
    """
    a,b=np.asarray(a,float),np.asarray(b,float); ma,mb=np.isnan(a),np.isnan(b)
    p_missing=float(fisher_exact([[int(ma.sum()),int((~ma).sum())],[int(mb.sum()),int((~mb).sum())]]).pvalue)
    x,y=a[~ma],b[~mb]
    if min(len(x),len(y))<2: p_ks=1.
    elif len(np.unique(np.r_[x,y]))==1: p_ks=1.
    else: p_ks=float(ks_2samp(x,y,method='exact').pvalue)
    return min(1.,2*min(p_missing,p_ks))


def performance(d,m):
    y,p=d['y'][m],d['pred'][m]
    return {'n':len(y),'positive':int((y==1).sum()),'negative':int((y==0).sum()),
            'tp':int(((y==1)&(p==1)).sum()),'fp':int(((y==0)&(p==1)).sum()),'correct':int((y==p).sum())}


def outcome_tests(base,cur,min_n):
    rows=[]
    for group,(a,b) in enumerate(zip(base,cur)):
        for metric,num,den,direction in [('TPR','tp','positive','greater'),('FPR','fp','negative','less'),('Accuracy','correct','n','greater')]:
            eligible=min(a[den],b[den])>=min_n
            p=float(fisher_exact([[a[num],a[den]-a[num]],[b[num],b[den]-b[num]]],alternative=direction).pvalue) if eligible else 1.
            rows.append({'group':group,'metric':metric,'p':p,'eligible':eligible,'reference_n':a[den],'current_n':b[den],
                         'reference_rate':a[num]/a[den] if a[den] else None,'current_rate':b[num]/b[den] if b[den] else None})
    return rows


def run_stream(reference,design,audit,windows,c,seed):
    feats=[k for k in ['x','x2'] if k in reference]
    bins={f:NumericBins.fit(design[f],c['bins']) for f in feats}; rg=masks(reference)
    counts={(f,g):bins[f].counts(reference[f][m]) for f in feats for g,m in enumerate(rg)}
    baseline=[performance(audit,m) for m in masks(audit)]
    buffers={(f,g):[] for f in feats for g in range(9)}; starts={g:1 for g in range(9)}
    alpha=c['alpha']; h=c['windows']; rows=[]; outcomes=[]; details=[]
    assert len(windows)==h
    if c['permutations']+1 < 2*h*9*len(feats)/alpha: raise ValueError('Permutation budget cannot resolve combined-monitor threshold')
    for w,d in enumerate(windows,1):
        mg=masks(d); instant=[]; pooled=[]
        for f in feats:
            for g,m in enumerate(mg):
                a=counts[f,g]; vals=d[f][m]; b=bins[f].counts(vals); eligible=min(a.sum(),b.sum())>=c['min_n']
                t=time.perf_counter()
                # .05 cap retains all potential per-batch ablation rejections.
                test=count_test(a,b,seed=[seed,w,g,feats.index(f),0],draws=c['permutations'],stop_above=alpha) if eligible else {'psi':None,'p':1.,'draws':0,'censored':False}
                psi_seconds=time.perf_counter()-t; t=time.perf_counter()
                kp=ks_missing(reference[f][rg[g]],vals) if eligible else 1.
                ks_seconds=time.perf_counter()-t
                row={'window':w,'feature':f,'group':g,'n_reference':int(a.sum()),'n_current':int(b.sum()),'eligible':bool(eligible),**test,'ks_p':kp,'psi_seconds':psi_seconds,'ks_seconds':ks_seconds}
                instant.append(row)
                buffers[f,g].append(vals)
                poolvals=np.concatenate(buffers[f,g]); pc=bins[f].counts(poolvals)
                ready=min(int(a.sum()),int(pc.sum()))>=c['pool_n']
                if ready:
                    if starts[g]==w: pt=dict(test) if eligible else count_test(a,pc,seed=[seed,w,g,feats.index(f),1],draws=c['permutations'],stop_above=alpha/h)
                    else: pt=count_test(a,pc,seed=[seed,w,g,feats.index(f),1],draws=c['permutations'],stop_above=alpha/h)
                    buffers[f,g]=[]
                else: pt={'psi':None,'p':1.,'draws':0,'censored':False}
                pooled.append({'window':w,'feature':f,'group':g,'start_window':starts[g],'n_reference':int(a.sum()),'n_current':int(pc.sum()),'eligible':bool(ready),**pt})
        for g in range(9):
            if next(r for r in pooled if r['group']==g)['eligible']: starts[g]=w+1
        perf=[performance(d,m) for m in mg]; ot=outcome_tests(baseline,perf,c['outcome_min_n'])
        outcomes.extend([{'window':w,**r} for r in ot])
        op=adjust_pvalues([r['p'] for r in ot])
        ip=adjust_pvalues([r['p'] for r in instant]); pp=adjust_pvalues([r['p'] for r in pooled])
        for method in METHODS:
            source=instant; hit=[]; eligible_groups=[]
            if method in ['Overall PSI','Overall KS']:
                source=[r for r in instant if r['group']==0]
                ap=adjust_pvalues([r['p'] if method.endswith('PSI') else r['ks_p'] for r in source]); hit=[r['group'] for r,p in zip(source,ap) if p<=alpha/h]
            elif method=='Intersection PSI': hit=[r['group'] for r,p in zip(instant,ip) if p<=alpha/h]
            elif method=='Intersection KS': hit=[r['group'] for r,p in zip(instant,adjust_pvalues([r['ks_p'] for r in instant])) if p<=alpha/h]
            elif method=='Accumulated PSI':
                source=pooled; hit=[r['group'] for r,p in zip(pooled,pp) if p<=alpha/h]
            elif method=='Per-batch PSI': hit=[r['group'] for r,p in zip(instant,ip) if p<=alpha]
            elif method=='Fixed PSI 0.1': hit=[r['group'] for r in instant if r['psi'] is not None and r['psi']>=.1]
            elif method=='Outcome audit':
                source=ot; hit=[r['group'] for r,p in zip(ot,op) if p<=alpha/h]
            elif method=='Combined monitor':
                hit=[r['group'] for r,p in zip(instant,ip) if p<=alpha/(2*h)]+[r['group'] for r,p in zip(ot,op) if p<=alpha/(2*h)]
                source=instant+ot
            eligible_groups=sorted(set(r['group'] for r in source if r['eligible']))
            rows.append({'window':w,'method':method,'alert':bool(hit),'hits':sorted(set(hit)),'eligible_groups':eligible_groups})
        details.extend([{'policy':'batch',**r} for r in instant]+[{'policy':'accumulate',**r} for r in pooled])
    return {'decisions':rows,'tests':details,'outcomes':outcomes,'baseline_outcomes':baseline,'bins':{f:b.metadata() for f,b in bins.items()}}


def synthetic_run(c,case,repeat,seed):
    streams=np.random.SeedSequence([seed,repeat]).spawn(c['windows']+3)
    frames=[generate(c['n_'+r],np.random.default_rng(streams[i]),case) for i,r in enumerate(['reference','design','audit'])]
    windows=[]
    for w in range(1,c['windows']+1):
        progress=0 if w<c['onset'] or case['kind']=='null' else min(1,(w-c['onset']+1)/6) if case['kind']=='gradual' else 1
        windows.append(generate(case['n'],np.random.default_rng(streams[w+2]),case,progress))
    out=run_stream(*frames,windows,c,int(np.random.SeedSequence([seed,repeat,981]).generate_state(1)[0]))
    return {'case':case,'repeat':repeat,'seed':[seed,repeat],**out}

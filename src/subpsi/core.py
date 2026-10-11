"""Fixed-bin PSI and independent-sample permutation tests.

Bin design must use independent data. Count permutations condition on pooled
bin totals; they are exact draws from the label-permutation null distribution,
not a chi-squared approximation. No label/outcome argument is accepted.
"""
from dataclasses import dataclass
from itertools import combinations
from math import comb
import numpy as np
import pandas as pd


def _vector(x, name):
    a = np.asarray(x, dtype=float)
    if a.ndim != 1 or not len(a):
        raise ValueError(f"{name} must be a nonempty vector")
    return a


def proportions(counts, pseudocount=0.5):
    c = np.asarray(counts, dtype=float)
    if c.ndim < 1 or c.shape[-1] == 0 or not np.all(np.isfinite(c)) or np.any(c < 0):
        raise ValueError("counts must be finite, nonnegative and nonempty")
    if not np.isfinite(pseudocount) or pseudocount <= 0:
        raise ValueError("pseudocount must be positive")
    if np.any(c.sum(axis=-1) <= 0):
        raise ValueError("empty samples are unsupported")
    return (c + pseudocount) / (c.sum(axis=-1, keepdims=True) + c.shape[-1] * pseudocount)


def psi_counts(reference, current, pseudocount=0.5):
    p, q = proportions(reference, pseudocount), proportions(current, pseudocount)
    if p.shape != q.shape:
        raise ValueError("histograms must use the same bins and shape")
    return np.sum((q - p) * np.log(q / p), axis=-1)


def psi_probabilities(p, q):
    """Unsmooth population formula for strictly positive teaching fixtures."""
    p, q = _vector(p, "p"), _vector(q, "q")
    if p.shape != q.shape or np.any(p <= 0) or np.any(q <= 0):
        raise ValueError("positive matching probability vectors required")
    if not np.isfinite(p).all() or not np.isfinite(q).all() or not np.isclose(p.sum(), 1) or not np.isclose(q.sum(), 1):
        raise ValueError("probabilities must be finite and sum to one")
    return float(np.sum((q-p)*np.log(q/p)))


@dataclass(frozen=True)
class NumericBins:
    edges: tuple

    def __post_init__(self):
        e = np.asarray(self.edges, float)
        if len(e) < 2 or e[0] != -np.inf or e[-1] != np.inf or not np.all(np.diff(e) > 0):
            raise ValueError("strictly increasing edges from -inf to +inf required")

    @classmethod
    def fit(cls, design, n_bins=10):
        a = _vector(design, "design")
        if not isinstance(n_bins, int) or n_bins < 2:
            raise ValueError("n_bins must be an integer >= 2")
        if np.isinf(a).any():
            raise ValueError("infinite observations are invalid; NaN is explicit missingness")
        a = a[~np.isnan(a)]
        if not len(a):
            raise ValueError("design has no observed numeric values")
        if a.min() == a.max():
            c = float(a[0])
            inner = [c, np.nextafter(c, np.inf)]
            inner = [v for v in inner if np.isfinite(v)]
        else:
            inner = np.unique(np.quantile(a, np.linspace(0, 1, n_bins+1)[1:-1])).tolist()
        return cls(tuple([-np.inf, *inner, np.inf]))

    @property
    def size(self):
        return len(self.edges)  # finite-value bins plus one explicit missing bin

    def encode(self, values):
        a = np.asarray(values, float)
        if a.ndim != 1 or np.isinf(a).any():
            raise ValueError("numeric input must be a vector without infinities")
        codes = np.searchsorted(np.asarray(self.edges)[1:-1], a, side="right")
        codes[np.isnan(a)] = self.size - 1
        return codes

    def counts(self, values):
        return np.bincount(self.encode(values), minlength=self.size)

    def metadata(self):
        return {"kind":"numeric", "edges":[str(e) if not np.isfinite(e) else e for e in self.edges],
                "effective_numeric_bins":len(self.edges)-1,"missing_bin":self.size-1}


@dataclass(frozen=True)
class CategoryBins:
    categories: tuple

    @classmethod
    def fit(cls, design):
        a = list(design)
        if not a:
            raise ValueError("empty design")
        if any(not isinstance(v, str) for v in a if not pd.isna(v)):
            raise ValueError("categorical values must be strings or missing")
        return cls(tuple(sorted(set(v for v in a if not pd.isna(v)))))

    @property
    def size(self):
        return len(self.categories) + 2

    def encode(self, values):
        mapping = {v:i for i,v in enumerate(self.categories)}
        a = list(values)
        if any(not isinstance(v, str) for v in a if not pd.isna(v)):
            raise ValueError("categorical values must be strings or missing")
        return np.array([self.size-1 if pd.isna(v) else mapping.get(v,self.size-2) for v in a],dtype=int)

    def counts(self, values):
        return np.bincount(self.encode(values), minlength=self.size)

    def metadata(self):
        return {"kind":"categorical","categories":list(self.categories),"unknown_bin":self.size-2,"missing_bin":self.size-1}


def permutation_test_counts(reference, current, *, n_resamples=1999, seed=0, pseudocount=0.5, exact_limit=20000):
    a, b = _vector(reference,"reference"), _vector(current,"current")
    if a.shape != b.shape or np.any(a < 0) or np.any(b < 0) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("matching nonnegative finite counts required")
    if np.any(a != np.floor(a)) or np.any(b != np.floor(b)):
        raise ValueError("permutation counts must be integers")
    if not isinstance(n_resamples, int) or n_resamples < 1:
        raise ValueError("n_resamples must be a positive integer")
    observed = float(psi_counts(a,b,pseudocount))
    a,b = a.astype(np.int64),b.astype(np.int64)
    total, n = a+b,int(a.sum())
    if min(a.sum(),b.sum()) < 1:
        raise ValueError("both samples must be nonempty")
    possible = comb(int(total.sum()),n)
    tolerance = 100*np.finfo(float).eps*max(abs(observed),1)
    if possible <= exact_limit:
        labels = np.repeat(np.arange(len(total)),total)
        extreme=0
        for selection in combinations(range(len(labels)),n):
            c = np.bincount(labels[list(selection)],minlength=len(total))
            extreme += float(psi_counts(c,total-c,pseudocount)) >= observed-tolerance
        return {"psi":observed,"pvalue":extreme/possible,"resamples":possible,"exact":True}
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_hypergeometric(total,n,size=n_resamples)
    scores=psi_counts(draws,total-draws,pseudocount)
    extreme=int(np.count_nonzero(scores >= observed-tolerance))
    return {"psi":observed,"pvalue":(extreme+1)/(n_resamples+1),"resamples":n_resamples,"exact":False}


def adjust_pvalues(values, method="holm"):
    p=np.asarray(values,float)
    if p.ndim != 1 or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
        raise ValueError("p-values must be a finite vector in [0,1]")
    if method not in {"holm","bh","by"}:
        raise ValueError("method must be holm, bh or by")
    if not len(p): return p.copy()
    order=np.argsort(p,kind="stable"); v=p[order]; m=len(p)
    if method == "holm": adjusted=np.maximum.accumulate(v*np.arange(m,0,-1))
    else:
        factor=np.sum(1/np.arange(1,m+1)) if method=="by" else 1
        adjusted=np.minimum.accumulate((v*m*factor/np.arange(1,m+1))[::-1])[::-1]
    out=np.empty(m); out[order]=np.minimum(adjusted,1)
    return out


def validate_resolution(n_resamples, family_size, alpha=0.05):
    if not 0<alpha<1 or family_size<1:
        raise ValueError("invalid alpha or family size")
    if n_resamples+1 < family_size/alpha:
        raise ValueError("permutation p-value floor exceeds the first Holm cutoff")


@dataclass(frozen=True)
class Group:
    name: str
    selectors: tuple = ()
    level: str = "aggregate"

    def mask(self, frame):
        m=np.ones(len(frame),dtype=bool)
        for col,value in self.selectors:
            m &= frame[col].isna().to_numpy() if value is None else (frame[col]==value).fillna(False).to_numpy(dtype=bool)
        return m


def union_groups(reference,current,columns,intersection=True,predefined=()):
    """Only specified columns; one pair maximum. Never search for flattering slices."""
    if len(columns)>2: raise ValueError("at most two grouping attributes")
    groups=[Group("all")]
    for col in columns:
        vals={None if pd.isna(x) else x for x in pd.concat([reference[col],current[col]])}
        for v in sorted(vals,key=repr): groups.append(Group(f"{col}={v!r}",((col,v),),"single"))
    if intersection and len(columns)==2:
        pairs=set()
        for x,y in pd.concat([reference[list(columns)],current[list(columns)]]).itertuples(index=False,name=None):
            pairs.add((None if pd.isna(x) else x,None if pd.isna(y) else y))
        for x,y in sorted(pairs,key=repr):
            groups.append(Group(f"{columns[0]}={x!r} & {columns[1]}={y!r}",((columns[0],x),(columns[1],y)),"intersection"))
    seen={g.selectors for g in groups}
    for group in predefined:
        if group.selectors not in seen:
            groups.append(group)
            seen.add(group.selectors)
    return groups


def compare(reference,current,bins,groups,*,min_n=50,n_resamples=1999,seed=0,pseudocount=0.5):
    if min_n < 1: raise ValueError("min_n must be positive")
    if len({g.name for g in groups})!=len(groups): raise ValueError("duplicate group names")
    rows=[]
    streams=np.random.SeedSequence(seed).spawn(len(bins)*len(groups))
    for feature,binning in bins.items():
        ref_codes=binning.encode(reference[feature]); cur_codes=binning.encode(current[feature])
        for group in groups:
            rm,cm=group.mask(reference),group.mask(current)
            a=np.bincount(ref_codes[rm],minlength=binning.size)
            b=np.bincount(cur_codes[cm],minlength=binning.size)
            nr,nc=int(a.sum()),int(b.sum())
            supported=min(nr,nc)>=min_n
            row={"feature":feature,"group":group.name,"level":group.level,"n_reference":nr,"n_current":nc,
                 "missing_reference":int(a[-1]),"missing_current":int(b[-1]),
                 "counts_reference":a.tolist(),"counts_current":b.tolist(),
                 "status":"assessed" if supported else "insufficient_evidence",
                 "psi":None,"pvalue":1.0,"resamples":0,"exact":False}
            if supported: row.update(permutation_test_counts(a,b,n_resamples=n_resamples,seed=streams[len(rows)],pseudocount=pseudocount))
            rows.append(row)
    return rows


def decisions(rows,alpha=0.05,threshold=0.1):
    """Separate declared method families, including p=1 unsupported comparisons."""
    result={}
    for name,levels in [("A1",{"aggregate"}),("B1",{"aggregate","single"}),("B2",{"aggregate","single","intersection"})]:
        r=[x for x in rows if x["level"] in levels]
        adjusted=adjust_pvalues([x["pvalue"] for x in r])
        hit=[x["group"]+" / "+x["feature"] for x,p in zip(r,adjusted) if x["status"]=="assessed" and p<=alpha]
        result[name]={"alert":bool(hit),"hits":hit,"family_size":len(r),"assessed":sum(x["status"]=="assessed" for x in r),"adjusted_pvalues":adjusted.tolist()}
    for name,levels in [("A0",{"aggregate"}),("B0",{"aggregate","single","intersection"})]:
        r=[x for x in rows if x["level"] in levels]
        hit=[x["group"]+" / "+x["feature"] for x in r if x["psi"] is not None and x["psi"]>=threshold]
        result[name]={"alert":bool(hit),"hits":hit,"family_size":len(r),"assessed":sum(x["status"]=="assessed" for x in r)}
    return result

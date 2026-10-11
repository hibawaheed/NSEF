"""Approved revision-3 source roles, frozen baseline and whole-record controls.

Natural inference is descriptive. Conditional controls resample real whole rows;
no generated feature values or fabricated calendar dates are used.
"""
import hashlib
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import norm
from .matched import declared_groups
from .provenance import sha256


def acs_role(key, year):
    v = int(hashlib.sha256(f'r3-role-31721|{key}'.encode()).hexdigest()[:16], 16) / 2**64
    if year == 2015:
        return 'fit' if v < .5 else 'design' if v < .75 else 'calibration'
    return ('reference' if v < .5 else 'audit') if year == 2016 else ('monitor' if v < .5 else 'audit')


def oulad_role(student, period):
    v = int(hashlib.sha256(f'r3-oulad-31721|{student}'.encode()).hexdigest()[:16], 16) / 2**64
    if period == '2013J':
        return 'fit' if v < .4 else 'design' if v < .6 else 'reference' if v < .8 else 'audit'
    return 'monitor' if v < .5 else 'audit'


def eligible_oulad(info, registration, module='BBB'):
    keys = ['code_module', 'code_presentation', 'id_student']
    if info.duplicated(keys).any() or registration.duplicated(keys).any():
        raise ValueError('Duplicate enrolment key')
    pair = info.loc[info.code_module.eq(module) & info.code_presentation.isin(['2013J', '2014J'])].merge(
        registration, on=keys, how='left', validate='one_to_one', indicator=True)
    if not pair['_merge'].eq('both').all():
        raise ValueError('Missing registration match')
    earlier = set(pair.loc[pair.code_presentation.eq('2013J'), 'id_student'])
    eligible = pair.date_registration.le(0) & (pair.date_unregistration.isna() | pair.date_unregistration.gt(0))
    repeats = pair.code_presentation.eq('2014J') & pair.id_student.isin(earlier)
    return pair.loc[eligible & ~repeats].copy()


def validate_schema(df, features, levels):
    if not np.isfinite(df[features].to_numpy(float)).all():
        raise ValueError('Unexpected missing/infinite selected feature; stop rather than improvise imputation')
    for col, values in levels.items():
        if not df[col].isin(values).all():
            raise ValueError(f'Unexpected group code in {col}')
    if not df.index.is_unique:
        raise ValueError('Nonunique row keys')


def load_datasets(root, config):
    """Verify raw hashes and reproduce the pre-review private role assignments."""
    root = Path(root); sources = {}; frames = {}
    for year in config['acs']['years']:
        path = root / f'data/raw/revision3/acs/{year}/csv_pma.zip'
        receipt = json.loads(path.with_suffix('.receipt.json').read_text())
        if sha256(path) != receipt['sha256']:
            raise ValueError('ACS source hash mismatch')
        sources[str(path.relative_to(root))] = sha256(path)
        with zipfile.ZipFile(path) as z:
            member = next(n for n in z.namelist() if n.endswith('.csv'))
            with z.open(member) as f:
                d = pd.read_csv(f, usecols=['SERIALNO','SPORDER','ST','AGEP','SCHL','SEX','RAC1P','ESR'], dtype={'SERIALNO': str})
        if not d.ST.eq(25).all() or d.duplicated(['SERIALNO','SPORDER']).any():
            raise ValueError('Unexpected state or duplicate person key')
        d = d.loc[d.AGEP.between(*config['acs']['age_inclusive'])].copy()
        if not d.ESR.isin(range(1,7)).all():
            raise ValueError('Unknown adult outcome')
        d['record_id'] = [f'{year}:{s}:{o}' for s,o in zip(d.SERIALNO, d.SPORDER)]
        d['household_id'] = [f'{year}:{s}' for s in d.SERIALNO]
        d.index = d.record_id
        d['role'] = [acs_role(k, year) for k in d.household_id]
        lineage = d[['record_id','household_id','role']].to_csv(index=False).encode()
        old = root / f'data/raw/revision3/lineage/acs_{year}_proposed_roles.csv'
        if hashlib.sha256(lineage).hexdigest() != sha256(old):
            raise ValueError('ACS roles differ from inspected proposal')
        sources[str(old.relative_to(root))] = sha256(old)
        d['label'] = d.ESR.eq(1).astype(int)
        validate_schema(d, config['acs']['features'], config['acs']['group_levels'])
        frames[year] = d
    acs = dict(name='ACS_MA', frames=frames, fit=frames[2015].query("role == 'fit'"),
               design=frames[2015].query("role == 'design'"), reference=frames[2016].query("role == 'reference'"),
               audit_reference=frames[2016].query("role == 'audit'"),
               windows=[(y, frames[y].query("role == 'monitor'")) for y in [2017,2018,2019]],
               audits=[(y, frames[y].query("role == 'audit'")) for y in [2017,2018,2019]],
               features=config['acs']['features'], groups=declared_groups(config['acs']['group_levels']), model_kind='acs')
    source = root / 'data/raw/revision3/oulad/metadata'
    receipt = json.loads((source/'receipt.json').read_text())
    for member in receipt['members']:
        path = source/member['name']
        if sha256(path) != member['sha256']:
            raise ValueError('OULAD source hash mismatch')
        sources[str(path.relative_to(root))] = sha256(path)
    info = pd.read_csv(source/'studentInfo.csv', na_values=['?'])
    reg = pd.read_csv(source/'studentRegistration.csv', na_values=['?'])
    d = eligible_oulad(info, reg, config['oulad']['module'])
    if not d.final_result.isin(['Pass','Distinction','Fail','Withdrawn']).all():
        raise ValueError('Unknown OULAD outcome')
    d['role'] = [oulad_role(i,p) for i,p in zip(d.id_student,d.code_presentation)]
    lineage = d[['code_module','code_presentation','id_student','role']].to_csv(index=False).encode()
    old = root/'data/raw/revision3/lineage/oulad_proposed_roles.csv'
    if hashlib.sha256(lineage).hexdigest() != sha256(old):
        raise ValueError('OULAD roles differ from inspected proposal')
    sources[str(old.relative_to(root))] = sha256(old)
    d.index = [f'OULAD:{m}:{p}:{i}' for m,p,i in zip(d.code_module,d.code_presentation,d.id_student)]
    d['label'] = d.final_result.isin(['Pass','Distinction']).astype(int)
    validate_schema(d, config['oulad']['features'], config['oulad']['group_levels'])
    old = d.loc[d.code_presentation.eq('2013J')]; new = d.loc[d.code_presentation.eq('2014J')]
    oulad = dict(name='OULAD_BBB', frames={2013:old,2014:new}, fit=old.query("role == 'fit'"),
                 design=old.query("role == 'design'"), reference=old.query("role == 'reference'"),
                 audit_reference=old.query("role == 'audit'"), windows=[(2014,new.query("role == 'monitor'"))],
                 audits=[(2014,new.query("role == 'audit'"))], features=config['oulad']['features'],
                 groups=declared_groups(config['oulad']['group_levels']), model_kind='oulad')
    return [acs, oulad], sources


class FrozenLogistic:
    """L2 logistic baseline, C=1, unpenalized intercept, historical fit only."""
    def __init__(self, kind):
        if kind not in {'acs','oulad'}:
            raise ValueError('Unknown baseline')
        self.kind = kind

    def numeric(self, frame):
        if self.kind == 'acs':
            age = frame.AGEP.to_numpy(float)
            return np.column_stack([age, age**2])
        return frame[['num_of_prev_attempts','studied_credits']].to_numpy(float)

    def transform(self, frame):
        z = (self.numeric(frame)-self.mean)/self.scale
        if self.kind == 'acs':
            z = np.column_stack([z, *[frame.SCHL.eq(v).to_numpy(float) for v in self.categories]])
        return np.column_stack([np.ones(len(frame)), z])

    def fit(self, frame):
        x = self.numeric(frame)
        self.mean = x.mean(axis=0); self.scale = x.std(axis=0)
        self.scale[self.scale == 0] = 1.
        self.categories = sorted(frame.SCHL.unique().tolist()) if self.kind == 'acs' else []
        x = self.transform(frame); y = frame.label.to_numpy(float)
        if not np.isfinite(x).all() or set(y) != {0.,1.}:
            raise ValueError('Baseline requires finite features and both labels')
        def objective(beta):
            z = x @ beta
            penalty = beta.copy(); penalty[0] = 0
            return (float(np.logaddexp(0,z).sum()-y@z + .5*(penalty@penalty)),
                    x.T @ (expit(z)-y)+penalty)
        fit = minimize(objective, np.zeros(x.shape[1]), jac=True, method='L-BFGS-B',
                       options={'gtol':1e-8,'ftol':1e-12,'maxiter':2000})
        if not fit.success or not np.isfinite(fit.fun):
            raise RuntimeError(f'Logistic convergence failure: {fit.message}')
        self.coef = fit.x
        self.fit_info = dict(n=len(y), positives=int(y.sum()), objective=float(fit.fun),
                             iterations=int(fit.nit), convergence=str(fit.message),
                             max_abs_gradient=float(np.max(np.abs(fit.jac))))
        return self

    def predict(self, frame):
        return (expit(self.transform(frame) @ self.coef) >= .5).astype(int)

    def metadata(self):
        return dict(kind=self.kind, numeric_mean=self.mean.tolist(), numeric_scale=self.scale.tolist(),
                    schooling_categories=self.categories, coefficients=self.coef.tolist(), fit=self.fit_info,
                    C=1., threshold=.5, objective='sum logistic loss + .5 * nonintercept squared norm')


def audit_outcomes(reference, current, groups, model, minimum=20):
    """Descriptive group/complement rates and gaps with explicit denominators."""
    predictions = [model.predict(d) for d in [reference,current]]
    rows = []
    for group in groups:
        counts = []
        for d,p in zip([reference,current], predictions):
            y = d.label.to_numpy(int); mask = group.mask(d)
            def count(m):
                return {'TPR':(int(((y==1)&(p==1)&m).sum()),int(((y==1)&m).sum())),
                        'FPR':(int(((y==0)&(p==1)&m).sum()),int(((y==0)&m).sum())),
                        'Accuracy':(int(((y==p)&m).sum()),int(m.sum()))}
            counts.append((count(mask), count(~mask)))
        for metric in ['TPR','FPR','Accuracy']:
            r = {'group':group.name,'level':group.level,'metric':metric}
            for period,c in zip(['baseline','current'],counts):
                for prefix,entry in zip(['','complement_'],c):
                    num,den = entry[metric]
                    r[f'{period}_{prefix}numerator'] = num
                    r[f'{period}_{prefix}denominator'] = den
                    r[f'{period}_{prefix}rate'] = num/den if den >= minimum else None
            supported = min(r['baseline_denominator'],r['current_denominator']) >= minimum
            r['rate_status'] = 'assessed' if supported else 'insufficient_denominator'
            r['rate_change'] = r['current_rate']-r['baseline_rate'] if supported else None
            gap_ok = supported and group.level != 'aggregate' and min(r['baseline_complement_denominator'],r['current_complement_denominator']) >= minimum
            r['gap_status'] = 'assessed' if gap_ok else 'not_applicable' if group.level == 'aggregate' else 'insufficient_denominator'
            for period in ['baseline','current']:
                r[f'{period}_gap'] = r[f'{period}_rate']-r[f'{period}_complement_rate'] if gap_ok else None
            r['gap_change'] = r['current_gap']-r['baseline_gap'] if gap_ok else None
            rows.append(r)
    return rows


def household_pool(frame):
    """One preselected adult per household; independent of features/outcomes."""
    return frame.sort_values(['household_id','SPORDER'],kind='stable').drop_duplicates('household_id').copy()


def constructed_stream(pool, replacement_pool, n, seed, condition, horizon=20, onset=6, reference_n=10000):
    if condition not in {'unchanged','substitution'}:
        raise ValueError('Unknown control condition')
    if len(pool)==0 or len(replacement_pool)==0:
        raise ValueError('Empty source pool')
    if not (replacement_pool.SEX.eq(2) & replacement_pool.RAC1P.eq(2)).all():
        raise ValueError('Replacement pool must contain only the prespecified target')
    def draw(rng, source, count, prefix):
        d = source.iloc[rng.integers(len(source),size=count)].copy()
        d['source_id'] = d.index
        d.index = [f'{prefix}:{i}' for i in range(count)]
        return d
    ref = draw(np.random.default_rng([seed,n,1]),pool,reference_n,'reference')
    stream_rng = np.random.default_rng([seed,n,2]); replace_rng = np.random.default_rng([seed,n,3])
    windows = []
    for look in range(1,horizon+1):
        d = draw(stream_rng,pool,n,f'delivery:{look}')
        if condition == 'substitution' and look >= onset:
            mask = d.SEX.eq(2) & d.RAC1P.eq(2)
            rep = draw(replace_rng,replacement_pool,int(mask.sum()),'replacement')
            # Replace the whole record, including its source identifier and label.
            d.loc[mask,:] = rep.to_numpy()
        windows.append((look,d))
    return ref, windows


def wilson(k,n,confidence=.95):
    if not n:
        return (None,None)
    z = norm.ppf((1+confidence)/2); p=k/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den
    radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return float(max(0,center-radius)),float(min(1,center+radius))


def paired_interval(a,b,seed=948271,draws=2000):
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.shape!=b.shape or a.ndim!=1 or not len(a) or not np.isfinite(a-b).all():
        raise ValueError('Complete paired stream arrays required')
    delta=a-b; rng=np.random.default_rng(seed)
    means=delta[rng.integers(len(delta),size=(draws,len(delta)))].mean(axis=1)
    lo,hi=np.quantile(means,[.025,.975])
    return {'difference':float(delta.mean()),'low':float(lo),'high':float(hi),
            'degenerate':bool(np.all(delta==delta[0])),'n_pairs':len(delta)}

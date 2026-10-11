"""Bounded, explicitly post-result corrections. Earlier implementations stay intact."""
import hashlib
import numpy as np
import pandas as pd
from .core import NumericBins
from .realdata import FrozenLogistic
from .revision import generate
from .matched import declared_groups, run_matched


class AttemptBins(NumericBins):
    """Historical 2013J design rule: zero / one / two-or-more / missing.

    This is a feature-specific correction, not a general quantile algorithm.
    Half-integer cuts prevent tied nonnegative integers collapsing at zero.
    """
    def __init__(self):
        super().__init__((-np.inf, .5, 1.5, np.inf))

    def encode(self, values):
        a = np.asarray(values, float)
        observed = a[~np.isnan(a)]
        if a.ndim != 1 or not np.isfinite(observed).all() or np.any(observed < 0) or np.any(observed != np.floor(observed)):
            raise ValueError('Previous attempts must be nonnegative integer counts or NaN')
        return super().encode(a)

    def metadata(self):
        return {**super().metadata(), 'rule': 'historical OULAD correction: 0 / 1 / 2+',
                'labels': ['0', '1', '2 or more', 'missing']}


class TrainingMajority:
    """One training-only decision, including a prespecified zero-on-tie rule."""
    def fit(self, labels):
        y = np.asarray(labels)
        if y.ndim != 1 or not len(y) or not np.isin(y, [0, 1]).all():
            raise ValueError('Nonempty binary training labels required')
        self.counts = [int((y == v).sum()) for v in [0, 1]]
        self.constant = int(self.counts[1] > self.counts[0])
        return self

    def predict(self, frame):
        return np.full(len(frame), self.constant, dtype=int)

    def metadata(self):
        return {'training_counts': self.counts, 'constant_prediction': self.constant,
                'tie_rule': 'predict 0', 'uses_audit_labels_for_selection': False}


def restore_model(metadata):
    """Restore the saved frozen parameters; no fit or hyperparameter search."""
    if metadata['kind'] != 'oulad' or metadata['threshold'] != .5 or metadata['C'] != 1.:
        raise ValueError('Unexpected frozen OULAD model')
    model = FrozenLogistic('oulad')
    model.mean = np.array(metadata['numeric_mean'])
    model.scale = np.array(metadata['numeric_scale'])
    model.categories = metadata['schooling_categories']
    model.coef = np.array(metadata['coefficients'])
    model.fit_info = metadata['fit']
    if model.metadata() != metadata:
        raise ValueError('Frozen metadata failed round trip')
    return model


def synthetic_inputs(c, old):
    """Regenerate exactly the saved V2 simulation, without additional records."""
    case = old['case']; seed, repeat = old['seed']
    expected = c['seed'] + int(hashlib.sha256(case['id'].encode()).hexdigest()[:7], 16)
    if seed != expected or repeat != old['repeat']:
        raise ValueError('Original V2 seed mismatch')
    streams = np.random.SeedSequence([seed, repeat]).spawn(c['windows'] + 3)
    # The original audit seed slot is reserved. Its labels are not monitor inputs.
    def frame(data, prefix):
        return pd.DataFrame({k:v for k,v in data.items() if k not in {'y', 'pred'}},
                            index=[f'{prefix}:{i}' for i in range(len(data['x']))])
    reference = frame(generate(c['n_reference'], np.random.default_rng(streams[0]), case), 'reference')
    design = frame(generate(c['n_design'], np.random.default_rng(streams[1]), case), 'design')
    windows = []
    for w in range(1, c['windows'] + 1):
        progress = 0 if w < c['onset'] or case['kind'] == 'null' else min(1, (w-c['onset']+1)/6) if case['kind'] == 'gradual' else 1
        windows.append((w, frame(generate(case['n'], np.random.default_rng(streams[w+2]), case, progress), f'look{w}')))
    bins = {f:NumericBins.fit(design[f], c['bins']) for f in ['x', 'x2'] if f in design}
    if {f:b.metadata() for f,b in bins.items()} != old['bins']:
        raise ValueError('Original V2 design bins changed')
    seed_test = int(np.random.SeedSequence([seed, repeat, 981]).generate_state(1)[0])
    return reference, windows, bins, declared_groups({'A':[0,1], 'B':[0,1]}), seed_test


def matched_v2(c, old):
    reference, windows, bins, groups, seed = synthetic_inputs(c, old)
    result = run_matched(reference, windows, bins=bins, groups=groups,
                         min_n=c['pool_n'], alpha=c['alpha'], draws=c['permutations'],
                         seed=seed, inferential=True)
    validate_v2_parity(old, result, groups)
    return result


def validate_v2_parity(old, result, groups):
    """Fail loudly if the historical PSI experiment has changed."""
    indices = {g.name:i for i,g in enumerate(groups)}
    previous = {(r['window'],r['group'],r['feature']):r for r in old['tests'] if r['policy']=='accumulate'}
    if len(previous) != len(result['tests']):
        raise ValueError('Different opportunity count')
    for r in result['tests']:
        o = previous[r['look'], indices[r['group']], r['feature']]
        if (r['n_reference'],r['n_current'],r['eligible'],r['opened_look']) != (o['n_reference'],o['n_current'],o['eligible'],o['start_window']):
            raise ValueError('V2 collection/support mismatch')
        if r['eligible'] and not np.isclose(r['psi'],o['psi'],rtol=0,atol=1e-12):
            raise ValueError('V2 PSI score mismatch')
    for r in result['decisions']:
        if r['scope']=='intersection' and r['method']=='PSI':
            o = next(d for d in old['decisions'] if d['window']==r['look'] and d['method']=='Accumulated PSI')
            hits = sorted({indices[g] for g,_ in r['hits']})
            if r['alert'] != o['alert'] or hits != o['hits']:
                raise ValueError('V2 PSI alert mismatch')


def stream_metrics(result, c, old):
    rows = []; onset = c['onset']; horizon = c['windows']-onset+1
    target = 'A=1 & B=1'; tests = result['tests']
    post_tests = [r for r in tests if r['look']>=onset]
    target_tests = [r for r in post_tests if r['group']==target]
    assessed = [r for r in target_tests if r['eligible']]
    for method in ['PSI', 'KS']:
        decisions = [r for r in result['decisions'] if r['scope']=='intersection' and r['method']==method]
        post = [r for r in decisions if r['look']>=onset]
        hits = [r['look'] for r in post if r['alert']]
        targets = [r['look'] for r in post if any(g==target for g,_ in r['hits'])]
        supported = [r for r in tests if r['eligible']]
        rows.append({**{k:v for k,v in old['case'].items() if k!='repeats'}, 'repeat':old['repeat'],
                     'method':method, 'stream_alert':any(r['alert'] for r in decisions),
                     'pre_alert':any(r['alert'] for r in decisions if r['look']<onset),
                     'post_alert':bool(hits), 'target_detected':bool(targets),
                     'restricted_delay':min(hits)-onset if hits else horizon,
                     'target_restricted_delay':min(targets)-onset if targets else horizon,
                     'target_ever_assessed':bool(assessed),
                     'target_first_assessment_restricted':min(r['look'] for r in assessed)-onset if assessed else horizon,
                     'target_assessed_fraction':sum(r['eligible'] for r in target_tests)/len(target_tests),
                     'eligible_fraction':sum(r['eligible'] for r in post_tests)/len(post_tests),
                     'maximum_block_age':max((r['maximum_age'] or 0 for r in supported), default=0),
                     'test_seconds':sum(r[f'{method.lower()}_seconds'] for r in tests),
                     'maximum_logical_payload_bytes':max((r[f'{method.lower()}_payload_bytes'] for r in supported), default=0),
                     'shared_input_frame_bytes':result['metadata']['shared_input_frame_bytes']})
    return rows

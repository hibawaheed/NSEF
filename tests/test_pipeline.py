import importlib.util,json
from pathlib import Path
import numpy as np
from subpsi.scenarios import predefined_groups
ROOT=Path(__file__).resolve().parents[1]


def load_script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_independent_synthetic_pipeline_reproduces(monkeypatch):
    m=load_script('run_synthetic'); c=json.loads((ROOT/'configs/synthetic.json').read_text())
    c.update(n_fit=200,n_design=200,n_reference=100,n_audit=200,n_window=100,windows=2,onset_window=2,min_n=5,n_resamples=399)
    original=m.compare
    def guarded(reference,current,*args,**kwargs):
        assert 'y' not in reference.columns and 'y' not in current.columns
        return original(reference,current,*args,**kwargs)
    monkeypatch.setattr(m,'compare',guarded)
    a=m.one_run(c,'S1',0); b=m.one_run(c,'S1',0)
    assert a==b
    assert len(a['windows'])==2
    assert a['windows'][1]['methods']['B2']['family_size']==18
    assert a['role_hashes']['reference']!=a['windows'][0]['input_sha256']


def test_adult_no_reused_rows_within_run():
    m=load_script('run_adult'); c=json.loads((ROOT/'configs/adult.json').read_text())
    import pandas as pd
    rng=np.random.default_rng(1)
    pool=pd.DataFrame({'A':np.repeat([0,0,1,1],150),'B':np.repeat([0,1,0,1],150),'hours-per-week':rng.integers(10,60,600),'id':[str(x) for x in range(600)]})
    c.update(n_window=80,windows=4)
    windows=m.sample_windows(pool,c,'female_hours_tilt',0)
    ids=[i for w in windows for i in w.id]
    assert len(ids)==len(set(ids))==320
    assert all(set(w['hours-per-week'])<=set(pool['hours-per-week']) for w in windows)


def test_wilson_endpoints_are_valid_plot_intervals():
    m=load_script('make_figures')
    for values in [[0]*60,[1]*60,[0,1,1]]:
        r=m.wilson(values)
        assert 0<=r['low']<=r['estimate']<=r['high']<=1
        assert r['estimate']-r['low']>=0 and r['high']-r['estimate']>=0

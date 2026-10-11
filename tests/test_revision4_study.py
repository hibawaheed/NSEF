"""Software fixtures only; no fixture is reported as collected research data."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from subpsi.core import NumericBins
from subpsi.matched import declared_groups
from subpsi.revision4 import validate_draw_lineage, run_frozen_targets
from subpsi.revision4_study import (evaluation_stream, source_distances, inventory,
    plans, seed_integer, support_map, stream_summary)


def config():
    c=json.loads((Path(__file__).parents[1]/'configs/revision4/approved.json').read_text())
    c['evaluation'].update(reference_draw_n=100,batch_size=40,end=4,onset=3)
    c['monitoring'].update(horizon=4,min_reference=1,permutations=479)
    return c


def pool():
    return pd.DataFrame({'AGEP':[20,30,65,75,25,70,35,80],
        'SCHL':[12,15,19,23,15,21,19,18],'SEX':[2,2,2,2,1,1,1,1],
        'RAC1P':[2,2,2,2,1,1,1,1],'label':[0,1,0,1,0,1,1,0],
        'household_id':[f'h{i}' for i in range(8)]},index=[f's{i}' for i in range(8)])


def test_stream_pairing_whole_rows_and_pre_onset_invariance():
    c=config();p=pool();original=p.copy(deep=True)
    a,aw=evaluation_stream(p,c,3,'unchanged')
    for condition in ['age_up2','age_up4','age_down4']:
        b,bw=evaluation_stream(p,c,3,condition)
        pd.testing.assert_frame_equal(a,b)
        for (time,x),(_,y) in zip(aw,bw):
            validate_draw_lineage(y,p)
            if time<3: pd.testing.assert_frame_equal(x,y)
            other=~(x.SEX.eq(2)&x.RAC1P.eq(2))
            pd.testing.assert_frame_equal(x.loc[other],y.loc[other])
            pd.testing.assert_frame_equal(x[['SEX','RAC1P']],y[['SEX','RAC1P']])
    pd.testing.assert_frame_equal(p,original)
    assert not set(a.index).intersection(pd.concat([f for _,f in aw]).index)
    assert a.source_id.nunique()<len(a)
    c2=deepcopy(c); changed=p.assign(label=1-p.label)
    r,rw=evaluation_stream(changed,c2,3,'age_up4')
    s,sw=evaluation_stream(p,c2,3,'age_up4')
    assert r.source_id.tolist()==s.source_id.tolist()
    assert [f.source_id.tolist() for _,f in rw]==[f.source_id.tolist() for _,f in sw]


def test_stage_and_channel_randomness_are_separate_and_reproducible():
    c=config()
    assert seed_integer(c,'selection',0,0)==seed_integer(c,'selection',0,0)
    values={seed_integer(c,stage,cell,rep,channel) for stage in ['selection','validation','evaluation']
            for cell in [0,1] for rep in [0,1] for channel in [1,2,3,4]}
    assert len(values)==48


def test_empirical_distances_and_null():
    p=pool();bins={'AGEP':NumericBins((-np.inf,60,np.inf))}
    a=source_distances(p,bins,1)[0];b=source_distances(p,bins,4)[0]
    assert a['source_psi']==0 and a['source_ks']==0
    assert b['source_psi']==pytest.approx(.3*np.log(4))
    assert b['source_ks']==pytest.approx(.3)


def test_support_requires_both_halves_and_both_strata():
    row={'group':'Everyone'}
    for s in ['selection','validation']: row.update({s+'_households':50,s+'_age_ge60':5,s+'_age_lt60':45})
    assert support_map(pd.DataFrame([row]),config())=={'Everyone':True}
    row['validation_age_ge60']=4
    assert support_map(pd.DataFrame([row]),config())=={'Everyone':False}


def test_inventories_and_maps_include_all_groups_and_deduplicate_validation():
    c=config();g=declared_groups({'SEX':[1,2]})
    chosen={'group_targets':[{'group':x.name,'target':800} for x in g],'global_target':800}
    cells=inventory(c,g,'selection')
    assert len(cells)==3*3*5*3 and [r['cell'] for r in cells]==list(range(len(cells)))
    val=inventory(c,g,'validation',chosen)
    assert len(val)==3*4 and all(r['reference_n']==400 for r in val)
    policies=plans(c,g,chosen)
    assert policies['global_calibrated'].metadata()==policies['group_calibrated'].metadata()
    assert policies['ordinary_50'].policy=='batch'
    assert all(p.min_reference==1 for p in policies.values())
    with pytest.raises(ValueError): inventory(c,g,'validation')


def test_stream_endpoints_retain_misses_pre_onset_alerts_and_never_assessed():
    decisions=[{'scope':scope,'method':method,'look':look,'alert':look==1,'hits':[('target','x')] if look==1 else []}
               for scope in ['aggregate','single','intersection'] for method in ['PSI','KS'] for look in range(1,5)]
    result={'decisions':decisions,'schedule':[dict(group='target',eligible=False,look=i) for i in range(1,5)]}
    rows=stream_summary(result,'target',onset=3,horizon=4)
    assert all(r['whole_stream_alert'] and r['pre_onset_alert'] for r in rows)
    assert all(not r['exact_target_detection'] and r['restricted_delay']==2 for r in rows)
    assert all(r['first_assessment'] is None and not r['ever_assessed'] for r in rows)


def test_five_policy_fixture_end_to_end_exact_shared_maps_tie():
    c=config();p=pool();g=declared_groups({'SEX':[1,2],'RAC1P':[1,2]})
    chosen={'group_targets':[{'group':x.name,'target':20} for x in g],'global_target':20}
    ref,win=evaluation_stream(p,c,0,'age_up4');bins={'AGEP':NumericBins((-np.inf,60,np.inf))}
    outputs={}
    for name,plan in plans(c,g,chosen).items():
        outputs[name]=run_frozen_targets(ref,win,bins=bins,groups=g,plan=plan,draws=999,inferential=True,seed=123)
    fields=['block_sha256','p','ks_p','psi','eligible','n_current','n_reference']
    for a,b in zip(outputs['global_calibrated']['tests'],outputs['group_calibrated']['tests']):
        assert {f:a[f] for f in fields}=={f:b[f] for f in fields}
    assert len(outputs['ordinary_50']['schedule'])==4*len(g)

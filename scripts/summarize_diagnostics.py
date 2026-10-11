#!/usr/bin/env python3
"""Additional tables: coverage, outcomes, relevance, and transparent denominators."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import write_json,sha256
from make_figures import load_runs,mean_interval,wilson,METHODS


def main():
    p=argparse.ArgumentParser(); p.add_argument('--runs',required=True); p.add_argument('--out',required=True); args=p.parse_args()
    path=ROOT/args.runs; runs,meta,c=load_runs(path); out=ROOT/args.out; out.mkdir(parents=True,exist_ok=False)
    windows=[]; outcome=[]; coverage=[]; denominators=[]
    for r in runs:
        for w in r['windows']:
            for m in METHODS:
                d=w['methods'][m]
                windows.append({'scenario':r['scenario'],'repeat':r['repeat'],'window':w['window'],'active':w['active'],'method':m,
                                'alert':d['alert'],'tpr_gap_change':w['tpr_gap_change'],
                                'outcome_relevance_observed':w['tpr_gap_change'] is not None and w['tpr_gap_change']>=.05,
                                'assessed':d['assessed'],'declared_tests':d['family_size']})
            for t in w['tests']:
                coverage.append({'scenario':r['scenario'],'repeat':r['repeat'],'window':w['window'],**{k:t[k] for k in ['group','feature','n_reference','n_current','status','missing_reference','missing_current']}})
            for row in w['performance']:
                outcome.append({'scenario':r['scenario'],'repeat':r['repeat'],'window':w['window'],'active':w['active'],**row})
    wf=pd.DataFrame(windows); of=pd.DataFrame(outcome); cf=pd.DataFrame(coverage)
    wf.to_csv(out/'window_decisions.csv',index=False); of.to_csv(out/'group_outcomes.csv',index=False); cf.to_csv(out/'assessment_coverage.csv',index=False)
    summaries=[]
    for scenario in c['scenarios']:
        for m in METHODS:
            subset=wf[(wf.scenario==scenario)&(wf.method==m)&wf.active]
            alert=subset[subset.alert]; ratios=[]
            for repeat,one in subset.groupby('repeat'):
                eligible=one[one.alert]
                if len(eligible): ratios.append(float(eligible.outcome_relevance_observed.mean()))
            summaries.append({'scenario':scenario,'method':m,'post_onset_windows':len(subset),'alert_windows':len(alert),
                              'alert_windows_with_gap_increase_ge_5pp':int(alert.outcome_relevance_observed.sum()),
                              'pooled_descriptive_warning_precision':float(alert.outcome_relevance_observed.mean()) if len(alert) else None,
                              'eligible_runs_with_alert':len(ratios),'mean_run_warning_precision':float(np.mean(ratios)) if ratios else None,
                              'interpretation':'No binomial window interval: windows share a stream/reference. No alerts yields undefined precision, not zero.'})
    write_json(out/'warning_relevance.json',summaries)
    counts={
     'runs':len(runs),'planned_runs':meta['planned_runs'],'failed_runs':meta['failures'],
     'runtime_seconds':meta['runtime_seconds'],'input_comparisons':len(cf),
     'unsupported_comparisons':int((cf.status!='assessed').sum()),
     'minimum_reference_group_n':int(cf.n_reference.min()),'minimum_current_group_n':int(cf.n_current.min()),
     'smallest_outcome_positive_n':int(of.positive.min()),'smallest_outcome_negative_n':int(of.negative.min()),
     'label_access':'Detector receives no outcomes. Outcome measurements do not alter alerts/model/reference.',
     'source_manifest_sha256':sha256(path/'manifest.json')}
    write_json(out/'summary.json',counts)
    print(json.dumps(counts,indent=2))

if __name__=='__main__': main()

"""Summarize and plot approved R4 saved results; no data-driven tuning."""
import argparse
from datetime import datetime,timezone
import gzip
import itertools
import json
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,write_json,environment
from subpsi.correction import read_table
from subpsi.revision4 import wilson_lower
from subpsi.revision4_study import rng


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--out',default='figures/revision4/final');args=parser.parse_args()
    root=args.root;source=root/'results/summary/revision4/main-approved';raw=root/'results/raw/revision4/main-approved'
    out=root/args.out;out.mkdir(parents=True,exist_ok=False)
    c=json.loads((root/'configs/revision4/approved.json').read_text())
    if not (raw/'evaluation_complete.json').exists(): raise ValueError('Full evaluation required')
    selection=read_table(source/'selection_cells.csv');validation=read_table(source/'validation_cells.csv')
    streams=read_table(source/'streams.csv');coverage=read_table(source/'coverage.csv');costs=read_table(source/'costs.csv')
    frozen=json.loads((raw/'frozen_targets.json').read_text());targets=frozen['selection']
    for frame in [streams,coverage]:
        if frame.empty: raise ValueError('Missing results')
    policies=c['monitoring']['policies'];conditions=c['evaluation']['conditions']
    scenario_label={'unchanged':'Unchanged source','age_up2':'Age 60+ weight ×2','age_up4':'Age 60+ weight ×4','age_down4':'Age 60+ weight ×0.25'}
    labels={'ordinary_50':'One batch (50)','fixed_100':'Accumulate 100','fixed_400':'Accumulate 400',
            'global_calibrated':'Global calibration','group_calibrated':'Group calibration'}
    if targets['global_status']=='criterion_unmet_fallback': labels['global_calibrated']=f"Global fallback {targets['global_target']}"
    if all(r['status']!='criterion_met_selection_only' for r in targets['group_targets']): labels['group_calibrated']='Group fallback 800'
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'svg.fonttype':'none','pdf.fonttype':42})
    figures=[];pack=PdfPages(out/'CHART_PACK.pdf')
    def export(stem,fig,table,parents,explanation):
        table.to_csv(out/f'{stem}.csv',index=False)
        for extension in ['png','pdf','svg']:fig.savefig(out/f'{stem}.{extension}',dpi=300,facecolor='white')
        pack.savefig(fig,facecolor='white')
        plt.close(fig)
        figures.append(dict(stem=stem,source_csv=stem+'.csv',source_tables={str(p.relative_to(root)):sha256(p) for p in parents},explanation=explanation))
    # Exact pointwise intervals for every declared group, including missing cells.
    groups=selection.group.drop_duplicates().tolist(); supported=selection.loc[selection.status.eq('assessed'),'group'].drop_duplicates().tolist()
    for scenario in c['calibration']['selection_conditions']:
        table=selection.loc[selection.scenario.eq(scenario)].copy()
        fig,axes=plt.subplots(1,6,figsize=(18,12),sharey=True)
        for ax,(reference,method) in zip(axes,itertools.product(c['calibration']['reference_grid'],['PSI','KS'])):
            part=table.loc[table.reference_n.eq(reference)&table.method.eq(method)]
            arr=part.pivot(index='group',columns='incoming_n',values='rate').reindex(index=groups,columns=c['calibration']['incoming_grid']).to_numpy(float)
            cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#dddddd')
            im=ax.imshow(arr,vmin=0,vmax=1,aspect='auto',cmap=cmap)
            ax.set_xticks(range(5),c['calibration']['incoming_grid'],rotation=90)
            ax.set_yticks(range(len(groups)),groups);ax.set_title(f'{method}\nReference {reference}')
            ax.set_xlabel('Incoming draw count')
        fig.suptitle(f'Historical single-block sensitivity: {scenario_label[scenario]}',fontsize=17,y=.975)
        fig.subplots_adjust(left=.17,right=.91,top=.9,bottom=.10,wspace=.14)
        color=fig.add_axes([.93,.22,.012,.58]);fig.colorbar(im,cax=color,label='Success fraction (100 repetitions)')
        fig.text(.5,.035,'2015 selection records, resampled whole. Gray = historical support shortage. Fixed family/horizon cutoff; not whole-stream power.',ha='center',fontsize=10)
        export('01_sensitivity_'+scenario,fig,table,[source/'selection_cells.csv'],
               'Each square reports how often a single block signalled under the declared constructed condition. Reference size, incoming size and statistic vary. Gray groups lack enough independent historical source households; they are not successful or failed tests.')
    # Selection/validation contrast at the exact frozen group target.
    map_by_group={r['group']:r for r in targets['group_targets']};rows=[]
    for stage,frame in [('selection',selection),('validation',validation)]:
        for group in groups:
            n=map_by_group[group]['target']
            subset=frame.loc[frame.group.eq(group)&frame.reference_n.eq(400)&frame.incoming_n.eq(n)&frame.scenario.isin(c['calibration']['design_alternatives'])]
            assessed=subset.loc[subset.status.eq('assessed')]
            rows.append(dict(stage=stage,group=group,target=n,selection_status=map_by_group[group]['status'],
                minimum_rate=float(assessed.rate.min()) if len(assessed) else None,
                minimum_lower=float(assessed.lower.min()) if len(assessed) else None,
                criterion_met=bool(len(assessed)==4 and assessed.lower.min()>=.8)))
    comparison=pd.DataFrame(rows);comparison.to_csv(source/'selection_validation.csv',index=False)
    fig,ax=plt.subplots(figsize=(11,12)); y=np.arange(len(groups))
    for stage,offset,color in [('selection',-.16,'#0072B2'),('validation',.16,'#D55E00')]:
        part=comparison.loc[comparison.stage.eq(stage)].set_index('group').loc[groups]
        ax.scatter(part.minimum_lower,y+offset,label=stage,color=color,s=25)
    ax.axvline(.8,color='black',linestyle='--',label='Selection criterion')
    ax.set_yticks(y,[f'{g}  [n={map_by_group[g]["target"]}]' for g in groups]);ax.invert_yaxis()
    ax.set_xlim(-.025,1);ax.set_xlabel('Minimum 95% Wilson lower bound across both statistics and age-up alternatives')
    ax.set_title('Frozen group targets: selection and independent validation',pad=18);ax.legend(loc='lower right')
    fig.subplots_adjust(left=.35,right=.97,top=.92,bottom=.1)
    fig.text(.65,.025,'Blank = historical shortage. Falling short remains a failure; targets are not retuned.',ha='center',fontsize=9)
    export('02_frozen_targets_validation',fig,comparison,[source/'selection_cells.csv',source/'validation_cells.csv',raw/'frozen_targets.json'],
           'Dots show the worst lower confidence bound across the two statistics and both design changes at the frozen group target. The dashed line is the declared 80% criterion. Missing dots mean support shortage. This check does not certify stream detection probability.')
    # Wilson intervals for all scopes; exact intersection detection only meaningful in intersection scope.
    summary=[]
    binary=['whole_stream_alert','pre_onset_alert','exact_target_detection','ever_assessed']
    for (cond,policy,scope,method),frame in streams.groupby(['condition','policy','scope','method'],sort=False):
        for metric in binary:
            if metric=='exact_target_detection' and scope!='intersection': continue
            k=int(frame[metric].sum());n=len(frame)
            report_metric='exact_target_false_alert' if cond=='unchanged' and metric=='exact_target_detection' else metric
            summary.append(dict(condition=cond,policy=policy,scope=scope,method=method,metric=report_metric,
                successes=k,repeats=n,rate=k/n,lower=0. if k==0 else wilson_lower(k,n),upper=1. if k==n else 1-wilson_lower(n-k,n)))
    summary=pd.DataFrame(summary);summary.to_csv(source/'rates.csv',index=False)
    reported=streams.copy()
    reported['exact_target_scope_applicable']=reported.scope.eq('intersection')
    reported['change_present']=~reported.condition.eq('unchanged')
    reported['exact_target_false_alert']=reported.exact_target_detection.where(
        reported.exact_target_scope_applicable & ~reported.change_present,None)
    # Raw engine rows retain their literal zero-hit records; secondary scopes
    # cannot address this intersection target and are marked N/A in reporting.
    for column in ['exact_target_detection','first_detection','restricted_delay']:
        reported[column]=reported[column].astype(object)
        reported.loc[~reported.exact_target_scope_applicable,column]=None
        reported.loc[~reported.change_present,column]=None
    reported.to_csv(source/'stream_endpoints_reported.csv',index=False)
    ref_summary=coverage.loc[coverage.condition.eq('unchanged')&coverage.policy.eq('ordinary_50')].groupby('group',sort=False).agg(
        minimum_reference_n=('n_reference','min'),median_reference_n=('n_reference','median'),maximum_reference_n=('n_reference','max'),
        fraction_below_reference_gate=('n_reference',lambda x:float((x<50).mean())),
        fraction_below_planning_reference=('n_reference',lambda x:float((x<400).mean()))).reset_index()
    ref_summary['planning_reference_n']=400;ref_summary['collection_reference_gate']=50
    ref_summary.to_csv(source/'evaluation_reference_counts.csv',index=False)
    table=summary.loc[summary.scope.eq('intersection')&
        ((summary.condition.eq('unchanged')&summary.metric.eq('whole_stream_alert'))|
         (~summary.condition.eq('unchanged')&summary.metric.eq('exact_target_detection')))].copy()
    fig,axes=plt.subplots(1,4,figsize=(17,6),sharey=True)
    for ax,cond in zip(axes,conditions):
        for i,(method,color) in enumerate([('PSI','#0072B2'),('KS','#D55E00')]):
            part=table.loc[table.condition.eq(cond)&table.method.eq(method)].set_index('policy').loc[policies]
            x=np.arange(5)+(i-.5)*.2
            ax.errorbar(x,part.rate,yerr=np.maximum(0,np.vstack([part.rate-part.lower,part.upper-part.rate])),fmt='o',capsize=3,label=method,color=color)
        ax.set_xticks(range(5),[labels[p] for p in policies],rotation=55,ha='right');ax.set_title('Null: any alert' if cond=='unchanged' else scenario_label[cond]+': target')
        ax.set_ylim(-.035,1.06);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Fraction of streams');axes[-1].legend(loc='lower right')
    fig.suptitle('Same records and error budgets: complete policy comparison',fontsize=16,y=.97)
    fig.subplots_adjust(left=.06,right=.99,top=.86,bottom=.34,wspace=.15)
    fig.text(.5,.035,'2016 empirical-source resampling. 100 null / 40 per alternative. Pointwise 95% Wilson intervals; neither natural accuracy nor population inference.',ha='center',fontsize=10)
    export('03_paired_policy_alerts',fig,table,[source/'streams.csv'],
           'The null panel asks whether any intersection-family alert occurred. The alternative panels ask whether the prespecified target group was detected after onset. Every declared policy and both statistics are shown on identical streams, with misses included.')
    # Compact paper layout, same complete data and fixed 0–100% scale.
    with plt.rc_context({'font.size':8,'axes.titlesize':9,'axes.labelsize':8}):
        fig,axes=plt.subplots(2,2,figsize=(7.2,6.6),sharey=True)
        for ax,cond in zip(axes.flat,conditions):
            for i,(method,color) in enumerate([('PSI','#0072B2'),('KS','#D55E00')]):
                part=table.loc[table.condition.eq(cond)&table.method.eq(method)].set_index('policy').loc[policies]
                ax.errorbar(np.arange(5)+(i-.5)*.18,part.rate,
                    yerr=np.maximum(0,np.vstack([part.rate-part.lower,part.upper-part.rate])),fmt='o',markersize=3,capsize=2,label=method,color=color)
            ax.set_xticks(range(5),['Batch 50','Fixed 100','Fixed 400','Global 800','Group 800'],rotation=45,ha='right')
            ax.set_title('Unchanged: any false alert' if cond=='unchanged' else scenario_label[cond]+': target')
            ax.set_ylim(-.035,1.06);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y',alpha=.2)
        axes[0,0].legend(loc='upper right');axes[0,0].set_ylabel('Fraction of streams');axes[1,0].set_ylabel('Fraction of streams')
        fig.subplots_adjust(left=.10,right=.98,top=.94,bottom=.23,hspace=.64,wspace=.20)
        fig.text(.5,.07,'Whole-record resampling: 100 unchanged streams; 40 per declared change.',ha='center',fontsize=8)
        fig.text(.5,.043,'Pointwise 95% Wilson intervals. Both calibrated rules fell back to 800.',ha='center',fontsize=8)
        fig.text(.5,.016,'Conditional experimental evidence; not accuracy on natural survey changes.',ha='center',fontsize=8)
        export('03b_paper_policy_alerts',fig,table,[source/'streams.csv'],
               'Paper-sized version of the complete four-condition policy comparison. It uses exactly the same rows, intervals, scale and methods as figure 03; neither favorable nor unfavorable conditions were omitted.')
    # All complete-stream pairings: bootstrap differences, not independent-error bars.
    primary=streams.loc[streams.scope.eq('intersection')].copy();paired=[]
    keys=[(p,m) for p in policies for m in ['PSI','KS']]
    for ci,cond in enumerate(conditions):
        data=primary.loc[primary.condition.eq(cond)]; reps=sorted(data.repeat.unique())
        draws=rng(c,'bootstrap',ci,0,1).integers(len(reps),size=(c['uncertainty']['paired_bootstrap_repetitions'],len(reps)))
        metrics=['whole_stream_alert','pre_onset_alert','exact_target_detection','ever_assessed','restricted_delay','assessment_fraction']
        if cond=='unchanged':metrics.remove('restricted_delay')
        for metric in metrics:
            values={key:data.loc[data.policy.eq(key[0])&data.method.eq(key[1])].set_index('repeat').loc[reps,metric].to_numpy(float) for key in keys}
            for a,b in itertools.combinations(keys,2):
                difference=values[a]-values[b]; estimates=difference[draws].mean(axis=1)
                lower,upper=np.quantile(estimates,[.025,.975])
                report_metric='exact_target_false_alert' if cond=='unchanged' and metric=='exact_target_detection' else metric
                paired.append(dict(condition=cond,metric=report_metric,policy_a=a[0],method_a=a[1],policy_b=b[0],method_b=b[1],
                    repeats=len(reps),difference=float(difference.mean()),lower=float(lower),upper=float(upper),
                    identical_observed_endpoints=bool(np.all(difference==0)),bootstrap_repetitions=len(draws)))
    pd.DataFrame(paired).to_csv(source/'paired_differences.csv',index=False)
    # Assessability for all declared groups and conditions.
    cov=coverage.groupby(['condition','group','policy'],sort=False).agg(assessability=('ever_assessed','mean'),
         assessment_fraction=('assessment_fraction','mean'),never_assessed=('never_assessed','sum'),
         streams=('never_assessed','size'),mean_reference_n=('n_reference','mean'),
         mean_pending_records=('pending_records','mean'),mean_assessed_wait=('mean_assessed_wait','mean')).reset_index()
    cov.to_csv(source/'coverage_summary.csv',index=False)
    fig,axes=plt.subplots(1,4,figsize=(16,12),sharey=True)
    for ax,cond in zip(axes,conditions):
        arr=cov.loc[cov.condition.eq(cond)].pivot(index='group',columns='policy',values='assessability').reindex(index=groups,columns=policies)
        im=ax.imshow(arr,vmin=0,vmax=1,aspect='auto',cmap='cividis')
        ax.set_yticks(range(len(groups)),groups);ax.set_xticks(range(5),[labels[p] for p in policies],rotation=65,ha='right');ax.set_title(scenario_label[cond])
    fig.suptitle('Could each group be assessed at least once?',fontsize=17,y=.98)
    fig.subplots_adjust(left=.19,right=.93,top=.92,bottom=.20,wspace=.15)
    fig.colorbar(im,cax=fig.add_axes([.95,.3,.012,.5]),label='Fraction ever assessed')
    fig.text(.55,.04,'All 30 groups retained. A test being possible does not mean a change was detected. Reference support cannot be repaired by collecting incoming records.',ha='center',fontsize=9)
    export('04_all_group_assessability',fig,cov,[source/'coverage.csv'],
           'This chart shows whether a policy collected enough records to perform any test for each group. Low assessability and never-assessed groups remain visible. PSI and KS have exactly the same availability because their collection schedule is shared.')
    # Detection delay includes every miss at the prespecified 15-look restriction.
    table=primary.loc[~primary.condition.eq('unchanged')].copy()
    fig,axes=plt.subplots(1,3,figsize=(15,6),sharey=True)
    for ax,cond in zip(axes,conditions[1:]):
        for i,(method,color) in enumerate([('PSI','#0072B2'),('KS','#D55E00')]):
            part=table.loc[table.condition.eq(cond)&table.method.eq(method)]
            means=part.groupby('policy').restricted_delay.mean().reindex(policies)
            ax.plot(np.arange(5)+(i-.5)*.12,means,'o-',label=method,color=color)
        ax.set_xticks(range(5),[labels[p] for p in policies],rotation=50,ha='right');ax.set_title(scenario_label[cond])
        ax.set_ylim(-.3,15.7);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Mean restricted detection delay (looks)');axes[-1].legend()
    fig.suptitle('Waiting for detection: misses stay in the denominator',fontsize=16,y=.98)
    fig.subplots_adjust(left=.07,right=.99,top=.86,bottom=.34,wspace=.15)
    fig.text(.5,.04,'Onset is look 6. Detection then has delay 0; no detection by look 20 receives 15. First assessment is saved separately. Paired intervals are in paired_differences.csv.',ha='center',fontsize=9)
    export('05_detection_wait_including_misses',fig,table,[source/'streams.csv'],
           'A lower number means earlier detection. Undetected streams receive the full 15-look restricted waiting value, so a method cannot look fast by excluding its misses. These are constructed delivery looks, not days or survey years.')
    # Replayed OULAD simple baseline, exact same records.
    full=read_table(source/'oulad_outcomes_extended.csv'); table=full.query("group == 'Everyone' and subset == 'group' and period == 'current'").copy()
    fig,ax=plt.subplots(figsize=(11,5.8)); order=['Accuracy','Balanced accuracy','TPR','FPR'];x=np.arange(4)
    for i,(model,color) in enumerate([('Frozen logistic','#0072B2'),('Training-majority baseline','#D55E00')]):
        values=table.loc[table.model.eq(model)].set_index('metric').loc[order,'value']
        bars=ax.bar(x+(i-.5)*.35,values,.35,label=model,color=color);ax.bar_label(bars,labels=[f'{v:.1%}' for v in values],padding=4)
    ax.set_xticks(x,['Accuracy','Balanced accuracy','TPR','FPR (lower better)']);ax.set_ylim(0,1.15)
    ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_title('OULAD corrected replay: model versus training-only baseline',pad=45)
    ax.legend(loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2,frameon=False)
    fig.subplots_adjust(top=.76,bottom=.2,left=.08,right=.98)
    fig.text(.5,.06,'2014J audit, same 973 records: frozen model 541 correct; constant baseline 547. Constant class chosen only from 2013J training labels.',ha='center',fontsize=9)
    fig.text(.5,.025,'Previously examined cohorts; this is a documented correction replay, not untouched validation or evidence of natural drift-detection accuracy.',ha='center',fontsize=9)
    export('06_oulad_model_baseline',fig,table,[source/'oulad_outcomes_extended.csv'],
           'The simple majority baseline is slightly more accurate than the frozen model. Balanced accuracy is about 50.9% for the model and 50% for the baseline. This limits claims about outcome prediction; the input-monitoring comparison is a separate question.')
    # Costs distinguish kernel arrays from measured whole-process memory.
    table=costs.copy();fig,axes=plt.subplots(1,2,figsize=(12,6));x=np.arange(5)
    for method,column,color in [('PSI','psi_kernel_seconds','#0072B2'),('KS','ks_kernel_seconds','#D55E00')]:
        means=table.groupby('policy')[column].mean().reindex(policies)
        axes[0].plot(x,means,'o-',label=method,color=color)
    axes[0].set_ylabel('Mean kernel seconds per complete stream');axes[0].legend();axes[0].set_title('Measured statistic computation')
    means=table.groupby('policy').wall_seconds.mean().reindex(policies)
    axes[1].bar(x,means,color='#777777');axes[1].set_ylabel('Mean seconds per policy engine');axes[1].set_title('Shared engine, both statistics + setup')
    for ax in axes: ax.set_xticks(x,[labels[p] for p in policies],rotation=45,ha='right');ax.grid(axis='y',alpha=.2)
    fig.subplots_adjust(left=.08,right=.98,top=.86,bottom=.3,wspace=.3)
    fig.suptitle('Compute cost is part of the comparison',fontsize=16,y=.98)
    fig.text(.5,.035,'Sequential local runs. Whole-process peak RSS and logical payloads are saved in the source CSV; peak RSS cannot be attributed to one statistic.',ha='center',fontsize=9)
    export('07_compute_costs',fig,table,[source/'costs.csv'],
           'The left panel times the two statistic kernels separately. The right includes both statistics and shared setup. Memory columns distinguish small logical arrays from whole-process peak memory. Timing is hardware-dependent; no scaling guarantee is claimed.')
    # The known OULAD binning correction is shown with every declared view retained.
    path=raw/'oulad-replay/old_vs_corrected.csv'; table=read_table(path)
    table=table.loc[table.feature.eq('num_of_prev_attempts')].copy()
    variants=table.variant.drop_duplicates().tolist();oulad_groups=table.group.drop_duplicates().tolist()
    fig,axes=plt.subplots(1,len(variants),figsize=(5*len(variants),7),sharey=True,squeeze=False)
    for ax,variant in zip(axes[0],variants):
        part=table.loc[table.variant.eq(variant)].set_index('group').loc[oulad_groups]
        for column,label,color,offset in [('psi_old','Original bins','#777777',-.12),('psi_new','Corrected bins','#0072B2',.12)]:
            ax.scatter(part[column],np.arange(len(oulad_groups))+offset,label=label,color=color,s=32)
        ax.set_yticks(range(len(oulad_groups)),oulad_groups);ax.invert_yaxis();ax.set_title(variant)
        ax.set_xlabel('Descriptive PSI');ax.grid(axis='x',alpha=.2)
    axes[0,-1].legend(loc='lower right')
    fig.suptitle('Known OULAD representation error: preserve the before/after comparison',fontsize=15,y=.97)
    fig.subplots_adjust(left=.19,right=.98,top=.87,bottom=.15,wspace=.18)
    fig.text(.5,.035,'2013J reference versus 2014J incoming BBB records. Blank = insufficient support. Same records and unchanged KS. This is a post-result correction.',ha='center',fontsize=9)
    export('08_oulad_corrected_psi',fig,table,[path],
           'The correction separates zero, one and two-or-more previous attempts. This changes PSI because the old bins discarded that distinction. Original values are retained beside corrected values; neither gives natural drift-detection accuracy because the true onset is unknown.')
    # Calibration costs are included separately, never hidden as free preprocessing.
    costs_cal=[]
    for stage in ['selection','validation']:
        for path in sorted((raw/stage).glob('*.json.gz')):
            with gzip.open(path,'rt') as handle:r=json.load(handle)
            costs_cal.append(dict(**r['cell'],status=r['status'],cpu_seconds=r['cpu_seconds'],wall_seconds=r['wall_seconds'],
                peak_process_rss_kib=r['peak_rss_kib'],psi_kernel_seconds=sum(x['psi_seconds'] for x in r['rows']),
                ks_kernel_seconds=sum(x['ks_seconds'] for x in r['rows']),
                ks_warnings=sum(x['ks_status']=='conservative_warning' for x in r['rows']),
                raw_file=str(path.relative_to(root)),raw_sha256=sha256(path)))
    pd.DataFrame(costs_cal).to_csv(source/'calibration_costs.csv',index=False)
    pipeline=pd.DataFrame(costs_cal).groupby('stage',sort=False).agg(cpu_seconds=('cpu_seconds','sum'),
        wall_seconds=('wall_seconds','sum'),peak_process_rss_kib=('peak_process_rss_kib','max')).reset_index()
    pipeline=pd.concat([pipeline,pd.DataFrame([dict(stage='evaluation',cpu_seconds=costs.cpu_seconds.sum(),
        wall_seconds=costs.wall_seconds.sum(),peak_process_rss_kib=costs.peak_process_rss_kib.max())])],ignore_index=True)
    pipeline.to_csv(source/'pipeline_costs.csv',index=False)
    fig,axes=plt.subplots(1,3,figsize=(15,5.6))
    axes[0].bar(pipeline.stage,pipeline.cpu_seconds/60,color=['#56B4E9','#009E73','#777777'])
    axes[0].set_ylabel('Sum of recorded cell / engine CPU minutes');axes[0].set_title('Calibration is part of the cost')
    axes[1].bar(pipeline.stage,pipeline.peak_process_rss_kib/1024,color='#777777')
    axes[1].set_ylabel('Whole-process peak RSS (MiB)');axes[1].set_title('Shared process memory')
    payload=pd.DataFrame([dict(method='PSI',bytes=int(costs.psi_max_payload_bytes.max())),
                          dict(method='KS',bytes=int(costs.ks_max_payload_bytes.max()))])
    axes[2].bar(payload.method,payload.bytes,color=['#0072B2','#D55E00']);axes[2].set_yscale('log')
    axes[2].set_ylabel('Maximum logical input-array bytes (log scale)');axes[2].set_title('Kernel payload only')
    for ax in axes:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    for ax in axes[:2]:ax.tick_params(axis='x',rotation=25)
    fig.suptitle('Keep preprocessing, process memory and statistic payload separate',fontsize=15,y=.98)
    fig.subplots_adjust(left=.07,right=.98,top=.85,bottom=.25,wspace=.38)
    fig.text(.5,.04,'Cell/engine sums exclude loading, reporting and verification overhead. Peak RSS is cumulative for the shared process; small histogram arrays do not prove a smaller whole system.',ha='center',fontsize=9)
    table=pd.concat([pipeline.assign(record_type='stage'),payload.assign(record_type='payload')],ignore_index=True)
    export('09_pipeline_cost_and_memory',fig,table,[source/'costs.csv',source/'calibration_costs.csv'],
           'Choosing targets takes computation too. The middle panel measures the complete shared process, while the right panel counts only the statistic input arrays. These are different quantities; the small PSI histogram is not evidence that the full deployed system uses that little memory.')
    pack.close()
    write_json(out/'figure_index.json',figures)
    articles=''.join(f'<article><h2>{r["stem"]}</h2><img src="{r["stem"]}.png" style="max-width:100%"><p>{r["explanation"]}</p><p><a href="{r["stem"]}.csv">Exact source CSV</a> · <a href="{r["stem"]}.pdf">PDF</a> · <a href="{r["stem"]}.svg">SVG</a></p></article>' for r in figures)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>SubPSI Version 4</title><main style="max-width:1400px;margin:3rem auto;font-family:system-ui"><h1>Version 4: sensitivity and matched collection policies</h1><p>Constructed resampling of genuine ACS records and a separate corrected natural OULAD comparison. These are distinct evidence types.</p>'+articles+'</main>')
    write_json(out/'manifest.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        config_sha256=sha256(root/'configs/revision4/approved.json'),map_sha256=frozen['map_sha256'],
        computation_identity_sha256=sha256(raw/'identity.json'),plot_code_sha256=sha256(Path(__file__)),
        git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),environment=environment(),
        files={p.name:sha256(p) for p in out.iterdir() if p.is_file()}))
    print(f'Saved {len(figures)} figures with exact CSV, PNG, PDF and SVG sources.')


if __name__=='__main__':main()

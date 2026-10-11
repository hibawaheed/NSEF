"""Scientific figures with exact plotted CSVs, complete cells and visible limits."""
import argparse
import json
from pathlib import Path
import sys
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import manifest, sha256, write_json, save_snapshot

BLUE='#176B98'; ORANGE='#C46A1A'; INK='#183047'; GRAY='#BBC5CD'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.labelcolor':INK,'text.color':INK,'axes.titleweight':'bold','figure.facecolor':'white',
                     'savefig.facecolor':'white','pdf.fonttype':42,'svg.fonttype':'none'})


def short(group):
    return group.replace('gender=','').replace('disability=','disability ').replace("'",'').replace(' & ',' / ')


class Exporter:
    def __init__(self,out):
        self.out=out;self.entries=[];self.pdf=PdfPages(out/'SubPSI_correction_chart_pack.pdf')
    def save(self,fig,stem,data,title,caption):
        fig.suptitle(title,x=.02,ha='left',fontsize=17,fontweight='bold')
        bottom=max(.16,1.8/fig.get_figheight())
        fig.tight_layout(rect=(.01,bottom,.99,.93))
        fig.text(.025,.025,textwrap.fill(caption,150),fontsize=8.5,va='bottom',color=INK)
        for ext in ['png','pdf','svg']:
            fig.savefig(self.out/f'{stem}.{ext}',dpi=300)
        self.pdf.savefig(fig);plt.close(fig);data.to_csv(self.out/f'{stem}.csv',index=False)
        self.entries.append({'stem':stem,'title':title,'caption':caption,'csv_rows':len(data)})
    def finish(self):
        self.pdf.close()
        write_json(self.out/'figure_index.json',self.entries)
        body=''.join(f'<section><h2>{e["title"]}</h2><img src="{e["stem"]}.svg" alt="{e["title"]}"><p>{e["caption"]}</p><a href="{e["stem"]}.csv">Source CSV</a> · <a href="{e["stem"]}.pdf">Vector PDF</a></section>' for e in self.entries)
        (self.out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>SubPSI correction evidence</title><style>body{font:17px system-ui;max-width:1200px;margin:40px auto;color:#183047}img{width:100%}section{margin:70px 0}p{line-height:1.6}</style><h1>Post-result correction — evidence pack</h1><p>Original versions preserved. Natural observations and mathematical simulations are separate. Final project version remains undecided.</p>'+body)


def natural_figures(e,ou,summary):
    d=pd.read_csv(ou/'bin_counts.csv')
    p=d.query("period=='design_2013J' and group=='Everyone' and feature=='num_of_prev_attempts'")
    fig,axes=plt.subplots(1,2,figsize=(11,6))
    for ax,version,title in zip(axes,['original_v3','corrected'],['Original quantile rule','Corrected count rule']):
        part=p[p.version.eq(version)]
        labels=['below 0','all nonnegative','missing'] if version=='original_v3' else part.label.tolist()
        bars=ax.bar(labels,part['count'],color=GRAY if version=='original_v3' else BLUE)
        ax.bar_label(bars);ax.set_ylim(0,415);ax.set_ylabel('Historical design students');ax.set_title(title)
    e.save(fig,'01_historical_bin_correction',p,'Keep zero, one and multiple attempts distinct',
           'POST-RESULT CORRECTION. Only the 372 historical design records chose the rule: 314 zero, 45 one, 13 two or more. The tail remains sparse. Future larger integers use the same tail. Missing values keep their own bin. This chart explains a measurement fix; it does not show detection accuracy.')
    d=pd.read_csv(ou/'old_vs_corrected.csv').query("variant=='accum100'")
    groups=d.group.drop_duplicates().tolist();y=np.arange(len(groups))
    fig,axes=plt.subplots(2,2,figsize=(13,10))
    for row,feature in enumerate(['num_of_prev_attempts','studied_credits']):
        part=d[d.feature.eq(feature)].set_index('group').loc[groups]
        for col,stat in enumerate(['psi','ks_d']):
            ax=axes[row,col];ax.set_yticks(y,[short(g) for g in groups] if col==0 else ['']*len(groups));ax.invert_yaxis()
            if stat=='psi':
                ax.scatter(part.psi_old,y-.08,color=GRAY,marker='s',label='Original V3',s=45)
                ax.scatter(part.psi_new,y+.08,color=BLUE,label='Corrected',s=45)
            else: ax.scatter(part.ks_d_new,y,color=ORANGE,label='KS unchanged',s=45)
            ax.set_xlim(-.002,.065);ax.grid(axis='x',alpha=.18);ax.set_xlabel('PSI distance' if stat=='psi' else 'KS distance')
            ax.set_title(('Previous attempts' if row==0 else 'Studied credits')+' · '+('PSI' if col==0 else 'KS'))
            for i,r in enumerate(part.itertuples()):
                if not r.eligible_new: ax.text(.001,i,f'not assessed (reference n={r.n_reference_new})',fontsize=8,color='#6C7883',va='center')
            ax.set_ylim(len(groups)-.5,-.5)  # NaNs must not autoscale unsupported rows out of view.
            ax.legend(fontsize=8,loc='upper right')
    e.save(fig,'02_oulad_corrected_distances',d,'OULAD: changed bins, unchanged records and KS',
           'NATURAL OBSERVATIONAL COMPARISON; post-result correction. BBB 2013J reference → 2014J monitoring. Both statistics use exactly the same group records. Minimum support 100; four of nine views qualify. Batch-50, batch-100 and accumulated-100 yield the same supported scores here. PSI and KS have different scales. No drift onset, accuracy, significance or harm is established. The small original attempt PSI came from smoothing unequal sample sizes across empty bins, not separation of attempt counts.')
    o=pd.read_csv(ou/'outcomes.csv');p=o.query("group=='Everyone'")
    fig,axes=plt.subplots(1,3,figsize=(13,6.5))
    for ax,metric in zip(axes,['Accuracy','TPR','FPR']):
        for i,(model,color) in enumerate([('Frozen logistic',BLUE),('Training-majority baseline',ORANGE)]):
            r=p[p.model.eq(model)&p.metric.eq(metric)].iloc[0]
            vals=[r.baseline_rate,r.current_rate];bars=ax.bar(np.arange(2)+(i-.5)*.32,np.array(vals)*100,width=.3,color=color,label=model)
            labels=[f'{r[f"{period}_numerator"]}/{r[f"{period}_denominator"]}\n{r[f"{period}_rate"]:.1%}' for period in ['baseline','current']]
            ax.bar_label(bars,labels=labels,fontsize=8,padding=4)
        ax.set_xticks([0,1],['2013J audit','2014J audit']);ax.set_ylim(0,120);ax.set_ylabel('Percent');ax.set_title(metric+(' (lower is better)' if metric=='FPR' else ''));ax.grid(axis='y',alpha=.12)
    axes[0].legend(fontsize=8,loc='upper left')
    e.save(fig,'03_prediction_baseline',p,'Does the frozen model beat a simple prediction?',
           'DESCRIPTIVE OUTCOME AUDIT. The constant rule is fixed by the 2013J training majority (438 positive of 757); it always predicts Pass/Distinction. On the 973 later audit records, logistic accuracy is 541/973 (55.60%); the simple baseline is 547/973 (56.22%). The logistic model does beat the baseline in the earlier audit. Predicting everyone positive gives both TPR and FPR of 100%. These selected-cohort rates have no claimed population confidence intervals. No classifier tuning was performed.')
    fig,axes=plt.subplots(1,3,figsize=(14,8));groups=o.group.drop_duplicates().tolist()[1:];y=np.arange(len(groups))
    for ax,metric in zip(axes,['Accuracy','TPR','FPR']):
        for i,(model,color) in enumerate([('Frozen logistic',BLUE),('Training-majority baseline',ORANGE)]):
            part=o[o.model.eq(model)&o.metric.eq(metric)&o.group.isin(groups)].set_index('group').loc[groups]
            ax.scatter(part.gap_change*100,y+(i-.5)*.2,color=color,label=model)
            for j,r in enumerate(part.itertuples()):
                if r.gap_status!='assessed': ax.scatter(0,j+(i-.5)*.2,marker='x',color=GRAY)
        ax.axvline(0,color=GRAY,lw=1);ax.invert_yaxis();ax.set_yticks(y,[short(g) for g in groups] if ax==axes[0] else ['']*len(groups));ax.set_title(metric);ax.set_xlabel('Change in group–complement gap (pp)');ax.grid(axis='x',alpha=.15)
    axes[0].legend(fontsize=8)
    e.save(fig,'04_outcome_gaps_with_baseline',o,'OULAD group outcome gaps, with a simple baseline',
           'DESCRIPTIVE, NOT CAUSAL. Each point is (group rate minus complement rate) in 2014J minus the same gap in 2013J. Both models use the same audit students. Gray crosses mean an insufficient relevant denominator (at least 20 is required in all four group/complement-period cells); they are not zero effects. The CSV retains every numerator and denominator, including Everyone. TPR/FPR gaps of an all-positive predictor are zero by construction; this does not establish fairness.')
    d=pd.read_csv(summary/'oulad_input_outcome_pairs.csv');fig,axes=plt.subplots(1,2,figsize=(12,6.8))
    for ax,feature in zip(axes,['num_of_prev_attempts','studied_credits']):
        for model,color,marker in [('Frozen logistic',BLUE,'o'),('Training-majority baseline',ORANGE,'s')]:
            p=d[d.feature.eq(feature)&d.model.eq(model)&d.metric.eq('Accuracy')&d.status.eq('assessed')&d.gap_status.eq('assessed')]
            ax.scatter(p.psi,p.gap_change*100,color=color,marker=marker,label=model)
            for r in p.itertuples():ax.annotate(short(r.group),(r.psi,r.gap_change*100),fontsize=7,xytext=(3,5),textcoords='offset points')
        ax.set_title('Previous attempts' if feature=='num_of_prev_attempts' else 'Studied credits');ax.set_xlabel('Corrected conditional PSI');ax.set_ylabel('Accuracy gap change (pp)');ax.axhline(0,color=GRAY);ax.legend(fontsize=8)
    e.save(fig,'05_input_and_outcome_context',d,'Input changes and outcome gaps answer different questions',
           'NATURAL OULAD ONLY; post-result correction. Points pair monitoring distances with separate labelled audits for matching groups. Only jointly supported subgroup accuracy-gap points are drawn; the CSV keeps all 108 group-feature-metric-model opportunities and their support statuses. Overlapping groups are dependent. No regression, correlation test, causal claim, harm threshold, or drift-detection accuracy is inferred from this small cohort comparison.')


def benchmark_figures(e,summary):
    cells=pd.read_csv(summary/'all_cells.csv');pairs=pd.read_csv(summary/'paired_cells.csv');a=pd.read_csv(summary/'benchmark_aggregate.csv')
    p=cells[cells.id.str.startswith('grid_') & cells.metric.eq('post_alert')]
    fig,axes=plt.subplots(2,2,figsize=(11,9))
    for row,n in enumerate([250,1000]):
        for col,method in enumerate(['PSI','KS']):
            q=p[p.n.eq(n)&p.method.eq(method)].pivot(index='share',columns='magnitude',values='estimate').sort_index()
            ax=axes[row,col];ax.imshow(q.to_numpy(),vmin=0,vmax=1,cmap='Blues',aspect='auto')
            ax.set_xticks(range(3),q.columns);ax.set_yticks(range(4),[f'{s:.0%}' for s in q.index]);ax.set_xlabel('Introduced shift (standard deviations)');ax.set_ylabel('Affected intersection share');ax.set_title(f'Accumulated {method} · batch n={n}')
            for i in range(4):
                for j in range(3):
                    v=q.iloc[i,j];ax.text(j,i,f'{round(v*40)}/40\n{v:.0%}',ha='center',va='center',color='white' if v>.55 else INK)
    e.save(fig,'06_all_original_grid_cells',p,'The full Version 2 grid: matched accumulated PSI and KS',
           'MATHEMATICAL SIMULATIONS; retrospective comparator. Every original grid cell is shown, 40 streams per cell, same seeds and records. Endpoint is any post-onset alert in the full fixed group-feature family, not exact target recovery. Both methods accumulate to 100 using the same whole-batch blocks and standalone horizon budget. Color scale is identical. Source CSV supplies Wilson intervals; paired intervals for every cell are in paired_cells.csv. This is not evidence of natural-world detection accuracy.')
    fig,axes=plt.subplots(1,2,figsize=(12,6.5));plot=a[a.method.isin(['PSI','KS']) & a.metric.isin(['stream_alert','post_alert'])]
    for ax,kind,title in zip(axes,['null','shift'],['Unchanged streams: any alert','Shift grid: any post-onset alert']):
        for j,(method,color) in enumerate([('PSI',BLUE),('KS',ORANGE)]):
            p=plot[plot.kind.eq(kind)&plot.method.eq(method)].sort_values('n');x=np.arange(2)+(j-.5)*.22
            ax.errorbar(x,p.estimate*100,yerr=np.array([p.estimate-p.low,p.high-p.estimate])*100,fmt='o',color=color,capsize=4,label=method)
            for xx,r in zip(x,p.itertuples()):ax.annotate(f'{int(r.successes)}/{r.n_streams}',(xx,r.estimate*100),xytext=(0,12),textcoords='offset points',ha='center',fontsize=9)
        ax.set_xticks([0,1],['batch n=250','batch n=1000']);ax.set_xlim(-.5,1.5);ax.set_ylim(0,18 if kind=='null' else 105);ax.set_title(title);ax.set_ylabel('Percent of complete streams');ax.legend();ax.grid(axis='y',alpha=.15)
        if kind=='null':ax.axhline(5,color=GRAY,ls='--',label='5% design target')
    e.save(fig,'07_matched_detection_and_null_alerts',plot,'Separate detection from false alerts',
           'SYNTHETIC BENCHMARK, not new public records. Null denominators are 250 per batch size, with 95% Wilson intervals. Grid denominators are 480 per batch size: equal weight to all 12 fixed cells, with stratified bootstrap intervals that resample streams within each cell. PSI and KS are paired, standalone methods; their union is not a 5% monitor. Intervals do not certify a universal false-alert rate. The paired contrast is retained in benchmark_aggregate.csv.')
    metrics=['target_ever_assessed','target_detected','target_restricted_delay','eligible_fraction']
    p=cells[cells.id.str.startswith('grid_')&cells.magnitude.eq(1.4)&cells.metric.isin(metrics)]
    fig,axes=plt.subplots(2,2,figsize=(12,9))
    for ax,metric,title in zip(axes.flat,metrics,['Target ever assessed','Exact target alerted after onset','Target restricted mean delay','All-group assessment coverage']):
        for n,style in [(250,'-'),(1000,'--')]:
            for method,color,marker in [('PSI',BLUE,'o'),('KS',ORANGE,'x')]:
                q=p[p.n.eq(n)&p.method.eq(method)&p.metric.eq(metric)].sort_values('share')
                scale=1 if metric=='target_restricted_delay' else 100
                ax.plot(q.share*100,q.estimate*scale,ls=style,color=color,marker=marker,label=f'{method} n={n}')
        ax.set_title(title);ax.set_xlabel('Target share (%)');ax.set_ylabel('Batches after onset; misses=15' if metric=='target_restricted_delay' else 'Percent');ax.grid(alpha=.15);ax.legend(fontsize=8)
    e.save(fig,'08_target_coverage_and_wait',p,'Revisit the original small-group accumulation claim',
           'SYNTHETIC 1.4-SD shift slice used by the existing Version 2 claim, all four original shares and both batch sizes retained. Each point has 40 paired streams. Shared collection means PSI/KS support and waiting are identical, so those curves overlap. Exact-target detection and delay can differ. Delay includes misses at 15 batches; it is not an average only among successes. Full weaker-shift cells and paired intervals remain in the summary CSVs.')
    p=cells[~cells.id.str.startswith(('grid_','null_')) & cells.metric.eq('post_alert')]
    ids=p.id.drop_duplicates().tolist();fig,ax=plt.subplots(figsize=(11,8));y=np.arange(len(ids))
    for j,(method,color) in enumerate([('PSI',BLUE),('KS',ORANGE)]):
        q=p[p.method.eq(method)].set_index('id').loc[ids]
        ax.errorbar(q.estimate*100,y+(j-.5)*.16,xerr=np.array([q.estimate-q.low,q.high-q.estimate])*100,fmt='o',capsize=3,color=color,label=method)
    ax.set_yticks(y,ids);ax.invert_yaxis();ax.set_xlim(-3,105);ax.set_xlabel('Any post-onset input alert (% of 40 streams)');ax.legend();ax.grid(axis='x',alpha=.2)
    e.save(fig,'09_all_robustness_cases',p,'Keep cancellation and every robustness case visible',
           'MATHEMATICAL SIMULATIONS. All 120 cancellation and 240 robustness streams are retained. Bars are 95% Wilson intervals. An input alert is not necessarily successful detection of outcome deterioration: the outcome-only and correlation scenarios do not change the monitored marginal inputs. A benign feature change need not harm the predictor. No new scenarios or algorithms were added in this follow-up.')
    p=cells[cells.metric.isin(['test_seconds','maximum_logical_payload_bytes','shared_input_frame_bytes','maximum_block_age'])]
    fig,axes=plt.subplots(1,2,figsize=(13,12));ids=p.id.drop_duplicates().tolist();y=np.arange(len(ids))
    for ax,metric,title in zip(axes,['test_seconds','maximum_logical_payload_bytes'],['Mean summed statistic time per stream','Mean maximum logical test-input payload']):
        for method,color,marker in [('PSI',BLUE,'o'),('KS',ORANGE,'x')]:
            q=p[p.method.eq(method)&p.metric.eq(metric)].set_index('id').loc[ids]
            ax.scatter(q.estimate,y,color=color,marker=marker,label=method,s=20)
        ax.set_yticks(y,ids if ax==axes[0] else ['']*len(ids),fontsize=6);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlabel('Seconds' if metric=='test_seconds' else 'Bytes');ax.set_title(title);ax.legend();ax.grid(axis='x',alpha=.15)
    e.save(fig,'10_costs_with_scope',p,'Costs on the same observation blocks',
           'ALL 35 ORIGINAL SYNTHETIC CASES. Time includes the statistic implementation, but excludes shared scheduling/input retention and PSI histogram construction. Main execution computes PSI before KS; small timing differences are machine/order dependent. Payload is histogram arrays for PSI versus numeric arrays for KS, not total process memory. The engine retains shared inputs and record-ID bookkeeping. Full-engine wall time and shared peak RSS are in the raw manifest. These are implementation costs, not a universal efficiency claim.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='figures/correction');a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=False)
    ou=ROOT/'results/raw/correction/oulad';summary=ROOT/'results/summary/correction'
    e=Exporter(out);natural_figures(e,ou,summary);benchmark_figures(e,summary);e.finish()
    write_json(out/'manifest.json',{**manifest(ROOT,ROOT/'configs/correction/frozen.json'),
               'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in [ou/'manifest.json',summary/'manifest.json']},
               'source_snapshot_sha256':save_snapshot(ROOT,out),
               'files':{p.name:sha256(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'}})
    print('Exported ten figures in PDF/SVG/PNG with source CSVs and combined PDF.')

if __name__=='__main__':main()

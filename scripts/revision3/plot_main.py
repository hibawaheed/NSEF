"""Publication exports from complete results, with exact CSVs and hash manifests."""
import argparse,html,json,sys,time,textwrap
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import TwoSlopeNorm
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,manifest,write_json,save_snapshot
COLORS={'PSI':'#007c91','KS':'#c26428'}
LABEL={'batch50':'Ordinary ≥50','batch100':'Ordinary ≥100','accum100':'Accumulated ≥100'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.facecolor':'white','axes.titleweight':'bold','pdf.fonttype':42,'svg.fonttype':'none'})


def group_order(frame):return list(dict.fromkeys(frame.group))


def heat(ax,table,title,*,vmin=None,vmax=None,diverging=False,fmt=None):
    a=table.to_numpy(float);cmap=plt.get_cmap('RdBu_r' if diverging else 'viridis').copy();cmap.set_bad('#e3e5e7')
    if diverging:
        limit=max(float(np.nanmax(np.abs(a))) if np.isfinite(a).any() else 0,.01)
        im=ax.imshow(np.ma.masked_invalid(a),aspect='auto',cmap=cmap,vmin=-limit,vmax=limit)
    else:im=ax.imshow(np.ma.masked_invalid(a),aspect='auto',cmap=cmap,vmin=vmin,vmax=vmax)
    ax.set_xticks(range(len(table.columns)),table.columns,rotation=0)
    ax.set_yticks(range(len(table)),table.index,fontsize=8)
    ax.set_title(title,fontsize=11,pad=12)
    for i,j in zip(*np.where(~np.isfinite(a))):ax.text(j,i,'×',ha='center',va='center',color='#62666b',fontsize=8)
    if fmt:
        for i,j in zip(*np.where(np.isfinite(a))):
            rgba=im.cmap(im.norm(a[i,j]));light=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
            ax.text(j,i,format(a[i,j],fmt),ha='center',va='center',fontsize=8,color='black' if light>.55 else 'white')
    return im


class Exporter:
    def __init__(self,out,raw,tables):
        self.out=out;self.raw=raw;self.tables=tables;self.items=[];self.pdf=PdfPages(out/'SubPSI_revision3_chart_pack.pdf');self.start=time.perf_counter()
        self.base=manifest(ROOT,ROOT/'configs/revision3/approved.json')
        self.base.update(raw_manifest_sha256=sha256(raw/'manifest.json'),table_manifest_sha256=sha256(tables/'manifest.json'),
                         plot_code_sha256=sha256(Path(__file__)),source_snapshot_sha256=save_snapshot(ROOT,out))
    def save(self,fig,name,title,data,note):
        fig.suptitle(title,fontsize=16,fontweight='bold',y=.985)
        fig.text(.015,.008,'\n'.join(textwrap.wrap(note,150)),fontsize=9,va='bottom',color='#343b45')
        fig.subplots_adjust(top=.90,bottom=.115)
        data.to_csv(self.out/f'{name}.csv',index=False)
        self.pdf.savefig(fig)
        for suffix in ['png','pdf','svg']:fig.savefig(self.out/f'{name}.{suffix}',dpi=300,facecolor='white')
        self.items.append(dict(name=name,title=title,note=note,rows=len(data)))
        plt.close(fig)
    def finish(self):
        self.pdf.close()
        sections=[]
        for item in self.items:
            n=item['name'];sections.append(f'<section><h2>{html.escape(item["title"])}</h2><img src="{n}.png" alt="{html.escape(item["title"])}"><p>{html.escape(item["note"])}</p><p><a href="{n}.pdf">PDF</a> · <a href="{n}.svg">SVG</a> · <a href="{n}.csv">Exact source CSV</a></p></section>')
        self.out.joinpath('index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SubPSI revision 3 results</title><style>body{font:17px system-ui;max-width:1450px;margin:35px auto;padding:20px;color:#172533;background:#f6f8fa}section{background:white;padding:25px;margin:25px 0;border:1px solid #d9e2eb;border-radius:12px}img{width:100%;height:auto}a{color:#006679}h1{font-size:34px}</style><h1>SubPSI revision 3 — results and chart sources</h1><p>AI-assisted research outputs. Natural observations are descriptive. Constructed controls resample real records and have a deliberately imposed source substitution; their delivery index is not calendar time. No new algorithmic novelty or fairness repair is established.</p><p><a href="SubPSI_revision3_chart_pack.pdf">Download the complete chart pack</a> · <a href="../../../docs/revision3/MAIN_FINDINGS.md">Findings and plain-English guide</a></p>'+''.join(sections)+'</html>')
        self.base.update(status='COMPLETE',charts=self.items,elapsed_seconds=time.perf_counter()-self.start,
                         files={p.name:sha256(p) for p in self.out.iterdir() if p.is_file() and p.name!='manifest.json'})
        write_json(self.out/'manifest.json',self.base)
        print('Exported',len(self.items),'figures with CSV/PDF/SVG/300-dpi PNG and combined PDF.')


def natural_figures(e):
    tests=pd.read_csv(e.raw/'natural_tests.csv');outcomes=pd.read_csv(e.raw/'natural_outcomes.csv')
    for no,dataset,title in [(1,'ACS_MA','ACS Massachusetts: observed input-distribution differences'),(2,'OULAD_BBB','OULAD BBB: observed input-distribution differences')]:
        d=tests.loc[tests.dataset.eq(dataset)&tests.variant.eq('batch100')];groups=group_order(d)
        features=list(dict.fromkeys(d.feature));fig,axs=plt.subplots(1,4,figsize=(17,12 if dataset=='ACS_MA' else 7))
        for ax,(f,stat) in zip(axs,[(f,s) for f in features for s in ['psi','ks_d']]):
            t=d.loc[d.feature.eq(f)].pivot(index='group',columns='time',values=stat).reindex(groups)
            im=heat(ax,t,f'{f} · {"PSI" if stat=="psi" else "KS distance"}',vmin=0,fmt='.3f' if len(groups)<10 else None)
            if ax!=axs[0]:ax.set_yticklabels([])
            fig.colorbar(im,ax=ax,fraction=.046,pad=.04)
        fig.subplots_adjust(left=.17,wspace=.30)
        e.save(fig,f'{no:02d}_natural_{dataset.lower()}',title,d,
               'Natural observations; no known drift onset or detection accuracy. Both methods use the same records and require ≥100 on each side. Gray × = insufficient support. PSI and KS have different units; their color bars are separate. Calendar labels denote actual survey years/cohorts. All declared views are retained.')
    for no,dataset in [(3,'ACS_MA'),(4,'OULAD_BBB')]:
        d=outcomes.loc[outcomes.dataset.eq(dataset)];groups=group_order(d)
        fig,axs=plt.subplots(1,3,figsize=(15,12 if dataset=='ACS_MA' else 7))
        for ax,metric in zip(axs,['TPR','FPR','Accuracy']):
            sub=d.loc[d.metric.eq(metric)].copy();sub['pp']=100*sub.gap_change
            t=sub.pivot(index='group',columns='period',values='pp').reindex(groups)
            im=heat(ax,t,f'Change in {metric} gap (percentage points)',diverging=True,fmt='.1f')
            if ax!=axs[0]:ax.set_yticklabels([])
            fig.colorbar(im,ax=ax,fraction=.046,pad=.04)
        fig.subplots_adjust(left=.20,wspace=.25)
        e.save(fig,f'{no:02d}_outcome_gaps_{dataset.lower()}',f'{dataset}: changes in frozen-model group-versus-complement gaps',d,
               'Descriptive held-out audits, separate from monitored records. Gap = group rate minus its complement; change = later gap minus baseline gap. Positive means the signed gap increased, not necessarily harm. Gray × includes unsupported denominators and the aggregate, which has no complement. Each relevant denominator must be ≥20. CSV includes baseline/current rates, gaps, numerators and denominators; no causal or population inference.')


def alert_figures(e):
    p=pd.read_csv(e.tables/'control_proportions.csv')
    methods=[(v,m) for v in ['batch50','batch100','accum100'] for m in ['PSI','KS']]
    labels=[LABEL[v]+' '+m for v,m in methods]
    for no,scope in [(5,'aggregate'),(6,'single'),(7,'intersection')]:
        cols=[('unchanged','any_alert','Any alert in 20 unchanged blocks'),('substitution','post_alert','Any alert after substitution')]
        if scope=='intersection':cols.append(('substitution','target_post_alert','Exact-target alert after substitution'))
        fig,axs=plt.subplots(2,len(cols),figsize=(16 if len(cols)==3 else 13,8),squeeze=False)
        for row,n in enumerate([250,1000]):
            for col,(condition,metric,title) in enumerate(cols):
                ax=axs[row,col];d=p.loc[p.scope.eq(scope)&p.batch_n.eq(n)&p.condition.eq(condition)&p.metric.eq(metric)]
                for i,(v,m) in enumerate(methods):
                    r=d.loc[d.variant.eq(v)&d.method.eq(m)].iloc[0]
                    ax.errorbar(r.estimate,i,xerr=[[r.estimate-r.low],[r.high-r.estimate]],fmt='o',color=COLORS[m],capsize=3)
                    ax.text(.99,i,f'{int(r.successes)}/30',ha='right',va='center',fontsize=9,transform=ax.get_yaxis_transform())
                ax.set_xlim(-.025,1.05);ax.set_ylim(5.7,-.7);ax.set_yticks(range(6),labels if col==0 else ['']*6)
                ax.set_title(f'{title}\n{n:,} records per delivery block',fontsize=10);ax.set_xlabel('Proportion of complete streams');ax.grid(axis='x',alpha=.2)
        fig.subplots_adjust(left=.19,hspace=.48,wspace=.2)
        e.save(fig,f'{no:02d}_controls_{scope}',f'Constructed controls · {scope} scope · matched PSI and KS',p.loc[p.scope.eq(scope)],
               '30 paired streams per cell; points and 95% Wilson intervals. Source substitution begins at delivery block 6 and may cause only a small feature-distribution difference. Natural drift accuracy is not measured. Each standalone method has alpha .05 over 20 looks; scopes are separate comparisons. Zero observed events does not establish zero risk. Exact-target recovery is defined only for the intersection scope. CSV also retains pre-intervention alerts.')


def collection_figure(e):
    d=pd.read_csv(e.tables/'control_group_coverage.csv');x=d.loc[d.condition.eq('unchanged')].copy()
    # Group membership is identical in paired unchanged/substitution streams.
    a=x.sort_values(['batch_n','repeat','variant','group']).coverage.to_numpy()
    b=d.loc[d.condition.eq('substitution')].sort_values(['batch_n','repeat','variant','group']).coverage.to_numpy()
    if not np.array_equal(a,b):raise ValueError('Paired condition coverage changed unexpectedly')
    x['setting']=x.batch_n.astype(str)+' / '+x.variant
    settings=[f'{n} / {v}' for n in [250,1000] for v in ['batch50','batch100','accum100']]
    # Use declared source order from natural source table for consistent reading.
    groups=group_order(pd.read_csv(e.raw/'natural_tests.csv').query("dataset == 'ACS_MA'"))
    fig,axs=plt.subplots(1,3,figsize=(19,13))
    for ax,metric,title in zip(axs,['coverage','first_assessment_restricted','maximum_age_when_assessed'],
                              ['Fraction of looks assessable','First assessment look (21 = missed)','Oldest age in tested block (delivery blocks)']):
        table=x.groupby(['group','setting'])[metric].mean().unstack().reindex(index=groups,columns=settings)
        im=heat(ax,table,title,vmin=0,fmt='.2f' if metric=='coverage' else '.1f')
        ax.set_xticklabels([s.replace(' / ','\n') for s in settings],fontsize=8)
        if ax!=axs[0]:ax.set_yticklabels([])
        fig.colorbar(im,ax=ax,fraction=.046,pad=.03)
    fig.subplots_adjust(left=.16,wspace=.25)
    e.save(fig,'08_collection_support_wait_age','Collection: coverage, waiting and record age for every declared group',d,
           'Means across 30 unchanged conditional streams. Paired substitution streams have identical group membership and coverage; both conditions are included in the CSV. PSI and KS share one scheduler, so their coverage is exactly identical. Waiting summaries assign 21 to streams never assessed by look 20. Gray × in age means no assessed block; it does not mean fresh records. Ages are constructed delivery blocks, not calendar time.')


def delay_figure(e):
    d=pd.read_csv(e.raw/'control_stream_metrics.csv');s=d.loc[d.condition.eq('substitution')&d.scope.eq('intersection')]
    methods=[(v,m) for v in ['batch50','batch100','accum100'] for m in ['PSI','KS']]
    fig,axs=plt.subplots(2,2,figsize=(14,9))
    for i,n in enumerate([250,1000]):
        for j,metric in enumerate(['restricted_delay','target_restricted_delay']):
            ax=axs[i,j]
            for k,(v,m) in enumerate(methods):
                vals=s.loc[s.batch_n.eq(n)&s.variant.eq(v)&s.method.eq(m)].sort_values('repeat')[metric].to_numpy()
                jitter=np.linspace(-.19,.19,len(vals))
                ax.scatter(vals,k+jitter,s=15,color=COLORS[m],alpha=.65)
                ax.plot(vals.mean(),k,'D',color='black',markersize=5)
            ax.axvline(15,color='#9a3445',ls='--',lw=1);ax.set_xlim(-.6,15.8);ax.set_xticks([0,3,6,9,12,15],['0','3','6','9','12','Missed\n(15)'])
            ax.set_yticks(range(6),[LABEL[v]+' '+m for v,m in methods] if j==0 else ['']*6)
            ax.invert_yaxis();ax.set_xlabel('Delivery blocks after intervention');ax.set_title(f'{n:,} per block · '+('any post-intervention alert' if j==0 else 'exact-target alert'),fontsize=11)
    fig.subplots_adjust(left=.20,hspace=.5,wspace=.15)
    e.save(fig,'09_restricted_delay','Constructed intervention: delays with every missed recovery retained',d,
           'Intersection scope; 30 points per method/setting. Black diamond = mean restricted delay. An alert at block 6 has delay 0; no alert during blocks 6–20 is retained at 15, not dropped. Any-view recovery may be unrelated to the target; the right panels require an alert in SEX=2 & RAC1P=2. Zero alerts is a result, not evidence that the implementation is accurate.')


def cost_figure(e):
    d=pd.read_csv(e.raw/'alternating_kernel_benchmark.csv');d['case']=d.batch_n.astype(str)+' / '+np.where(d.group.eq('Everyone'),'all','target')+' / '+d.feature
    cases=list(dict.fromkeys(d['case']));fig,axs=plt.subplots(1,3,figsize=(17,8))
    metrics=[('kernel_seconds','Statistic kernel runtime (ms)',1000),('logical_payload_bytes','Logical input payload (bytes)',1),('peak_kernel_allocation_bytes','Measured temporary allocation peak (bytes)',1)]
    for ax,(metric,title,factor) in zip(axs,metrics):
        for off,method in [(-.18,'PSI'),(.18,'KS')]:
            vals=d.loc[d.method.eq(method)].groupby('case',sort=False)[metric].median().reindex(cases)*factor
            ax.barh(np.arange(len(cases))+off,vals,.34,label=method,color=COLORS[method])
        ax.set_xscale('log');ax.set_yticks(range(len(cases)),cases if ax==axs[0] else ['']*len(cases));ax.invert_yaxis();ax.set_title(title,fontsize=11);ax.legend();ax.grid(axis='x',alpha=.2)
    m=json.loads((e.raw/'manifest.json').read_text());fig.subplots_adjust(left=.16,wspace=.2)
    e.save(fig,'10_runtime_and_memory','Cost comparison on identical, prespecified real-record blocks',d,
           f'Medians of five repeats; timing order alternates. Allocation profiling is separate from native timing. PSI histogram construction and shared scheduling are additional costs. These null-block benchmarks use conservative early stopping and do not characterize every alternative. Whole offline study high-water RSS = {m["process_high_water_rss_kib"]/1024:.1f} MiB, including retained frames/IDs. Histogram payload is not total monitor memory. Full engine timings are retained separately.')


def agreement_figure(e):
    d=pd.read_csv(e.tables/'input_outcome_pairs.csv');features=[('ACS_MA','AGEP'),('ACS_MA','SCHL'),('OULAD_BBB','num_of_prev_attempts'),('OULAD_BBB','studied_credits')]
    fig,axs=plt.subplots(4,3,figsize=(15,15))
    for i,(dataset,feature) in enumerate(features):
        for j,metric in enumerate(['TPR','FPR','Accuracy']):
            ax=axs[i,j];cell=d.loc[d.dataset.eq(dataset)&d.feature.eq(feature)&d.metric.eq(metric)];valid=cell.loc[cell.pair_status.eq('descriptive_pair')]
            for period,sub in valid.groupby('period'):ax.scatter(sub.psi,100*sub.gap_change,label=str(period),s=25,alpha=.7)
            ax.axhline(0,color='gray',lw=.8);ax.set_xlabel(f'{feature} PSI');ax.set_ylabel(f'Change in {metric} gap (pp)');ax.set_title(f'{dataset} · {metric}\n{len(valid)}/{len(cell)} pairs assessable',fontsize=10)
            if i==0 and j==0:ax.legend(title='Survey year',fontsize=8)
    fig.subplots_adjust(left=.07,wspace=.35,hspace=.65)
    e.save(fig,'11_input_outcome_pairs','Input differences and outcome-gap changes answer different questions',d,
           'Every assessable declared group/period is shown, including negative and near-zero changes; unsupported and aggregate-without-complement rows remain in CSV. Each point pairs a descriptive input score with a separate held-out outcome audit. There is no fitted relationship, significance claim or causal interpretation. Repeated groups/years are dependent. All two-feature × three-metric combinations are shown; no association was selected for appearance.')


def paired_figure(e):
    d=pd.read_csv(e.tables/'paired_differences.csv');s=d.loc[d.scope.eq('intersection')]
    cases=[('unchanged','any_alert','PSI minus KS','PSI − KS: whole-stream null alerts'),('substitution','target_post_alert','PSI minus KS','PSI − KS: exact-target recovery'),
           ('unchanged','coverage','accum100 minus batch100','Accumulation − ordinary ≥100: coverage'),('substitution','target_post_alert','accum100 minus batch100','Accumulation − ordinary ≥100: target recovery')]
    fig,axs=plt.subplots(2,2,figsize=(15,10))
    for ax,(condition,metric,pattern,title) in zip(axs.flat,cases):
        x=s.loc[s.condition.eq(condition)&s.metric.eq(metric)&s.contrast.str.contains(pattern,regex=False)].copy()
        x=x.sort_values(['batch_n','contrast']);labels=[]
        for y,(_,r) in enumerate(x.iterrows()):
            ax.errorbar(r.difference,y,xerr=[[r.difference-r.low],[r.high-r.difference]],fmt='D' if r.degenerate else 'o',color='#006c7a',capsize=3)
            labels.append(f'{r.batch_n} / '+r.contrast.replace(': PSI minus KS','').replace(': accum100 minus batch100',''))
        ax.set_yticks(range(len(x)),labels,fontsize=9);ax.invert_yaxis();ax.axvline(0,color='gray',lw=1)
        lo=min(-.025,float(x.low.min())-.03);hi=max(.025,float(x.high.max())+.03);ax.set_xlim(lo,hi)
        ax.set_xlabel('Paired difference in proportions');ax.set_title(title,fontsize=10);ax.grid(axis='x',alpha=.2)
    fig.subplots_adjust(left=.12,wspace=.36,hspace=.5)
    e.save(fig,'12_paired_comparisons','Paired comparisons preserve ties and uncertainty',d,
           '2,000 bootstrap resamples of 30 complete paired conditional streams per cell. Diamonds flag degenerate intervals (for example every pair tied); they do not prove equivalence or superiority. Full tables also retain the ordinary ≥50 comparison and all scopes. The finite source pools and small number of repeats limit generalization; no natural detection-accuracy interval is claimed.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--tables',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    raw=ROOT/a.raw;tables=ROOT/a.tables;out=ROOT/a.out
    for directory in [raw,tables]:
        m=json.loads((directory/'manifest.json').read_text())
        if m['status']!='COMPLETE':raise ValueError('Incomplete input')
        for n,h in m['files'].items():
            if sha256(directory/n)!=h:raise ValueError('Input hash mismatch '+n)
    out.mkdir(parents=True,exist_ok=False);e=Exporter(out,raw,tables)
    natural_figures(e);alert_figures(e);collection_figure(e);delay_figure(e);cost_figure(e);agreement_figure(e);paired_figure(e);e.finish()
if __name__=='__main__':main()

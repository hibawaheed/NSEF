#!/usr/bin/env python3
"""Publication exports from immutable revision-2 stream summaries."""
import gzip,json,sys,textwrap
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import PercentFormatter
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,write_json
from subpsi.revision import GROUP_NAMES
OUT=ROOT/'figures/revision2';OUT.mkdir(parents=True,exist_ok=True)
D=pd.read_csv(ROOT/'results/revision2/streams.csv',keep_default_na=False,na_values=['']);O=pd.read_csv(ROOT/'results/revision2/outcomes.csv',keep_default_na=False,na_values=[''])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243449','text.color':'#17283c','axes.titlesize':12,'axes.titleweight':'bold','pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
COL={'Overall PSI':'#3268ce','Intersection PSI':'#d35727','Overall KS':'#75a5dc','Intersection KS':'#39816e','Accumulated PSI':'#7959b7','Per-batch PSI':'#939cac','Fixed PSI 0.1':'#c3b8ac','Outcome audit':'#16778d','Combined monitor':'#9a485c'}
MAIN=['Overall PSI','Intersection PSI','Intersection KS','Accumulated PSI'];ALL=list(COL)
figures=[];pdf=PdfPages(OUT/'SubPSI_revision2.pdf')

def interval(k,n):
    p=k/n;z=1.959963984540054;center=(p+z*z/(2*n))/(1+z*z/n);half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return max(0,min(p,center-half)),min(1,max(p,center+half))

def rate(frame,col):
    if len(frame)==0: raise ValueError(f'Empty figure selection for {col}')
    n=len(frame);k=int(frame[col].sum());lo,hi=interval(k,n);return {'rate':k/n,'low':lo,'high':hi,'events':k,'runs':n}

def save(fig,name,title,caption,rows,kind='Empirical · controlled evaluation'):
    fig.suptitle(title,x=.055,y=.985,ha='left',fontsize=19,weight='bold')
    fig.text(.055,.11,'\n'.join(textwrap.wrap(caption,145)),ha='left',va='top',fontsize=9,color='#526170')
    fig.text(.055,.013,'SubPSI · Revision 2 · AI-assisted implementation and figure production · source tables and settings accompany every figure',fontsize=8,color='#687483')
    fig.savefig(OUT/f'{name}.png',dpi=300);fig.savefig(OUT/f'{name}.svg');fig.savefig(OUT/f'{name}.pdf');pdf.savefig(fig);plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False)
    write_json(OUT/f'{name}.manifest.json',{'title':title,'caption':caption,'kind':kind,'source_summary_sha256':sha256(ROOT/'results/revision2/streams.csv'),'outcome_summary_sha256':sha256(ROOT/'results/revision2/outcomes.csv'),'config_sha256':sha256(ROOT/'configs/revision2.json'),'csv_sha256':sha256(OUT/f'{name}.csv'),'formats':{ext:sha256(OUT/f'{name}.{ext}') for ext in ['png','svg','pdf']}})
    figures.append({'name':name,'title':title,'caption':caption,'kind':kind})

def axesgrid(rows=1,cols=1,**kwargs):
    fig,axs=plt.subplots(rows,cols,figsize=(13.3,8.1),squeeze=False,**kwargs);fig.subplots_adjust(left=.08,right=.97,top=.87,bottom=.22,wspace=.32,hspace=.5);return fig,axs

# 1 — Whole-stream false alarms, including two intentionally uncontrolled ablations.
fig,axs=axesgrid(1,2);fig.subplots_adjust(left=.17,wspace=.72);rows=[]
for ax,n in zip(axs[0],[250,1000]):
    for i,m in enumerate(ALL):
        r=rate(D[(D.kind=='null')&(D.n==n)&(D.method==m)],'stream_alert');rows.append({'batch_size':n,'method':m,**r})
        ax.errorbar(r['rate']*100,i,xerr=[[100*(r['rate']-r['low'])],[100*(r['high']-r['rate'])]],fmt='o',color=COL[m],capsize=3)
    ax.set_yticks(range(len(ALL)),ALL);ax.invert_yaxis();ax.axvline(5,color='#222',ls='--',lw=1);ax.set_xlim(-1,105);ax.set_xlabel('Streams with ≥1 false alert (%)');ax.set_title(f'{n:,} records per batch · 250 streams');ax.grid(axis='x',alpha=.15)
save(fig,'01_stream_false_alarms','Does a 20-batch monitoring run raise a false alarm?',
     'No introduced change. Points show observed proportions; bars show 95% Wilson intervals. Dashed line: 5% target. Per-batch PSI and fixed PSI 0.1 are ablations without horizon control. Outcome and combined monitors include labels.',rows)
# 2 — Heatmap any drift alert for all declared grid cells.
fig,axs=axesgrid(2,3);rows=[];methods=['Overall PSI','Intersection PSI','Accumulated PSI'];shares=[.02,.05,.1,.25];mags=[.35,.7,1.4]
for ii,n in enumerate([250,1000]):
 for jj,m in enumerate(methods):
    ax=axs[ii,jj];a=np.zeros((4,3))
    for i,s in enumerate(shares):
     for j,mag in enumerate(mags):
        sub=D[(D.kind=='shift')&(D.n==n)&(D.share==s)&(D.magnitude==mag)&(D.method==m)];r=rate(sub,'post_alert');a[i,j]=r['rate'];rows.append({'batch_size':n,'share':s,'magnitude':mag,'method':m,**r})
    im=ax.imshow(a,vmin=0,vmax=1,cmap='Blues',aspect='auto')
    for i in range(4):
     for j in range(3):ax.text(j,i,f'{a[i,j]*100:.0f}%',ha='center',va='center',color='white' if a[i,j]>.55 else '#17283c')
    ax.set_xticks(range(3),mags);ax.set_yticks(range(4),['2%','5%','10%','25%']);ax.set_xlabel('Shift / baseline SD');ax.set_ylabel('Affected intersection share');ax.set_title(f'{m} · batch n={n:,}')
save(fig,'02_detection_map','Where does input-drift monitoring work?',
     'Forty independent streams per cell; color is the probability of any alert during 15 post-change batches. A=1,B=1 alone shifts. Zero can reflect inadequate subgroup counts, weak effects, or the error-control cost. Cell intervals are in the source CSV.',rows)
# 3 — Paired comparison with KS, no cherry-picked subset.
fig,axs=axesgrid(1,2);fig.subplots_adjust(left=.16,wspace=.75);rows=[];rng=np.random.default_rng(88217)
for ax,n in zip(axs[0],[250,1000]):
    labels=[]
    for i,(share,mag) in enumerate((s,m) for s in shares for m in mags):
        f=D[(D.kind=='shift')&(D.n==n)&(D.share==share)&(D.magnitude==mag)].pivot(index='run',columns='method',values='post_alert')
        delta=f['Intersection PSI'].astype(float).to_numpy()-f['Intersection KS'].astype(float).to_numpy();bs=rng.choice(delta,(5000,len(delta))).mean(axis=1);lo,hi=np.quantile(bs,[.025,.975]);mean=delta.mean();rows.append({'n':n,'share':share,'magnitude':mag,'difference':mean,'low':lo,'high':hi,'pairs':len(delta)})
        ax.errorbar(mean*100,i,xerr=[[100*(mean-lo)],[100*(hi-mean)]],fmt='o',color='#d35727',capsize=3);labels.append(f'{share:.0%} group · {mag:g} SD')
    ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.axvline(0,color='#555',lw=1);ax.set_xlim(-105,105);ax.grid(axis='x',alpha=.15);ax.set_title(f'Batch n={n:,}');ax.set_xlabel('PSI detection minus KS detection (percentage points)')
save(fig,'03_psi_vs_ks','Does PSI add value beyond subgrouping?',
     'Paired complete streams; both methods use the same groups and a 5% horizon budget. Percentile bootstrap intervals use 5,000 paired resamples. Positive favors PSI; negative favors KS. Degenerate intervals at identical paired outcomes do not prove population equality.',rows)
# 4 — Support and restricted target delay, not just favorable detections.
fig,axs=axesgrid(1,2);rows=[]
for m in ['Intersection PSI','Accumulated PSI']:
    for i,s in enumerate(shares):
        f=D[(D.kind=='shift')&(D.n==250)&(D.share==s)&(D.magnitude==1.4)&(D.method==m)]
        r=rate(f,'target_ever_assessed');rr=rate(f,'target_detected');delay=f.target_delay.fillna(15).to_numpy();mean=delay.mean();se=delay.std(ddof=1)/np.sqrt(len(delay));lo=max(0,mean-t.ppf(.975,len(delay)-1)*se);hi=min(15,mean+t.ppf(.975,len(delay)-1)*se)
        offset=-.06 if m=='Intersection PSI' else .06
        axs[0,0].errorbar(i+offset,r['rate']*100,yerr=[[100*(r['rate']-r['low'])],[100*(r['high']-r['rate'])]],fmt='o',color=COL[m],capsize=3,label=m if i==0 else None)
        axs[0,1].errorbar(i+offset,mean,yerr=[[mean-lo],[hi-mean]],fmt='o',color=COL[m],capsize=3,label=m if i==0 else None)
        rows.append({'method':m,'share':s,'coverage':r['rate'],'coverage_low':r['low'],'coverage_high':r['high'],'target_detection':rr['rate'],'target_detection_low':rr['low'],'target_detection_high':rr['high'],'restricted_target_delay':mean,'delay_low':lo,'delay_high':hi,'runs':len(f)})
for ax in axs[0]:ax.set_xticks(range(4),['2%','5%','10%','25%']);ax.set_xlabel('Affected intersection share');ax.grid(axis='y',alpha=.15)
axs[0,0].set_ylabel('Streams assessing the target at least once (%)');axs[0,0].set_ylim(-5,105);axs[0,0].set_title('Coverage after the change');axs[0,0].legend(loc='lower right',fontsize=9)
axs[0,1].set_ylabel('Restricted target delay (batches)');axs[0,1].set_ylim(-.5,15.8);axs[0,1].set_title('Delay includes missed target changes');axs[0,1].axhline(15,ls='--',lw=1,color='#999')
save(fig,'04_coverage_delay','More small-group coverage can come with a delay',
     'Batch n=250, shift=1.4 SD; 40 streams per share. Ordinary tests require 50 records per batch; accumulation requires 100 per block. Undetected targets are assigned the 15-batch horizon, not dropped. Delay intervals describe a restricted mean; coverage uses Wilson intervals.',rows)
# 5 — Imperfect cancellation.
fig,axs=axesgrid();ax=axs[0,0];rows=[]
for j,m in enumerate(MAIN):
    means=[];los=[];his=[]
    for cancel in [0,.5,1]:
        f=D[(D.kind=='cancellation')&(D.cancel==cancel)&(D.method==m)];r=rate(f,'post_alert');means.append(r['rate']*100);los.append((r['rate']-r['low'])*100);his.append((r['high']-r['rate'])*100);rows.append({'cancellation':cancel,'method':m,**r})
    ax.errorbar(np.array([0,.5,1])+(j-1.5)*.018,means,yerr=[los,his],marker=['o','s','^','D'][j],capsize=4,color=COL[m],label=m)
ax.set_xticks([0,.5,1],['No opposing shift','Half opposing shift','Exact mean swap']);ax.set_ylim(-5,108);ax.set_ylabel('Post-change streams with an alert (%)');ax.set_title('Equal-size intersections · batch n=1,000');ax.legend(loc='lower left');ax.grid(alpha=.15)
save(fig,'05_cancellation','How much does the cancellation example matter?',
     'Forty streams per condition; 95% Wilson intervals. Only the full swap preserves aggregate and single-attribute input distributions exactly. Aggregate alerts there are false alarms. Points are offset horizontally to expose overlap; lines only guide the eye.',rows)
# 6 — Input versus outcome detections.
fig,axs=axesgrid();ax=axs[0,0];rows=[];kinds=['null','benign','outcome','correlation','gradual','missing'];names=['No change','Unused feature shifts','Outcomes change only','Correlation changes only','Gradual input shift','Missingness increases'];methods=['Intersection PSI','Outcome audit','Combined monitor'];width=.23
for j,m in enumerate(methods):
 vals=[];low=[];high=[]
 for k in kinds:
    f=D[(D.kind==k)&(D.method==m)];f=f[f.n==1000] if k=='null' else f;r=rate(f,'post_alert');vals.append(r['rate']*100);low.append((r['rate']-r['low'])*100);high.append((r['high']-r['rate'])*100);rows.append({'scenario':k,'method':m,**r})
 ax.bar(np.arange(len(kinds))+(j-1)*width,vals,width,color=COL[m],label=m,yerr=[low,high],capsize=3)
ax.set_xticks(range(len(kinds)),['\n'.join(textwrap.wrap(s,19)) for s in names]);ax.set_ylabel('Post-change streams with an alert (%)');ax.set_ylim(0,110);ax.legend(loc='upper left',bbox_to_anchor=(0,1.13),ncol=3);ax.grid(axis='y',alpha=.15)
save(fig,'06_input_and_outcome','Input change and prediction deterioration are different signals',
     '250 no-change streams; 40 per other scenario. Outcome audits test TPR decrease, FPR increase and accuracy decrease even when input checks are quiet; labels arrive immediately. The combined monitor splits its 5% budget between channels. 95% Wilson intervals; no universal fairness verdict.',rows)
# 7 — Intersection outcomes, paired differences.
fig,axs=axesgrid(1,2);rows=[]
for ax,case,title in zip(axs[0],['cancel_1','outcome'],['Exact cancellation','Outcome-only change']):
    for j,metric in enumerate(['TPR','FPR','Accuracy']):
        for g in range(9):
            f=O[(O.case==case)&(O.group==g)&(O.metric==metric)].dropna(subset=['change']);v=f.change.to_numpy();mean=v.mean()*100;half=t.ppf(.975,len(v)-1)*v.std(ddof=1)/np.sqrt(len(v))*100
            ax.errorbar(mean,g+(j-1)*.2,xerr=half,fmt='o',markersize=4,capsize=2,color=['#3268ce','#d35727','#39816e'][j],label=metric if g==0 else None);rows.append({'case':case,'group':GROUP_NAMES[g],'metric':metric,'mean_change_pp':mean,'low':mean-half,'high':mean+half,'runs':len(v),'minimum_label_denominator':f.minimum_current_denominator.min()})
    ax.set_yticks(range(9),GROUP_NAMES);ax.invert_yaxis();ax.axvline(0,color='#555',lw=1);ax.set_xlim(-100,100);ax.set_title(title);ax.set_xlabel('Post-change minus baseline (percentage points)');ax.grid(axis='x',alpha=.15)
fig.subplots_adjust(left=.12,wspace=.45,top=.83)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.935),ncol=3,fontsize=9)
save(fig,'07_group_outcomes','Check what happened to predictions inside each group',
     'Average the 15 post-change batches within each stream, then estimate paired mean changes over 40 independent streams; bars are 95% t intervals, not simultaneous intervals. TPR: actual positives correctly predicted; FPR: actual negatives incorrectly predicted positive. Small denominators remain in the source table.',rows)
# 8 — Public data conditional by split, not pooled as independent people.
fig,axs=axesgrid(1,2);fig.subplots_adjust(left=.15,wspace=.68);rows=[];methods=['Overall PSI','Intersection PSI','Intersection KS','Accumulated PSI','Outcome audit','Combined monitor'];splits=sorted(D[D.kind=='public_null'].split.unique())
for ax,k,title in zip(axs[0],['public_null','public_tilt'],['Unchanged sampling','Introduced working-hours sampling shift']):
 for j,split in enumerate(splits):
    for i,m in enumerate(methods):
        f=D[(D.kind==k)&(D.split==split)&(D.method==m)];r=rate(f,'stream_alert' if k=='public_null' else 'post_alert');ax.errorbar(r['rate']*100,i+(j-1)*.18,xerr=[[100*(r['rate']-r['low'])],[100*(r['high']-r['rate'])]],fmt=['o','s','^'][j],markersize=4,capsize=2,color=COL[m]);rows.append({'split':int(split),'condition':k,'method':m,**r})
 ax.set_yticks(range(len(methods)),methods);ax.invert_yaxis();ax.set_xlim(-5,108);ax.set_xlabel('Streams with an alert (%)');ax.set_title(title);ax.grid(axis='x',alpha=.15)
save(fig,'08_public_data','Does the result persist across public-data splits?',
     'UCI Adult (Becker & Kohavi, CC BY 4.0): 20 repeats per condition within each of three fixed role splits. Markers distinguish splits; 95% Wilson intervals are conditional resampling uncertainty. This is an injected sampling shift, not observed chronological drift or new independent populations.',rows)
# 9 — Detection/false-alarm tradeoff rather than a fabricated ROC.
fig,axs=axesgrid(1,2);rows=[]
for ax,n in zip(axs[0],[250,1000]):
 for m in ['Overall PSI','Intersection PSI','Intersection KS','Accumulated PSI','Per-batch PSI','Fixed PSI 0.1']:
    nr=rate(D[(D.kind=='null')&(D.n==n)&(D.method==m)],'stream_alert');ds=D[(D.kind=='shift')&(D.n==n)&(D.method==m)];r=rate(ds,'post_alert')
    # Balanced mix is an explicitly defined benchmark summary, not a deployment prevalence.
    ax.scatter(nr['rate']*100,r['rate']*100,color=COL[m],s=55,label=m);rows.append({'n':n,'method':m,'null_rate':nr['rate'],'null_low':nr['low'],'null_high':nr['high'],'balanced_grid_detection':r['rate'],'grid_runs':len(ds),'null_runs':nr['runs']})
 ax.axvline(5,color='#555',ls='--',lw=1);ax.set_xlim(-3,103);ax.set_ylim(-5,105);ax.set_xlabel('Any false alert in 20 unchanged batches (%)');ax.set_ylabel('Detection across balanced shift grid (%)');ax.set_title(f'Batch n={n:,}');ax.grid(alpha=.15)
fig.subplots_adjust(top=.81)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.935),ncol=3,fontsize=9)
save(fig,'09_operating_tradeoff','A high alert rate is useful only with a low false-alarm cost',
     'Each point is one fixed method, not a threshold-swept ROC curve. Detection averages the 12 equally weighted group-share/shift cells at the stated batch size (480 streams); false alarms use 250 null streams. Real-world case frequencies may differ. Point overlap is possible; all values are in the CSV.',rows)
# 10 — A transparent single-run illustration, distinct from rate evidence above.
fig,axs=axesgrid(1,2);rows=[]
for ax,case,title in zip(axs[0],['cancel_1','gradual'],['Exact cancellation','Gradual target shift']):
    source=ROOT/'results/raw/revision2'/f'{case}_0000.json.gz'
    with gzip.open(source,'rt') as f:r=json.load(f)
    ax.axvspan(5.5,20.5,color='#eaf0f7',zorder=0);ax.axvline(5.5,ls='--',color='#738299',lw=1)
    for g,m,label in [(0,'Overall PSI','Overall population'),(8,'Intersection PSI','Intersection A=1, B=1')]:
        ts=[v for v in r['tests'] if v['policy']=='batch' and v['feature']=='x' and v['group']==g]
        alerts={v['window']:g in v['hits'] for v in r['decisions'] if v['method']==m}
        ax.plot([v['window'] for v in ts],[v['psi'] for v in ts],color=COL[m],label=label)
        for v in ts:
            hit=alerts[v['window']];ax.scatter(v['window'],v['psi'],s=25,edgecolor=COL[m],facecolor=COL[m] if hit else 'white',zorder=3)
            rows.append({'case':case,'repeat':0,'window':v['window'],'group':label,'psi':v['psi'],'corrected_alert':hit,'reference_n':v['n_reference'],'current_n':v['n_current'],'raw_file':str(source.relative_to(ROOT)),'raw_sha256':sha256(source)})
    ax.set_xlim(.5,20.5);ax.set_xticks([1,5,10,15,20]);ax.set_ylim(bottom=0);ax.set_xlabel('Batch number');ax.set_ylabel('Population Stability Index (PSI)');ax.set_title(title);ax.grid(axis='y',alpha=.15)
fig.subplots_adjust(top=.81)
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.935),ncol=2,fontsize=9)
save(fig,'10_drift_over_time','Watch a hidden shift appear over time',
     'First saved repeat (0) from each named scenario, selected by index rather than outcome. Shading begins at the batch-6 intervention. Filled markers: corrected alerts; hollow: no alert. These are two illustrative trajectories, not detection-rate estimates. Panel y-scales differ; all observations are generated.',rows,kind='Illustration · two saved generated streams')
pdf.close();write_json(OUT/'index.json',{'figures':figures,'summary':'Revision 2: 1,820 synthetic streams and 120 conditional Adult streams; 20 batches per stream. Accumulation improved detection in the fixed grid; PSI did not outperform KS overall. Input drift alone did not establish prediction harm or fairness. Methods, uncertainty and failures remain visible.','chart_pack_sha256':sha256(OUT/'SubPSI_revision2.pdf')})
print('Saved',len(figures),'figures and PDF',flush=True)

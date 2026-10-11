#!/usr/bin/env python3
"""Generate figures only from hash-verified saved runs; export source tables."""
import argparse,json,sys,hashlib,math,html
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256,verify_inputs,write_json,environment
from subpsi.scenarios import SCENARIOS
from subpsi.core import psi_probabilities

METHODS=['A0','A1','B0','B1','B2']
LABELS={'A0':'Aggregate / PSI ≥0.1','A1':'Aggregate / Holm','B0':'All subgroups / PSI ≥0.1','B1':'Single attributes / Holm','B2':'Intersections + singles / Holm'}
COLORS=dict(zip(METHODS,plt.rcParams['axes.prop_cycle'].by_key()['color'][:5]))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':17,'axes.labelsize':12,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130,'savefig.dpi':300,'pdf.fonttype':42,'svg.fonttype':'none'})


def wilson(values):
    x=np.asarray(values,float); n=len(x)
    if not n: raise ValueError('No successful runs')
    k=int(x.sum()); p=k/n; z=1.959963984540054; den=1+z*z/n
    center=(p+z*z/(2*n))/den; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {'estimate':p,'low':0.0 if k==0 else min(p,max(0,center-half)),'high':1.0 if k==n else max(p,min(1,center+half)),'n':n,'k':k,'interval':'95% Wilson, independent run-level indicators (conditional on fixed Adult pool where applicable)'}


def mean_interval(values):
    x=np.asarray([v for v in values if v is not None],float); n=len(x)
    if not n: raise ValueError('No estimable values')
    mean=float(x.mean()); half=float(t.ppf(.975,n-1)*x.std(ddof=1)/np.sqrt(n)) if n>1 else 0
    return {'estimate':mean,'low':mean-half,'high':mean+half,'n':n,'interval':'95% Student t across independent run summaries; descriptive pointwise interval'}


def load_runs(path):
    meta=json.loads((path/'manifest.json').read_text())
    verify_inputs(path,meta['result_hashes']); verify_inputs(path,{'config.json':meta['config_saved_sha256']})
    verify_inputs(path,meta.get('support_hashes',{}))
    verify_inputs(path,{'source_snapshot.zip':meta['source_snapshot_sha256']})
    runs=[json.loads((path/n).read_text()) for n in sorted(meta['result_hashes'])]
    if len(runs)+meta['failures']!=meta['planned_runs']: raise ValueError('Run accounting mismatch')
    return runs,meta,json.loads((path/'config.json').read_text())


def setup(title,ylabel):
    fig,ax=plt.subplots(figsize=(10,6.4)); fig.subplots_adjust(left=.10,right=.97,top=.84,bottom=.26)
    ax.set_title(title,loc='left',pad=24,fontweight='bold'); ax.set_ylabel(ylabel); ax.grid(axis='y',alpha=.18); ax.set_axisbelow(True)
    return fig,ax


def note(fig,text): fig.text(.10,.025,text+'\nAI-assisted code and plotting; source tables and methods accompany each figure.',fontsize=8,color='#444444',va='bottom')


def main():
    p=argparse.ArgumentParser(); p.add_argument('--synthetic',required=True); p.add_argument('--adult'); p.add_argument('--out',default='figures/report'); args=p.parse_args()
    synpath=ROOT/args.synthetic; sr,sm,sc=load_runs(synpath); out=ROOT/args.out; out.mkdir(parents=True,exist_ok=False)
    ar,am,ac=(None,None,None)
    if args.adult: ar,am,ac=load_runs(ROOT/args.adult)
    figs=[]; manifest_inputs={str(synpath.relative_to(ROOT)/'manifest.json'):sha256(synpath/'manifest.json')}
    if args.adult: manifest_inputs[str(Path(args.adult)/'manifest.json')]=sha256(ROOT/args.adult/'manifest.json')
    pdf=PdfPages(out/'SubPSI_chart_pack.pdf')
    def save(fig,name,table,caption,kind='empirical'):
        table=pd.DataFrame(table); table.to_csv(out/(name+'.csv'),index=False,float_format='%.12g')
        for ext in ['pdf','svg','png']: fig.savefig(out/(name+'.'+ext),bbox_inches='tight')
        pdf.savefig(fig,bbox_inches='tight'); plt.close(fig)
        files={name+'.'+ext:sha256(out/(name+'.'+ext)) for ext in ['csv','pdf','svg','png']}
        write_json(out/(name+'.manifest.json'),{'figure':name,'kind':kind,'caption':caption,'source_run_manifests':manifest_inputs,
          'config_hashes':{'synthetic':sm['config_sha256'],**({'adult':am['config_sha256']} if am else {})},
          'failed_runs':{'synthetic':sm['failures'],**({'adult':am['failures']} if am else {})},
          'plot_script_sha256':sha256(Path(__file__)),'environment':environment(),'files':files,
          'ai_role':'AI-assisted implementation and plotting; computed data, no invented measured values'})
        figs.append({'name':name,'caption':caption,'kind':kind})
    grouped={s:[r for r in sr if r['scenario']==s] for s in sc['scenarios']}

    table=[]; fig,ax=setup('A concentrated shift becomes visible inside the group','Population Stability Index (PSI)')
    for group,style,marker in [('all','-','o'),('A=1','--','s'),('A=1,B=1',':','^')]:
        values=[]
        for w in range(1,sc['windows']+1):
            stats=mean_interval([next(t['psi'] for t in r['windows'][w-1]['tests'] if t['group']==group and t['feature']=='signal') for r in grouped['S1']])
            table.append({'scenario':'S1','window':w,'group':group,**stats}); values.append(stats)
        line=ax.plot(range(1,sc['windows']+1),[v['estimate'] for v in values],linestyle=style,marker=marker,label=group)[0]
        ax.fill_between(range(1,sc['windows']+1),[v['low'] for v in values],[v['high'] for v in values],color=line.get_color(),alpha=.13)
    ax.axvline(sc['onset_window']-.5,color='gray',linestyle='--',label='Shift starts'); ax.set_ylim(bottom=0); ax.set_xlabel('Monitoring window')
    ax.legend(loc='upper left',ncols=2,fontsize=10)
    note(fig,f"Synthetic S1 • {sc['repeats']} independent runs • n={sc['n_window']:,} per window • affected group share {sc['affected_share']:.0%}\nBands: pointwise 95% intervals for mean PSI. Input shift is measurement corruption, not proof of unfairness.")
    save(fig,'01_drift_over_time',table,'Mean signal-feature PSI under S1. Reference is fixed within each run; bands summarize independent runs. The affected group is A=1; A=1,B=1 is a smaller intersection.')

    table=[]; fig,ax=setup('Opposing intersection shifts cancel in broader summaries','Signal-feature PSI, first changed window')
    names=['all','A=0','A=1','B=0','B=1','A=0,B=0','A=0,B=1','A=1,B=0','A=1,B=1']
    for i,g in enumerate(names):
        stats=mean_interval([next(t['psi'] for t in r['windows'][sc['onset_window']-1]['tests'] if t['group']==g and t['feature']=='signal') for r in grouped['S2']]); table.append({'group':g,**stats})
        ax.errorbar(i,stats['estimate'],yerr=[[stats['estimate']-stats['low']],[stats['high']-stats['estimate']]],fmt='o',capsize=4,color='C0' if i<5 else 'C1')
    ax.set_xticks(range(len(names)),[x.replace(',','\n') for x in names],fontsize=10); ax.set_ylim(bottom=0)
    note(fig,f"Synthetic S2 • {sc['repeats']} independent runs • equal intersection weights • 95% intervals for mean PSI\nConstructed stress test: the ±0.8 intersection means swap. Exact cancellation is an intentional special case.")
    save(fig,'02_intersection_cancellation',table,'Empirical PSI under a predeclared constructed cancellation scenario. This stress test demonstrates a blind spot of aggregation, not its prevalence in real deployments.')

    table=[]; fig,ax=setup('How often does each monitor alert after the intervention?','Runs with ≥1 alert in the post-onset horizon')
    xs=np.arange(len(sc['scenarios']))
    for j,method in enumerate(METHODS):
        vals=[]
        for s in sc['scenarios']:
            stats=wilson([any(w['methods'][method]['alert'] for w in r['windows'] if w['active']) for r in grouped[s]])
            vals.append(stats); table.append({'scenario':s,'method':method,**stats})
        ax.errorbar(xs+(j-2)*.13,[v['estimate'] for v in vals],yerr=[[v['estimate']-v['low'] for v in vals],[v['high']-v['estimate'] for v in vals]],fmt=['o','s','^','D','P'][j],capsize=2,color=COLORS[method],label=LABELS[method],markersize=5)
    ax.set_xticks(xs,['S0\nNo change','S1\nOne group','S2\nIntersections','S3\nBenign input','S4\nOutcome only','S5\nComposition'],fontsize=10); ax.set_ylim(-.035,1.05)
    fig.subplots_adjust(bottom=.32)
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncols=2,fontsize=9)
    note(fig,f"{sc['repeats']} runs/scenario • 95% Wilson intervals • horizon: {sc['windows']-sc['onset_window']+1} windows • Holm α=0.05 per window\nS0 and S4 have unchanged input distributions. An S5 aggregate alert can be correct composition drift.")
    save(fig,'03_alert_probability',table,'Run-level probability of any post-onset input alert. All methods see the same data and frozen bins. Fixed PSI thresholds are practical baselines, not matched-error tests; Holm families contain 2, 10 and 18 tests.')

    table=[]; fig,ax=setup('A per-window error criterion does not control a whole stream','No-change runs with an erroneous alert')
    for j,metric in enumerate(['first_window','complete_stream']):
        vals=[]
        for method in METHODS:
            stats=wilson([r['windows'][0]['methods'][method]['alert'] if metric=='first_window' else any(w['methods'][method]['alert'] for w in r['windows']) for r in grouped['S0']])
            vals.append(stats); table.append({'method':method,'metric':metric,**stats})
        ax.errorbar(np.arange(5)+(j-.5)*.16,[v['estimate'] for v in vals],yerr=[[v['estimate']-v['low'] for v in vals],[v['high']-v['estimate'] for v in vals]],fmt='o' if j==0 else 's',capsize=4,label='First window' if j==0 else f'Any of {sc["windows"]} windows')
    ax.axhline(.05,color='gray',linestyle=':',label='5% per-window reference'); ax.set_xticks(range(5),['Aggregate\nfixed','Aggregate\nHolm','Subgroups\nfixed','Singles\nHolm','Intersections\nHolm']); ax.set_ylim(-.035,1.05); ax.legend(fontsize=10)
    note(fig,f"Synthetic S0 • {sc['repeats']} independent complete runs • 95% Wilson intervals\nOne preselected window estimates per-window error; repeated windows are not treated as independent trials.")
    save(fig,'04_false_alerts',table,'False alerts under S0, with the first window and complete stream estimated separately. Within-window Holm correction does not promise horizon-wide control.')

    table=[]; fig,ax=setup('Detection delay includes the runs that never alert','Fraction of runs')
    horizon=sc['windows']-sc['onset_window']+1; delaylabels=[str(i) for i in range(horizon)]+['No alert']
    for j,m in enumerate(['A1','B1','B2']):
        delays=[]
        for r in grouped['S1']:
            hit=next((w['window']-sc['onset_window'] for w in r['windows'] if w['active'] and w['methods'][m]['alert']),horizon); delays.append(hit)
        rates=[np.mean(np.array(delays)==i) for i in range(horizon+1)]
        intervals=[wilson(np.array(delays)==i) for i in range(horizon+1)]
        ax.bar(np.arange(horizon+1)+(j-1)*.24,rates,width=.23,label=LABELS[m],color=COLORS[m],yerr=[[v['estimate']-v['low'] for v in intervals],[v['high']-v['estimate'] for v in intervals]],capsize=2,error_kw={'elinewidth':.8})
        for i in range(horizon+1): table.append({'scenario':'S1','method':m,'delay_windows':i if i<horizon else 'not_detected',**wilson(np.array(delays)==i)})
    ax.set_xticks(range(horizon+1),delaylabels); ax.set_xlabel('Windows after onset (0 = first changed window)'); ax.set_ylim(0,1.05); ax.legend(fontsize=10)
    note(fig,f"Synthetic S1 • {sc['repeats']} runs • each run appears exactly once per method\nBars: rates with 95% Wilson intervals. Pre-onset alerts do not remove runs from this diagnostic.")
    save(fig,'05_detection_delay',table,'Full delay distribution under S1, including non-detections. Bars show proportions and Wilson intervals for each delay category; coverage is not simultaneous across categories.')

    table=[]; fig,ax=setup('Input alerts and outcome disparities answer different questions','Change in absolute A-group TPR gap (percentage points)')
    for i,s in enumerate(sc['scenarios']):
        stats=mean_interval([np.mean([w['tpr_gap_change'] for w in r['windows'] if w['active'] and w['tpr_gap_change'] is not None]) for r in grouped[s]])
        stats={**stats}; table.append({'scenario':s,**stats})
        ax.errorbar(i,stats['estimate']*100,yerr=[[(stats['estimate']-stats['low'])*100],[(stats['high']-stats['estimate'])*100]],fmt='o',capsize=5,color='C0')
    ax.axhline(0,color='gray',linestyle='--'); ax.axhline(5,color='C1',linestyle=':',label='Predeclared +5 pp relevance marker')
    ax.set_xticks(range(6),['S0\nNo change','S1\nOne group','S2\nIntersections','S3\nBenign input','S4\nOutcome only','S5\nComposition']); ax.legend(fontsize=9)
    note(fig,f"Fixed logistic classifier uses signal only • {sc['repeats']} runs • 95% intervals for mean run-level change\nTPR gap = |TPR(A=1) − TPR(A=0)|. This single marginal metric can miss intersection disparities (including S2).")
    save(fig,'06_outcome_relevance',table,'A-group true-positive-rate gap change relative to a separate baseline audit. First average post-onset windows within each run, then form a run-level interval. Positive means wider gap; a lower gap is not a general fairness guarantee.')

    # Conditional assessment coverage: exact Binomial calculation, not fabricated empirical counts.
    from scipy.stats import binom
    table=[]; fig,ax=setup('Small groups can leave too little evidence to assess drift','Probability both samples meet the minimum count')
    shares=np.linspace(.005,.25,180)
    for n,style in [(200,'-'),(500,'--'),(2000,':')]:
        probability=binom.sf(sc['min_n']-1,n,shares)**2
        ax.plot(shares*100,probability,linestyle=style,label=f'{n:,} rows per sample')
        table.extend({'share':float(s),'sample_size':n,'minimum_count':sc['min_n'],'probability_both_supported':float(v)} for s,v in zip(shares,probability))
    ax.set_xlabel('Predefined group share of population (%)'); ax.set_ylim(0,1.03); ax.legend()
    note(fig,f"Analytical planning curve, not experimental results • independent equal-size samples • minimum n={sc['min_n']} each\nFormula: P[Binomial(n, share) ≥ {sc['min_n']}]². Passing this count gate does not guarantee useful power.")
    save(fig,'07_small_group_coverage',table,'Exact binomial planning calculation for a predefined group in two independent equal-size samples. This figure is analytical and makes no empirical coverage claim.','analytical')

    table=[]; fig,ax=setup('Aggregation dilutes a shift when fewer people are affected','Population PSI (no sampling noise or smoothing)')
    shares=np.linspace(.01,1,100); subgroup=psi_probabilities([.5,.5],[.2,.8]); aggregate=[]
    for s in shares:
        q=.5+.3*s; v=psi_probabilities([.5,.5],[1-q,q]); aggregate.append(v)
        table.append({'affected_share':s,'aggregate_psi':v,'affected_group_psi':subgroup})
    ax.plot(shares*100,aggregate,label='Whole population'); ax.axhline(subgroup,linestyle='--',color='C1',label='Affected group')
    ax.set_xlabel('Affected group share (%)'); ax.set_ylim(bottom=0); ax.legend()
    note(fig,"Constructed two-bin example • reference high-bin probability 0.50; affected group changes to 0.80\nExact population calculation, not a research trial. This demonstrates dilution, not real-world detection power.")
    save(fig,'08_explain_dilution',table,'A teaching example calculated directly from two-bin population probabilities. There are no sample counts, seeds or uncertainty intervals because no random experiment is represented.','constructed analytical example')

    table=[]; fig,ax=setup('Paired comparisons quantify the subgroup-monitoring difference','Difference in alert probability (percentage points)')
    for i,s in enumerate(sc['scenarios']):
        differences=np.array([int(any(w['methods']['B2']['alert'] for w in r['windows'] if w['active']))-int(any(w['methods']['A1']['alert'] for w in r['windows'] if w['active'])) for r in grouped[s]])
        rng=np.random.default_rng([sc['seed'],991,i]); boot=rng.choice(differences,size=(5000,len(differences)),replace=True).mean(axis=1)
        lo,hi=np.quantile(boot,[.025,.975]); estimate=float(differences.mean())
        table.append({'scenario':s,'comparison':'B2 minus A1','estimate':estimate,'low':lo,'high':hi,'n':len(differences),'interval':'paired run-level percentile bootstrap, 5000 resamples; degenerate bounds possible'})
        ax.errorbar(i,estimate*100,yerr=[[(estimate-lo)*100],[(hi-estimate)*100]],fmt='o',capsize=5,color='C0')
    ax.axhline(0,color='gray',linestyle='--'); ax.set_xticks(range(6),sc['scenarios']); ax.set_ylim(-105,105)
    note(fig,f"Synthetic streams paired across methods • {sc['repeats']} run pairs per scenario • 95% paired bootstrap intervals\nMore alerts are beneficial only when relevant input changes exist; S0/S4 differences are false-alert differences.")
    save(fig,'09_paired_comparison',table,'Difference between B2 and A1 post-onset any-alert proportions using the same simulated runs. Percentile bootstrap intervals resample paired complete runs, not windows; degeneracy at all-equal differences is a limitation.')

    if ar:
        table=[]; fig,ax=setup('Public-data check: a controlled change in Adult records','Runs with ≥1 alert after onset')
        for j,m in enumerate(METHODS):
            vals=[]
            for scenario in ac['scenarios']:
                runs=[r for r in ar if r['scenario']==scenario]; stats=wilson([any(w['methods'][m]['alert'] for w in r['windows'] if w['active']) for r in runs]); vals.append(stats); table.append({'scenario':scenario,'method':m,**stats})
            ax.errorbar(np.arange(2)+(j-2)*.1,[v['estimate'] for v in vals],yerr=[[v['estimate']-v['low'] for v in vals],[v['high']-v['estimate'] for v in vals]],fmt=['o','s','^','D','P'][j],capsize=4,color=COLORS[m],label=LABELS[m])
        ax.set_xticks([0,1],['Unweighted sampling','Within-Female high-hours enrichment']); ax.set_ylim(-.035,1.05); ax.set_xlim(-.45,1.45)
        fig.subplots_adjust(bottom=.32)
        ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncols=2,fontsize=9)
        note(fig,f"Adult (UCI, CC BY 4.0) • {ac['repeats']} Monte Carlo runs per condition • 95% conditional Wilson intervals\nHistorical cross-sectional records; simulated order. Reusing a finite pool does not create new independent people.")
        save(fig,'10_public_data_check',table,'Semi-synthetic Adult check, conditional on one deduplicated fixed split, classifier and monitoring pool. Within selected Female/age strata, records with hours>40 receive 6× sampling weight after onset. Labels and records are unchanged; composition counts use the original pool proportions. Becker & Kohavi (1996), DOI 10.24432/C5XW20, CC BY 4.0.')
    table=[]; fig,ax=setup('Intersection outcomes can differ while marginal gaps stay small','True-positive rate (TPR)')
    names=['all','A=0','A=1','A=0,B=0','A=0,B=1','A=1,B=0','A=1,B=1']
    for j,phase in enumerate(['baseline','post_onset']):
        stats_list=[]
        for group in names:
            values=[]
            for r in grouped['S2']:
                if phase=='baseline': value=next(x['tpr'] for x in r['baseline_performance'] if x['group']==group)
                else: value=float(np.mean([next(x['tpr'] for x in w['performance'] if x['group']==group) for w in r['windows'] if w['active']]))
                values.append(value)
            stats=mean_interval(values); stats_list.append(stats); table.append({'group':group,'phase':phase,**stats})
        ax.errorbar(np.arange(len(names))+(j-.5)*.18,[v['estimate'] for v in stats_list],yerr=[[v['estimate']-v['low'] for v in stats_list],[v['high']-v['estimate'] for v in stats_list]],fmt='o' if j==0 else 's',capsize=3,label='Independent baseline audit' if j==0 else 'After intersection shift')
    ax.set_xticks(range(len(names)),[n.replace(',','\n') for n in names],fontsize=10); ax.set_ylim(0,1.05); ax.legend(loc='lower left',fontsize=9)
    note(fig,f"Synthetic S2 • {sc['repeats']} runs • mean TPR, 95% run-level intervals • fixed classifier, unchanged labels\nOutcomes are used for evaluation only. Compare this chart with the input cancellation chart (Figure 2).")
    save(fig,'11_intersection_outcomes',table,'Baseline and post-onset TPR for aggregate, marginal A groups and intersections in S2. After averaging windows within each run, intervals use independent runs. Marginal outcome summaries alone can conceal large intersection differences.')
    pdf.close()
    write_json(out/'index.json',{'figures':figs,'run_manifests':manifest_inputs,'chart_pack_sha256':sha256(out/'SubPSI_chart_pack.pdf')})
    cards=''.join(f'<section><h2>{html.escape(f["name"])}</h2><img src="{f["name"]}.svg" alt="{html.escape(f["caption"])}"><p>{html.escape(f["caption"])}</p><p><a href="{f["name"]}.pdf">PDF</a> · <a href="{f["name"]}.png">300 dpi PNG</a> · <a href="{f["name"]}.svg">SVG</a> · <a href="{f["name"]}.csv">Source data</a> · <a href="{f["name"]}.manifest.json">Provenance</a></p></section>' for f in figs)
    (out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>SubPSI evidence and chart pack</title><style>body{font:17px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#172238;background:#f3f5f8}h1{font-size:36px}section{background:white;border:1px solid #dce1e8;border-radius:12px;padding:24px;margin:28px 0}img{width:100%}p{line-height:1.6}a{color:#1859a3}h2{font-size:20px}</style><h1>SubPSI · evidence &amp; chart pack</h1><p>Exploratory validation. Input drift is not proof of unfairness. Charts 7–8 are analytical teaching/planning examples; other charts come from saved experimental runs. Code and visual production were AI-assisted.</p><p><a href="SubPSI_chart_pack.pdf">Download all figures as a PDF</a></p>'+cards+'</html>')
    print(f'Exported {len(figs)} figures to {out}')

if __name__=='__main__': main()

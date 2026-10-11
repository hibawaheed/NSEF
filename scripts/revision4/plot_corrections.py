"""Two reporting corrections from saved tables, not new calibration evidence."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from subpsi.correction import read_table
from subpsi.provenance import sha256,write_json,save_snapshot,environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',default='results/summary/revision4/preparation-02')
    parser.add_argument('--out',default='figures/revision4/preparation')
    a = parser.parse_args(); source=ROOT/a.source; out=ROOT/a.out
    out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.size':12,'axes.titlesize':15,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    records=[]
    def export(stem,fig,table,parents,explanation):
        table.to_csv(out/f'{stem}.csv',index=False)
        for ext in ['png','pdf','svg']:
            fig.savefig(out/f'{stem}.{ext}',dpi=300,facecolor='white')
        plt.close(fig)
        records.append(dict(stem=stem,source_csv=stem+'.csv',
                            source_tables={str(p.relative_to(ROOT)):sha256(p) for p in parents},
                            evidence='Previously examined records; reporting correction, not untouched validation',
                            explanation=explanation))
    audit_path=source/'representation_audit.json'
    audit=json.loads(audit_path.read_text())
    rows=[]
    for r in audit:
        if r['feature']!='num_of_prev_attempts': continue
        labels=['Below zero','0 or more','Missing'] if r['rule']=='v3_quantile' else ['0','1','2 or more','Missing']
        for label,count in zip(labels,r['counts']):
            rows.append(dict(rule=r['rule'],category=label,count=count,n_design=r['n_design'],
                             occupied_numeric_bins=r['occupied_numeric_bins'],
                             nonconstant_collapse=r['nonconstant_collapse']))
    table=pd.DataFrame(rows)
    fig,axes=plt.subplots(1,2,figsize=(11,5.4),sharey=True)
    for ax,rule,title,color in zip(axes,['v3_quantile','corrected_counts'],
                                   ['Original representation','Corrected representation'],['#777777','#0072B2']):
        data=table.loc[table.rule.eq(rule)]
        bars=ax.bar(data.category,data['count'],color=color,width=.65)
        ax.bar_label(bars,padding=5,fontsize=12)
        ax.set_title(title,pad=14); ax.set_ylim(0,410)
        ax.set_xlabel('Previous attempts category',labelpad=10)
    axes[0].set_ylabel('Historical design records')
    fig.suptitle('Same 372 students; the corrected bins retain attempt counts',fontsize=16,y=.97)
    fig.text(.5,.035,'2013J BBB design role only. Missing = 0. This fixes representation; it does not prove a later change.',ha='center',fontsize=10)
    fig.subplots_adjust(left=.08,right=.98,bottom=.20,top=.79,wspace=.14)
    export('01_oulad_representation',fig,table,[audit_path],
           'The old rule put all nonnegative counts together. The retained correction separates 0, 1 and 2+; the underlying records did not change.')
    outcome_path=source/'oulad_outcomes_extended.csv'
    full=read_table(outcome_path)
    table=full.query("group == 'Everyone' and subset == 'group' and period == 'current'").copy()
    order=['Accuracy','Balanced accuracy','TPR','FPR']
    fig,ax=plt.subplots(figsize=(10.8,5.7)); x=np.arange(4); width=.34
    for i,(model,color) in enumerate([('Frozen logistic','#0072B2'),('Training-majority constant','#D55E00')]):
        # Saved model names, never inferred from which result is larger.
        saved_name='Training-majority baseline' if model.startswith('Training') else model
        values=table.loc[table.model.eq(saved_name)].set_index('metric').loc[order,'value'].to_numpy(float)
        bars=ax.bar(x+(i-.5)*width,100*values,width,label=model,color=color)
        ax.bar_label(bars,labels=[f'{v:.1%}' for v in values],padding=4,fontsize=11)
    ax.set_xticks(x,['Accuracy\n(higher is better)','Balanced accuracy\n(higher is better)',
                     'TPR\n(successes predicted positive)','FPR\n(lower is better)'])
    ax.set_ylim(0,112);ax.set_yticks([0,25,50,75,100]);ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_ylabel('Rate');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    ax.set_title('OULAD: the frozen model needs a simple baseline',pad=52)
    ax.legend(loc='lower center',bbox_to_anchor=(.5,1.03),ncol=2,frameon=False)
    accuracy=table.loc[table.metric.eq('Accuracy')].set_index('model')
    logistic=accuracy.loc['Frozen logistic']; constant=accuracy.loc['Training-majority baseline']
    if (logistic.n,logistic.positives,logistic.negatives)!=(constant.n,constant.positives,constant.negatives):
        raise ValueError('Model and baseline must use the same held-out records')
    fig.text(.5,.055,f'2014J audit: {int(logistic.n)} records ({int(logistic.positives)} successes; {int(logistic.negatives)} non-successes). Correct: model {int(logistic.numerator)}; constant {int(constant.numerator)}.',ha='center',fontsize=10)
    fig.text(.5,.018,'Constant class chosen from 2013J training labels only. Descriptive cohort results; no natural drift-accuracy claim.',ha='center',fontsize=10)
    fig.subplots_adjust(left=.09,right=.98,bottom=.25,top=.76)
    export('02_oulad_prediction_baseline',fig,table,[outcome_path],
           'The majority baseline is slightly more accurate; the frozen model has about 50.9% balanced accuracy. This limits outcome conclusions, without invalidating the separate input study.')
    write_json(out/'figure_index.json',records)
    import subprocess
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),
               purpose='Corrected reporting of historical design and already saved outcome counts',
               new_calibration_or_evaluation=False,source_manifest_sha256=sha256(source/'manifest.json'),
               git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
               source_snapshot_sha256=save_snapshot(ROOT,out),plot_code_sha256=sha256(Path(__file__)),environment=environment(),
               files={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
    links=''.join(f'<article><h2>{r["stem"]}</h2><img style="max-width:100%" src="{r["stem"]}.png"><p>{r["explanation"]}</p><p><a href="{r["stem"]}.csv">Exact source CSV</a> · <a href="{r["stem"]}.pdf">PDF</a> · <a href="{r["stem"]}.svg">SVG</a></p></article>' for r in records)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>SubPSI R4 preparation</title><main style="max-width:1000px;margin:3rem auto;font-family:system-ui"><h1>Revision 4: reporting corrections</h1><p>Previously examined OULAD data. New calibration and evaluation await approval.</p>'+links+'</main>')
    manifest['files']['index.html']=sha256(out/'index.html')
    write_json(out/'manifest.json',manifest)
    print(f'Saved {len(records)} figures with CSV, 300 dpi PNG, PDF and SVG: {out}')


if __name__=='__main__':main()

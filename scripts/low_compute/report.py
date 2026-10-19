"""Derive all figures and claims from saved benchmark and historical results."""
from common import *
import argparse,hashlib,gzip,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RAW=ROOT/'results/raw/low_compute/2026-10-18';SUMMARY=ROOT/'results/summary/low_compute/2026-10-18'
LABELS={'A':'Original\nPSI-only','B':'Count-reuse\nPSI','C':'Matched\nKS-only','D':'Aggregate\nPSI\n(lower scope)'}
COLORS={'A':'#6d7681','B':'#146f8c','C':'#d77a26','D':'#b6bac0'}
CONDITIONS=['unchanged','age_up2','age_up4','age_down4']

def main():
 p=argparse.ArgumentParser();p.add_argument('--figures',default='figures/low_compute/2026-10-18');a=p.parse_args();figdir=ROOT/a.figures
 if not (RAW/'benchmark/completion.json').exists():raise ValueError('Incomplete benchmark')
 if figdir.exists():raise FileExistsError('Preserve figure attempts; use a new directory')
 figdir.mkdir(parents=True);SUMMARY.mkdir(exist_ok=True,parents=True)
 c=configuration();records=[];streams=[];latency=[];parents=pd.read_csv(RAW/'benchmark/process_wall.csv');hashchecks=0
 for path in sorted((RAW/'benchmark').glob('*.json')):
  if path.name=='completion.json':continue
  d=json.loads(path.read_text());rows=d.pop('rows');d['stream_count']=len(rows);d['incoming_records']=sum(x['incoming_records'] for x in rows)
  row=parents.loc[(parents.variant==d['variant'])&(parents.workload==d['workload'])&(parents['repeat']==d['repeat'])].iloc[0]
  if row.receipt_sha256!=sha256(path):raise ValueError('Benchmark receipt changed')
  d['parent_wall']=row.parent_wall
  for field in ['monitoring_cpu','monitoring_wall','setup_cpu','setup_wall','validation_cpu','validation_wall','loading_cpu','loading_wall','output_cpu','output_wall','accounting_cpu','accounting_wall']:
   d[field]=sum(r[field] for r in rows)
   if d[field]<0:raise ValueError('Negative timing component')
  d['complete_cpu_per_stream']=d['complete_cpu']/len(rows);d['monitoring_cpu_per_stream']=d['monitoring_cpu']/len(rows)
  d['complete_throughput']=d['incoming_records']/d['complete_wall'];d['monitoring_throughput']=d['incoming_records']/d['monitoring_wall'];d['peak_rss_mib']=d['process_peak_rss_kib']/1024
  records.append(d)
  for r in rows:
   for look,value in enumerate(r.pop('batch_latencies_wall'),1):latency.append(dict(variant=r['variant'],workload=r['workload'],repeat=r['repeat'],warmup=r['warmup'],cell=r['cell'],look=look,seconds=value))
   r['stage_measurements']=json.dumps(r['stage_measurements'],sort_keys=True);streams.append(r)
 processes=pd.DataFrame(records);stream=pd.DataFrame(streams);lat=pd.DataFrame(latency)
 if len(processes)!=96 or processes.warmup.sum()!=16:raise ValueError('Expected 16 warm-ups and 80 timed processes')
 for (work,rep,cell),group in stream.loc[stream.variant.isin(['A','B'])].groupby(['workload','repeat','cell']):
  if len(group)!=2 or group.output_sha256.nunique()!=1:raise ValueError('Timed A/B output mismatch')
  hashchecks+=1
 for _,group in stream.groupby(['workload','variant','cell']):
  if group.output_sha256.nunique()!=1:raise ValueError('Non-reproducible timed scientific output')
 processes.to_csv(SUMMARY/'process_measurements.csv',index=False);stream.to_csv(SUMMARY/'stream_measurements.csv',index=False);lat.to_csv(SUMMARY/'batch_latency.csv',index=False)
 timed=processes.loc[~processes.warmup];metrics=['complete_cpu','complete_wall','parent_wall','monitoring_cpu','monitoring_wall','complete_cpu_per_stream','monitoring_cpu_per_stream','complete_throughput','monitoring_throughput','peak_rss_mib','startup_cpu','setup_cpu','validation_cpu','loading_cpu','output_cpu','accounting_cpu'];summary=[]
 for (work,var),group in timed.groupby(['workload','variant']):
  if len(group)!=5:raise ValueError('Five technical repeats required')
  for metric in metrics:summary.append(dict(workload=work,variant=var,metric=metric,median=group[metric].median(),minimum=group[metric].min(),maximum=group[metric].max(),repeats=5,source_csv='process_measurements.csv'))
 summaries=pd.DataFrame(summary);summaries.to_csv(SUMMARY/'cost_summary.csv',index=False)
 conditions=[]
 for (condition,var,rep),d in stream.loc[(stream.workload=='primary')&~stream.warmup].groupby(['condition','variant','repeat']):
  conditions.append(dict(condition=condition,variant=var,repeat=rep,monitoring_cpu=d.monitoring_cpu.sum(),elapsed_cpu=d.elapsed_cpu.sum(),elapsed_wall=d.elapsed_wall.sum(),records=d.incoming_records.sum(),throughput=d.incoming_records.sum()/d.elapsed_wall.sum()))
 pd.DataFrame(conditions).to_csv(SUMMARY/'condition_timings.csv',index=False)
 eq=pd.read_csv(RAW/'equivalence/summary.csv');eq.to_csv(SUMMARY/'equivalence.csv',index=False)
 old=pd.read_csv(ROOT/'results/summary/revision4/main-approved/streams.csv');rates=pd.read_csv(ROOT/'results/summary/revision4/main-approved/rates.csv')
 policies=['ordinary_50','fixed_100','fixed_400','global_calibrated','group_calibrated'];historical=[]
 for policy in policies:
  for condition in CONDITIONS:
   for method in ['PSI','KS']:
    metric='whole_stream_alert' if condition=='unchanged' else 'exact_target_detection'
    rate=rates.loc[(rates.policy==policy)&(rates.condition==condition)&(rates.method==method)&(rates.scope=='intersection')&(rates.metric==metric)].iloc[0]
    endpoints=old.loc[(old.policy==policy)&(old.condition==condition)&(old.method==method)&(old.scope=='intersection')]
    historical.append(dict(evidence='Historical Version 4; unchanged engine; not new optimization trials',policy=policy,condition=condition,method=method,metric=metric,successes=rate.successes,n=rate.repeats,rate=rate.rate,lower=rate.lower,upper=rate.upper,ever_assessed=int(endpoints.ever_assessed.sum()),restricted_delay_mean=endpoints.restricted_delay.mean(),source_csv='results/summary/revision4/main-approved/rates.csv',endpoint_csv='results/summary/revision4/main-approved/streams.csv'))
 history=pd.DataFrame(historical);history.to_csv(SUMMARY/'historical_tradeoff.csv',index=False)
 selected=old.loc[old.cell.isin(c['primary']['cells'])&(old.policy=='fixed_100')&(old.scope=='intersection')].copy();selected['evidence']='Existing selected 20 streams; equivalence verified; no new trials';selected.to_csv(SUMMARY/'verified_subset_endpoints.csv',index=False)
 # D has smaller scope: compare its numerical outputs to the old Everyone rows only.
 aggregate_checks=0
 from worker import scientific_look
 for cell in c['inputs']:
  with gzip.open(ROOT/cell['original']['fixed_100']['path'],'rt') as f:before=json.load(f)
  path=ROOT/f"data/raw/low_compute/2026-10-18/benchmark_outputs/primary/0/D/stream-{cell['cell']:03}.jsonl"
  for line in path.read_text().splitlines():
   value=json.loads(line);look=value['tests'][0]['look'];expected=scientific_look({k:[r for r in before[k] if r['look']==look] for k in ['tests','schedule','decisions']},'PSI')
   if value['tests']!=[r for r in expected['tests'] if r['group']=='Everyone']:raise ValueError('Aggregate test mismatch')
   ad=next(d for d in value['decisions'] if d['scope']=='aggregate');bd=next(d for d in expected['decisions'] if d['scope']=='aggregate')
   ad.pop('plan_sha256');bd.pop('plan_sha256')
   if ad!=bd:raise ValueError('Aggregate decision mismatch')
   aggregate_checks+=len(value['tests'])
 # Save graph CSVs BEFORE rendering; each visual uses its just-saved source.
 runtime=summaries.loc[summaries.workload=='primary'].copy();runtime.to_csv(figdir/'01_runtime.csv',index=False)
 memory=[]
 for _,r in summaries.loc[summaries.metric=='peak_rss_mib'].iterrows():memory.append(dict(panel='process_peak',**r.to_dict()))
 for prefix,work in [(5,'prefix5'),(10,'prefix10'),(20,'primary')]:
  d=stream.loc[(stream.variant=='B')&(stream.workload==work)&(stream.cell==140)&~stream.warmup]
  for metric in ['persistent_histogram_array_bytes','detector_state_accounted_bytes','validation_accounted_bytes']:
   memory.append(dict(panel='object_accounting',workload=work,variant='B',metric=metric,median=d[metric].median(),minimum=d[metric].min(),maximum=d[metric].max(),repeats=5,batches=prefix,source_csv='stream_measurements.csv'))
 pd.DataFrame(memory).to_csv(figdir/'02_memory.csv',index=False)
 third=history.copy();third['verified_feature_rows']=eq.feature_rows.sum();third['verified_replay_runs']=len(eq);third['maximum_psi_difference']=eq.max_psi_difference.max();third.to_csv(figdir/'03_equivalence_and_tradeoff.csv',index=False)
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','savefig.dpi':300})
 def save(fig,name,foot):
  fig.text(.04,.025,foot,ha='left',va='bottom',fontsize=8,color='#444444')
  for ext in ['png','pdf','svg']:fig.savefig(figdir/f'{name}.{ext}',facecolor='white')
  plt.close(fig)
 def bars(ax,data,metric,title,ylabel):
  d=data.loc[data.metric==metric].set_index('variant').loc[list('ABCD')]
  y=d['median'].to_numpy(float);low=y-d.minimum.to_numpy(float);high=d.maximum.to_numpy(float)-y
  ax.bar(range(4),y,color=[COLORS[x] for x in 'ABCD'],yerr=np.vstack([low,high]),capsize=4,width=.65)
  ax.set_xticks(range(4),[LABELS[x] for x in 'ABCD'],fontsize=9);ax.set_title(title,loc='left',fontsize=11,fontweight='bold');ax.set_ylabel(ylabel);ax.set_ylim(0,max(d.maximum)*1.22)
  for x,v in enumerate(y):ax.text(x,float(d.iloc[x].maximum)+max(y)*.025,f'{v:.2f}',ha='center',va='bottom',fontsize=9)
  ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
 data=pd.read_csv(figdir/'01_runtime.csv');fig,axes=plt.subplots(1,3,figsize=(12,5));fig.subplots_adjust(left=.06,right=.985,bottom=.23,top=.78,wspace=.36)
 fig.suptitle('Compute cost on the same saved records',x=.04,ha='left',fontsize=18,fontweight='bold',y=.97)
 fig.text(.04,.87,'Fixed-100 accumulation | 20 balanced streams | 20 batches per stream | median and range of 5 technical repeats',fontsize=10)
 bars(axes[0],data,'complete_cpu_per_stream','A. Complete execution','CPU seconds per stream')
 bars(axes[1],data,'monitoring_cpu_per_stream','B. Monitoring only','CPU seconds per stream')
 t=data.copy();mask=t.metric=='complete_throughput';t.loc[mask,['median','minimum','maximum']]/=1000
 bars(axes[2],t,'complete_throughput','C. Complete throughput','Thousand incoming records / wall second')
 save(fig,'01_runtime','Source: 01_runtime.csv. Complete costs include imports, loading, validation and output; setup is excluded from monitoring only.\nAggregate PSI tests Everyone only: its lower cost buys less scope. Ranges describe this machine, not population uncertainty.')
 data=pd.read_csv(figdir/'02_memory.csv');fig,axes=plt.subplots(1,2,figsize=(11,5.5));fig.subplots_adjust(left=.075,right=.98,bottom=.24,top=.78,wspace=.32)
 fig.suptitle('Measured RAM is much larger than the histogram state',x=.04,ha='left',fontsize=17,fontweight='bold',y=.97)
 fig.text(.04,.87,'Left: fresh-process high-water RAM. Right: separately accounted Python objects for the same first strong-change stream.',fontsize=9)
 bars(axes[0],data.loc[(data.panel=='process_peak')&(data.workload=='primary')],'peak_rss_mib','A. Complete process peak','MiB (resident set size)')
 sub=data.loc[data.panel=='object_accounting']
 for metric,label,color in [('validation_accounted_bytes','Exact ID audit (grows)','#c1612c'),('detector_state_accounted_bytes','Detector objects','#146f8c'),('persistent_histogram_array_bytes','Histogram arrays only','#6d7681')]:
  g=sub.loc[sub.metric==metric].sort_values('batches');axes[1].plot(g.batches,g['median']/1024,'o-',label=label,color=color)
 axes[1].set_yscale('log');axes[1].set_xticks([5,10,20]);axes[1].set_xlabel('Existing stream prefix: number of batches');axes[1].set_ylabel('KiB accounted at prefix end (log scale)');axes[1].set_title('B. Components; not total RAM',loc='left',fontweight='bold',fontsize=11);axes[1].legend(fontsize=9);axes[1].grid(alpha=.18)
 save(fig,'02_memory','Source: 02_memory.csv. Left whiskers: min/max of 5 fresh-process measurements. Right: object accounting, not peak RSS.\nThe full process includes Python/libraries, current batch, ID sets, output and permutation temporaries. Total memory is not constant.')
 data=pd.read_csv(figdir/'03_equivalence_and_tradeoff.csv');fig=plt.figure(figsize=(12,8));gs=fig.add_gridspec(2,2,left=.075,right=.98,bottom=.20,top=.76,hspace=.55,wspace=.35);ax=fig.add_subplot(gs[0,0]);wait=fig.add_subplot(gs[0,1]);tableax=fig.add_subplot(gs[1,:]);tableax.axis('off')
 fig.suptitle('Same scientific decisions; the old trade-offs remain',x=.04,ha='left',fontsize=18,fontweight='bold',y=.97)
 fig.text(.04,.87,f'Equivalence: {len(eq)} selected replays, {int(eq.feature_rows.sum()):,} feature comparisons; zero PSI difference; exact p-values, schedules and alerts.',fontsize=10,fontweight='bold')
 fig.text(.04,.81,'Below is the unchanged Version 4 study, not additional optimization trials or proof that all 220 streams were rechecked.',fontsize=10,color='#84401b')
 for mi,method in enumerate(['PSI','KS']):
  sub=data.loc[(data.policy=='fixed_100')&(data.method==method)].set_index('condition').loc[CONDITIONS];pos=np.arange(4)+(mi-.5)*.34;y=sub.rate.to_numpy()*100
  ax.bar(pos,y,.33,label=method,color=COLORS['B' if method=='PSI' else 'C'],yerr=np.maximum(0,np.vstack([y-sub.lower.to_numpy()*100,sub.upper.to_numpy()*100-y])),capsize=3)
  for x,(_,r) in zip(pos,sub.iterrows()):ax.text(x,min(112,r.upper*100+2),f'{int(r.successes)}/{int(r.n)}',ha='center',fontsize=8)
 ax.set_xticks(range(4),['Unchanged\nfalse alert','Age 60+\nweight x2','Age 60+\nweight x4','Age 60+\nweight x0.25']);ax.set_ylim(0,119);ax.set_ylabel('Streams with alert / detection (%)');ax.set_title('A. Fixed 100: retained historical results',loc='left',fontsize=11,fontweight='bold');ax.legend(fontsize=9)
 for mi,method in enumerate(['PSI','KS']):
  sub=data.loc[(data.policy=='fixed_100')&(data.method==method)&(data.condition!='unchanged')].set_index('condition').loc[CONDITIONS[1:]]
  wait.bar(np.arange(3)+(mi-.5)*.34,sub.restricted_delay_mean,.33,color=COLORS['B' if method=='PSI' else 'C'],label=method)
 wait.set_xticks(range(3),['Weight x2','Weight x4','Weight x0.25']);wait.set_ylim(0,16);wait.set_ylabel('Mean restricted delay (looks)');wait.set_title('B. Waiting includes every miss',loc='left',fontsize=11,fontweight='bold');wait.axhline(15,color='#777777',ls=':',lw=1)
 labels=['One batch, 50','Accumulate 100','Accumulate 400','Global fallback 800','Group fallback 800'];body=[]
 for policy,label in zip(policies,labels):
  row=[label]
  for condition in CONDITIONS[1:]+['unchanged']:
   d=data.loc[(data.policy==policy)&(data.condition==condition)].set_index('method');row.append(f"{int(d.loc['PSI','successes'])} / {int(d.loc['KS','successes'])}")
  ready=data.loc[(data.policy==policy)&(data.condition=='unchanged')&(data.method=='PSI')].iloc[0];row.append(f"{int(ready.ever_assessed)}/100");body.append(row)
 tableax.set_title('C. Every historical collection policy remains visible (PSI / KS counts)',loc='left',fontsize=11,fontweight='bold',pad=8)
 t=tableax.table(cellText=body,colLabels=['Policy','x2: /40','x4: /40','x0.25: /40','False alert: /100','Target assessed'],loc='center',cellLoc='center',colWidths=[.25,.13,.13,.15,.17,.17]);t.auto_set_font_size(False);t.set_fontsize(9);t.scale(1,1.5)
 for (r,col),cell in t.get_celld().items():cell.set_edgecolor('#d4dae0');cell.set_facecolor('#edf3f6' if r==0 else 'white')
 save(fig,'03_equivalence_and_tradeoff','Source: 03_equivalence_and_tradeoff.csv; original Version 4 rates/streams CSVs are linked in the evidence table.\nWhiskers in A: original pointwise 95% Wilson intervals. Delay: each miss = 15 delivery looks, not days.\nChanges are constructed whole-record resampling, not natural drift accuracy.\nThe 800-target rules failed their criterion and never assessed the target. No universal PSI advantage, fairness guarantee or new algorithm is claimed.')
 # Every rendered format and exact source table is hash-listed.
 files={str(p.relative_to(ROOT)):sha256(p) for p in sorted(figdir.iterdir()) if p.is_file()}
 report=dict(figures=files,source_csvs={str(p.relative_to(ROOT)):sha256(p) for p in sorted(SUMMARY.glob('*.csv'))},benchmark_outputs_AB_exact_checks=hashchecks,aggregate_feature_comparisons=aggregate_checks,original_source_sha256={str(p.relative_to(ROOT)):sha256(p) for p in [ROOT/'results/summary/revision4/main-approved/rates.csv',ROOT/'results/summary/revision4/main-approved/streams.csv']},report_code_sha256=sha256(Path(__file__)))
 (figdir/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 # Basic-English measured findings, not a paper in the student's voice.
 def val(var,metric):return float(summaries.loc[(summaries.workload=='primary')&(summaries.variant==var)&(summaries.metric==metric),'median'].iloc[0])
 findings={'cpu_reduction_percent':100*(1-val('B','complete_cpu')/val('A','complete_cpu')),'wall_reduction_percent':100*(1-val('B','complete_wall')/val('A','complete_wall')),'rss_reduction_percent':100*(1-val('B','peak_rss_mib')/val('A','peak_rss_mib')),'rss_difference_mib':val('A','peak_rss_mib')-val('B','peak_rss_mib'),'baseline_complete_cpu':val('A','complete_cpu'),'optimized_complete_cpu':val('B','complete_cpu'),'baseline_peak_mib':val('A','peak_rss_mib'),'optimized_peak_mib':val('B','peak_rss_mib')}
 (SUMMARY/'headline_measurements.json').write_text(json.dumps(findings,indent=2)+'\n');print(json.dumps(findings,indent=2));print(summaries.loc[(summaries.workload=='primary')&summaries.metric.isin(['complete_cpu','complete_wall','monitoring_cpu','peak_rss_mib'])].to_string(index=False))
if __name__=='__main__':main()

"""Pre-evaluation support figure, not a drift or accuracy result."""
import json,sys,subprocess,datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from subpsi.provenance import sha256

def main():
 out=ROOT/'figures/revision3/feasibility';out.mkdir(parents=True,exist_ok=False)
 paths=[ROOT/'results/raw/revision3/acs-feasibility/acs_support.csv',ROOT/'results/raw/revision3/oulad-feasibility-checked/oulad_support.csv']
 a,b=(pd.read_csv(p) for p in paths)
 a=a.loc[a.role.isin(['reference','monitor'])&a.level.eq('intersection')].copy()
 b=b.loc[b.role.isin(['reference','monitor'])&b.level.eq('intersection')].copy()
 races=['White alone','Black / African American alone','American Indian alone','Alaska Native alone','AI/AN specified or unspecified*','Asian alone','Native Hawaiian / Pacific Islander alone','Some other race alone','Two or more races']
 names=[f'{sex} · {race}' for sex in ['Male','Female'] for race in races]
 ga=list(a.loc[a.period.eq(2016),'group']);gb=list(b.loc[b.period.eq('2013J'),'group'])
 ma=a.pivot(index='group',columns='period',values='n').reindex(ga).to_numpy()
 mb=b.pivot(index='group',columns='period',values='n').reindex(gb).to_numpy()
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'svg.fonttype':'none'})
 fig=plt.figure(figsize=(14,11));grid=fig.add_gridspec(1,2,width_ratios=[1.35,1],left=.31,right=.97,bottom=.24,top=.82,wspace=.48)
 ax=fig.add_subplot(grid[0,0]);right=grid[0,1].subgridspec(3,1,height_ratios=[1,1,1]);bx=fig.add_subplot(right[0]);txt=fig.add_subplot(right[1:]);txt.axis('off')
 cmap=ListedColormap(['#e2e7ee','#f3c3a6','#f7dfa1','#c1dfdf'])
 def draw(axis,mat,labels,cols):
  classes=np.select([mat==0,mat<50,mat<100],[0,1,2],default=3)
  axis.imshow(classes,cmap=cmap,norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4),aspect='auto')
  for i in range(mat.shape[0]):
   for j in range(mat.shape[1]):axis.text(j,i,f'{mat[i,j]:,}',ha='center',va='center',fontsize=9,color='#173242')
  axis.set_xticks(range(len(cols)),cols);axis.set_yticks(range(len(labels)),labels,fontsize=9)
  axis.set_xticks(np.arange(-.5,mat.shape[1],1),minor=True);axis.set_yticks(np.arange(-.5,mat.shape[0],1),minor=True)
  axis.grid(which='minor',color='white',lw=2);axis.tick_params(which='both',length=0)
  for spine in axis.spines.values():spine.set_visible(False)
 draw(ax,ma,names,['2016\nreference','2017\nmonitor','2018\nmonitor','2019\nmonitor'])
 draw(bx,mb,['Female · no disability','Female · disability','Male · no disability','Male · disability'],['2013J\nreference','2014J\nmonitor'])
 ax.set_title('ACS · Massachusetts\n18 declared intersections',loc='left',pad=15,weight='bold')
 bx.set_title('OULAD · module BBB\n4 declared intersections',loc='left',pad=15,weight='bold')
 txt.text(0,.85,'Why these counts matter',weight='bold',fontsize=14,color='#173242')
 txt.text(0,.77,'Both sides need enough records.\n\nA large later cohort cannot repair\na tiny historical reference group.\n\nSmall and absent groups remain\nin the tables as unassessable.\n\nCounts describe these selected\nrecords, not population sizes.',va='top',fontsize=12,linespacing=1.4,color='#31485d')
 fig.text(.04,.95,'Before asking “did it drift?”, check who can be assessed.',fontsize=22,weight='bold',color='#173242')
 fig.text(.04,.90,'SOURCE & SUPPORT CHECK  ·  Proposed disjoint roles  ·  No new drift tests or prediction results',fontsize=11,color='#5b6a78')
 fig.legend(handles=[Patch(facecolor=cmap(i),label=l) for i,l in enumerate(['0 records','1–49','50–99','100 or more'])],loc='lower left',bbox_to_anchor=(.04,.16),ncol=4,frameon=False,title='Records per group: ordinary minimum 50; accumulation minimum 100, on both sides')
 fig.text(.04,.11,'Every declared intersection is shown. Aggregate and single-attribute counts are also retained in the source support tables.\nACS: ages 16–90; household role split. OULAD: registered and active at day 0; later repeat students excluded.\n*ACS race code 5: American Indian and Alaska Native tribes specified, or AI/AN unspecified with no other races.',fontsize=9,color='#536575',linespacing=1.5)
 fig.text(.04,.025,'SubPSI revision 3 · Feasibility only · AI-assisted code and figure · Counts are exact for these files; no population uncertainty implied.',fontsize=9,color='#536575')
 stem='01_support_feasibility'
 for ext in ['png','pdf','svg']:fig.savefig(out/f'{stem}.{ext}',dpi=300,facecolor='white')
 plt.close(fig)
 pd.concat([a,b],ignore_index=True).to_csv(out/f'{stem}.csv',index=False)
 manifest={'kind':'pre-evaluation schema/support check; no algorithmic result','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':{str(p.relative_to(ROOT)):sha256(p) for p in paths},'plot_code_sha256':sha256(Path(__file__)),'git_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'configuration':'proposed roles, seed string r3-role-31721 / r3-oulad-31721; see support script and review plan','files':{p.name:sha256(p) for p in out.iterdir() if p.is_file()},'uncertainty':'none: complete selected-file counts, not an estimated population probability','source_check_scripts':{'inspect_support.py':sha256(ROOT/'scripts/revision3/inspect_support.py')}}
 (out/f'{stem}.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Saved support CSV, SVG, PDF, 300 dpi PNG and manifest')
if __name__=='__main__':main()

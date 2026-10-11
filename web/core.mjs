export const VERSION='2.0.0';
export function random(seed=91){let a=seed>>>0;return()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}
export function parseCSV(text){
  text=text.replace(/^\uFEFF/,'');let rows=[],row=[],cell='',quoted=false,closed=false;
  for(let i=0;i<=text.length;i++){
    const c=text[i];
    if(quoted){if(c===undefined)throw Error('Unclosed quotation mark in CSV.');if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=c;continue;}
    if(c==='"'){if(cell.length||closed)throw Error('Unexpected quotation mark in CSV.');quoted=true;continue;}
    if(c===','||c==='\n'||c==='\r'||c===undefined){row.push(cell.trim());cell='';closed=false;if(c!==','){if(row.some(v=>v!==''))rows.push(row);row=[];if(c==='\r'&&text[i+1]==='\n')i++;}continue;}
    if(closed && !/\s/.test(c))throw Error('Unexpected text after a quoted CSV field.');if(!closed)cell+=c;
  }
  if(rows.length<2)throw Error('CSV needs a header and at least one data row.');
  const headers=rows.shift();if(headers.some(h=>!h)||new Set(headers).size!==headers.length)throw Error('Every column needs a unique, nonempty name.');
  if(headers.length>100||rows.length>20000)throw Error('Use at most 100 columns and 20,000 rows per file.');
  if(rows.some(r=>r.length!==headers.length))throw Error('Some rows have a different number of fields from the header.');
  return{headers,rows};
}
export const missing=v=>v===''||v===null||v===undefined;
export function psi(a,b){const na=a.reduce((x,y)=>x+y,0),nb=b.reduce((x,y)=>x+y,0),k=a.length;if(!na||!nb)return null;return a.reduce((s,v,i)=>{let p=(v+.5)/(na+k*.5),q=(b[i]+.5)/(nb+k*.5);return s+(q-p)*Math.log(q/p);},0);}
export function holm(ps){const order=ps.map((p,i)=>[p,i]).sort((a,b)=>a[0]-b[0]);const out=Array(ps.length);let prev=0;order.forEach(([p,i],j)=>{prev=Math.min(1,Math.max(prev,p*(ps.length-j)));out[i]=prev;});return out;}
export function binsFrom(values,type='numeric',n=6){
  if(type==='numeric'){
    let v=values.filter(x=>!missing(x)).map(Number);if(!v.length)throw Error('The design split contains no observed numeric values.');if(v.some(x=>!Number.isFinite(x)))throw Error('Numeric columns must contain finite numbers or blank cells.');v.sort((a,b)=>a-b);
    let edges=[];for(let j=1;j<n;j++){let p=(v.length-1)*j/n,k=Math.floor(p);edges.push(v[k]+(v[Math.min(k+1,v.length-1)]-v[k])*(p-k));}
    edges=[...new Set(edges)];
    if(v[0]===v.at(-1)){const x=v[0];return{type,constant:x,labels:[`<${x}`,`=${x}`,`>${x}`,'Missing']};}
    const fmt=x=>Number(x.toPrecision(4)).toString();const labels=edges.map((x,i)=>i?`${fmt(edges[i-1])} to <${fmt(x)}`:`<${fmt(x)}`);labels.push(`≥${fmt(edges.at(-1))}`,'Missing');return{type,edges,labels};
  }
  const categories=[...new Set(values.filter(v=>!missing(v)))].sort();if(categories.length>40)throw Error('Use a categorical feature with at most 40 design categories, or select numeric.');
  return{type,categories,labels:[...categories.map(x=>`Value: ${x}`),'Unseen in design','Missing']};
}
export function encode(v,b){if(missing(v))return b.labels.length-1;if(b.type==='numeric'){let x=Number(v);if(!Number.isFinite(x))throw Error('Numeric feature contains invalid or infinite values.');if(b.constant!==undefined)return x<b.constant?0:x===b.constant?1:2;let i=0;while(i<b.edges.length&&x>=b.edges[i])i++;return i;}let i=b.categories.indexOf(v);return i<0?b.categories.length:i;}
export function histogram(values,b){const c=Array(b.labels.length).fill(0);values.forEach(v=>c[encode(v,b)]++);return c;}
export function permuteCounts(a,b,draws,seed,stop=.05){
  let total=a.map((v,i)=>v+b[i]),na=a.reduce((s,v)=>s+v,0),nt=total.reduce((s,v)=>s+v,0),obs=psi(a,b),ex=0;const rng=random(seed),small=Math.min(na,nt-na);
  if(obs===null)return{p:1,psi:null,draws:0,censored:false};
  for(let d=0;d<draws;d++){
    let c=Array(a.length).fill(0),remaining=nt,needed=small;
    // Sequential sampling without replacement produces a multivariate hypergeometric draw.
    for(let k=0;k<total.length-1;k++){
      let v=total[k],take=0;
      for(let j=0;j<v;j++){if(needed===0){remaining-=v-j;break;}if(needed===remaining){take+=v-j;needed-=v-j;remaining-=v-j;break;}if(rng()<needed/remaining){take++;needed--;}remaining--;}
      c[k]=take;
    }
    c[c.length-1]=needed;
    if(psi(c,total.map((v,i)=>v-c[i]))>=obs-1e-12)ex++;
    if((ex+1)/(draws+1)>stop)return{p:1,psi:obs,draws:d+1,censored:true};
  }
  return{p:(ex+1)/(draws+1),psi:obs,draws,censored:false};
}
function compareValue(a,b){const an=Number(a),bn=Number(b);if(a!==''&&b!==''&&Number.isFinite(an)&&Number.isFinite(bn))return an-bn;return a.localeCompare(b,undefined,{numeric:true});}
export function analyze(reference,current,options,progress=()=>{}){
  const {feature,group1,group2,windowColumn,type='numeric',policy='batch'}=options;
  if(reference.rows.length<100)throw Error('Use at least 100 reference rows; 25% are reserved for independent bin design.');
  const cols=reference.headers,fi=cols.indexOf(feature),ci=current.headers.indexOf(feature);if(fi<0||ci<0)throw Error('Selected feature must appear in both files.');
  const gs=[group1,group2].filter(Boolean);if(new Set(gs).size!==gs.length||gs.includes(feature))throw Error('Choose distinct grouping columns, different from the monitored feature.');
  if(windowColumn&&[feature,...gs].includes(windowColumn))throw Error('The time column must differ from feature and grouping columns.');
  gs.forEach(g=>{if(!cols.includes(g)||!current.headers.includes(g))throw Error('Grouping columns must appear in both files.');});
  const rng=random(20261011),order=reference.rows.map((_,i)=>i);for(let i=order.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[order[i],order[j]]=[order[j],order[i]];}
  const dn=Math.floor(order.length*.25),design=order.slice(0,dn).map(i=>reference.rows[i]),ref=order.slice(dn).map(i=>reference.rows[i]);
  const bin=binsFrom(design.map(r=>r[fi]),type);reference.rows.forEach(r=>encode(r[fi],bin));current.rows.forEach(r=>encode(r[ci],bin));
  const normalize=v=>missing(v)?null:v;const label=v=>v===null?'(missing)':JSON.stringify(v);
  const groups=[{name:'Everyone',selectors:[],level:'overall'}];
  for(const g of gs){const ri=cols.indexOf(g),ti=current.headers.indexOf(g),values=[...new Set([...ref.map(r=>normalize(r[ri])),...current.rows.map(r=>normalize(r[ti]))])].sort((a,b)=>String(a).localeCompare(String(b)));if(values.length>12)throw Error('Each group column can have at most 12 categories. Create age bands or other categories first.');values.forEach(v=>groups.push({name:`${g} = ${label(v)}`,selectors:[[g,v]],level:'subgroup'}));}
  if(gs.length===2){const pairs=new Map();for(const [rs,hs] of [[ref,cols],[current.rows,current.headers]])for(const r of rs){const pair=gs.map(g=>normalize(r[hs.indexOf(g)]));pairs.set(JSON.stringify(pair),pair);}for(const pair of [...pairs.values()].sort())groups.push({name:gs.map((g,i)=>`${g} = ${label(pair[i])}`).join(' & '),selectors:gs.map((g,i)=>[g,pair[i]]),level:'intersection'});}
  if(groups.length>40)throw Error('This combination produces more than 40 groups. Reduce group categories.');
  let windows=['Current'];if(windowColumn){const wi=current.headers.indexOf(windowColumn);if(wi<0)throw Error('Time column is not in current data.');windows=[...new Set(current.rows.map(r=>r[wi]))].sort(compareValue);if(windows.some(missing))throw Error('The time column contains blank values.');if(windows.length>12)throw Error('Use at most 12 time batches per analysis.');}
  const m=windows.length*groups.length,draws=Math.max(1999,Math.ceil(m/.05)-1);const match=(r,hs,g)=>g.selectors.every(([col,v])=>normalize(r[hs.indexOf(col)])===v);
  const refValues=groups.map(g=>ref.filter(r=>match(r,cols,g)).map(r=>r[fi]));const refCounts=refValues.map(v=>histogram(v,bin));
  const buffers=groups.map(()=>[]),starts=groups.map(()=>0),results=[];let step=0;
  windows.forEach((win,w)=>{
    const batch=current.rows.filter(r=>!windowColumn||r[current.headers.indexOf(windowColumn)]===win);
    groups.forEach((g,gi)=>{
      const v=batch.filter(r=>match(r,current.headers,g)).map(r=>r[ci]);buffers[gi].push(...v);
      const values=policy==='accumulate'?buffers[gi]:v,threshold=policy==='accumulate'?100:50;
      const a=refCounts[gi],b=histogram(values,bin),supported=refValues[gi].length>=threshold&&values.length>=threshold;
      let t=supported?permuteCounts(a,b,draws,90217+w*1009+gi):{p:1,psi:null,draws:0,censored:false};
      results.push({window:win,windowIndex:w,group:g.name,level:g.level,nReference:refValues[gi].length,nCurrent:values.length,supported,...t,referenceCounts:a,currentCounts:b,startWindow:windows[policy==='accumulate'?starts[gi]:w]});
      if(policy==='accumulate'&&supported){buffers[gi]=[];starts[gi]=w+1;}
      progress(++step/m);
    });
  });
  const adjusted=holm(results.map(r=>r.p));results.forEach((r,i)=>{r.adjustedP=adjusted[i];r.alert=r.supported&&r.adjustedP<=.05;});
  return{version:VERSION,options,designRows:dn,referenceRows:ref.length,currentRows:current.rows.length,windows,groups:groups.map(g=>g.name),bins:bin,results,permutations:draws,alpha:.05,familySize:m,method:'Independent 25% reference design split; PSI count smoothing 0.5; permutation tests; Holm across all groups and selected batches. A p of 1 may conservatively censor a non-significant test.',limitations:'Requires independent exchangeable rows; not valid for arbitrary autocorrelated time series. Repeated new analyses do not share one error budget. No outcome-harm or fairness conclusion follows from input drift. Accumulation may mix pre-change and post-change records.'};
}
export function demo(kind='cancellation',n=1600){const rng=random(1003),normal=()=>Math.sqrt(-2*Math.log(Math.max(rng(),1e-12)))*Math.cos(2*Math.PI*rng());const headers=['signal','group_a','group_b','batch'];const rows=(active)=>Array.from({length:n},()=>{const a=rng()<.5?0:1,b=rng()<.5?0:1,p=a===b?1:-1;let x=normal()+.8*p;if(active&&kind==='cancellation')x-=1.6*p;if(active&&kind==='concentrated'&&a===1&&b===1)x+=1.6;return[x.toFixed(6),String(a),String(b),active?'2':'1'];});return{reference:{headers,rows:rows(false)},current:{headers,rows:rows(true)}};}
export function csv(rows){return rows.map(row=>row.map(v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}).join(',')).join('\r\n');}

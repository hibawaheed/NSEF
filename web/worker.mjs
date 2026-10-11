import {analyze} from './core.mjs';
self.onmessage=e=>{try{const result=analyze(e.data.reference,e.data.current,e.data.options,p=>self.postMessage({type:'progress',value:p}));self.postMessage({type:'result',result});}catch(e){self.postMessage({type:'error',message:e.message});}};

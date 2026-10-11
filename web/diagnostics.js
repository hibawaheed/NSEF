window.addEventListener('error',event=>{const status=document.getElementById('status');if(status){status.textContent='The page encountered an error: '+(event.message||'a required file could not load')+'. Please reload.';status.classList.add('error');}});
window.addEventListener('unhandledrejection',event=>{const status=document.getElementById('status');if(status){status.textContent='The page could not complete that action: '+(event.reason?.message||String(event.reason));status.classList.add('error');}});

document.getElementById('status').textContent='Loading analysis module…';

import React,{useEffect,useRef,useState} from 'react';

export default function AssistDialog({target,api,onClose,onApply,onBusy}){
 const dialog=useRef(),alive=useRef(true);
 const [instruction,setInstruction]=useState(''),[draft,setDraft]=useState(''),[working,setWorking]=useState(false),[error,setError]=useState(''),[model,setModel]=useState(''),[elapsed,setElapsed]=useState(0);
 useEffect(()=>{if(!working)return;const started=Date.now();const timer=setInterval(()=>setElapsed(Math.floor((Date.now()-started)/1000)),250);return()=>clearInterval(timer)},[working]);
 useEffect(()=>{alive.current=true;dialog.current.showModal();return()=>{alive.current=false}},[]);
 async function run(){
  setWorking(true);onBusy(true);setError('');setDraft('');setElapsed(0);
  try{
   const j=target.kind==='transcript'?await api('/assets/'+target.asset+'/transcribe',{}):await api('/assist/draft',{target:target.kind,text:target.source,instruction,context:target.context||'',language:target.language});
   for(;;){
    const job=await api('/jobs/'+j.id);
    if(!alive.current)return;
    if(job.status==='failed')throw Error(job.error);
    if(job.status==='complete'){setDraft(job.result.text);setModel(job.result.model);break}
    await new Promise(r=>setTimeout(r,1200));
   }
  }catch(e){if(alive.current)setError(e.message)}finally{if(alive.current){setWorking(false);onBusy(false)}}
 }
 return <dialog ref={dialog} className="assist-dialog" onCancel={e=>{e.preventDefault();if(!working)onClose()}}><div className="drawer-content">
  <div className="section"><h2>{target.kind==='transcript'?'Transcribe recording':'✦ '+target.label}</h2><button disabled={working} onClick={onClose}>Close assistant</button></div>
  <p className="muted">{target.kind==='transcript'?'Transcribes the entire saved recording. Apply trims first if needed. Review the words before using them as an exact voice reference.':'Uses the local writing model. Review and edit the suggestion before applying it. No audio is generated here.'}</p>
  {target.kind!=='transcript'&&<label>What should change?<textarea aria-label="Assistant instruction" value={instruction} maxLength={2000} onChange={e=>setInstruction(e.target.value)} placeholder={target.kind==='voice'?'Make this voice warm, friendly and slightly raspy.':'Make this more natural and conversational, keeping the meaning.'}/></label>}
  <button disabled={working||(target.kind!=='transcript'&&!instruction.trim())} onClick={run}>{working?'Working locally…':target.kind==='transcript'?'Start transcription':'Suggest draft'}</button>
  {working&&<div className="assist-progress" role="status" aria-live="polite"><span className="assist-spinner" aria-hidden="true"/><span><strong>{target.kind==='transcript'?'Transcribing recording…':'Writing your draft locally…'}</strong><small>Still working · {elapsed}s. You can review the result when it finishes.</small></span></div>}
  {error&&<p role="alert" className="error">{error}</p>}
  {draft&&<><label>Review suggestion<textarea aria-label="Review suggestion" rows={8} value={draft} maxLength={10000} onChange={e=>setDraft(e.target.value)}/></label><p className="muted">Model: {model}. {target.kind==='transcript'?'Transcript saved with its source asset ID. Audio is unchanged.':''}</p><div className="row"><button disabled={working||!draft.trim()} onClick={()=>onApply(draft)}>Use {target.kind==='transcript'?'reference transcript':'draft'}</button>{target.kind==='transcript'&&<button disabled={working||!draft.trim()} onClick={()=>onApply(draft,'script')}>Use in script</button>}<button disabled={working} onClick={onClose}>Discard suggestion</button></div></>}
 </div></dialog>
}

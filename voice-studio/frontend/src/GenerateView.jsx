// Generate screen from the new design (UI plan step 3): hero prompt card, voice chip,
// read-only model label, Draft / Rewrite, Ctrl+Enter, inline conversation blocks.
// Presentational only: all state and handlers come from App in main.jsx.
import React from 'react';
import {Icon} from './Shell.jsx';
import {Sparkles,WandSparkles,ChevronDown,X,Plus,User,CircleStop,AudioLines} from 'lucide';

export const LANGUAGES=['Auto','English','Chinese','Japanese','Korean','German','French','Russian','Portuguese','Spanish','Italian'];
const ENGINE='Qwen3-TTS';
export const isSample=p=>Boolean(p.archetype||(p.synthetic&&!p.designed));
const voiceKind=p=>!p?'No voice chosen':isSample(p)?'Sample voice':p.designed?'Designed voice':'Saved voice';

// Read-only model status from GET /api/health. The backend has one model and no model choice.
export function modelInfo(health){
 if(!health)return {state:'checking',pill:'Checking model…',label:'Checking…'};
 const inf=health.inference||{};
 if(inf.status!=='ready')return {state:'offline',pill:ENGINE+' · offline',label:'Unavailable'};
 const kind=inf.model||'Base';
 return {state:inf.loaded?'ready':'idle',pill:ENGINE+' · '+kind+(inf.loaded?' loaded':' · loads on first run'),label:ENGINE+' 1.7B '+kind,loaded:!!inf.loaded};
}
const isSubmit=e=>e.key==='Enter'&&(e.ctrlKey||e.metaKey)&&!e.shiftKey&&!e.altKey;

export function GenerateView(p){
 const {profiles,profile,onProfile,language,onLanguage,text,onText,health,capabilities,canGenerate,onGenerate,onDraft,helpersDisabled,
  conversation,onConversation,sequence,onBlock,onAddBlock,onRemoveBlock,onRewrite,canConverse,onGenerateConversation,generating,canStop,onStop,onLoadReference,children}=p;
 const chosen=profiles.find(x=>x.id===profile),model=modelInfo(health);
 const assist=Boolean(capabilities?.enabled)&&!health?.demo;
 // Ctrl+Enter (Cmd+Enter on macOS) runs the same handler as the button, with the same guard.
 const promptKey=e=>{if(!isSubmit(e))return;e.preventDefault();if(canGenerate)onGenerate()};
 const blockKey=e=>{if(!isSubmit(e))return;e.preventDefault();if(canConverse)onGenerateConversation()};
 return <section className="vs-gen" aria-label="Generate speech">
  <div className="vs-prompt">
   <div className="vs-prompt-top">
    <label className="vs-voice-chip" title="Choose a voice">
     <span className="vs-avatar" aria-hidden="true">{(chosen?.name||'?').trim().charAt(0).toUpperCase()}</span>
     <span className="vs-voice-text"><b>{chosen?.name||'Choose a voice'}</b><small>{voiceKind(chosen)}</small></span>
     <Icon icon={ChevronDown} size={14}/>
     <select aria-label="Choose a voice" value={profile} onChange={e=>onProfile(e.target.value)}><option value="">Choose a voice…</option>{[['Your saved voices',false],['Sample voices',true]].map(([label,sample])=><optgroup label={label} key={label}>{profiles.filter(x=>isSample(x)===sample).map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</optgroup>)}</select>
    </label>
    <button className="vs-link" disabled={!chosen} onClick={onLoadReference} title="Put this voice's reference recording in the player">Load voice reference</button>
    <span className="vs-grow"/>
    <button className={'vs-switch'+(conversation?' on':'')} role="switch" aria-checked={conversation} onClick={()=>onConversation(!conversation)}><i aria-hidden="true"/>Conversation</button>
   </div>
   <textarea className="vs-prompt-text" aria-label="Text to speak" rows="2" value={text} onChange={e=>onText(e.target.value)} onKeyDown={promptKey} placeholder="Type what the voice should say…"/>
   <div className="vs-prompt-rule"/>
   <div className="vs-prompt-bar">
    <label className="vs-drop"><span>Language</span><select aria-label="Language" value={language} onChange={e=>onLanguage(e.target.value)}>{LANGUAGES.map(l=><option key={l}>{l}</option>)}</select><Icon icon={ChevronDown} size={13}/></label>
    <span className={'vs-drop vs-readonly '+model.state} title="Set by the local inference worker. There is no model choice in this version."><span>Model</span><b>{model.label}</b></span>
    <span className="vs-grow"/>
    {assist&&<button className="vs-btn vs-btn-tint" disabled={helpersDisabled} onClick={onDraft}><Icon icon={WandSparkles} size={14}/>Draft / Rewrite</button>}
    <button className="accent vs-generate" disabled={!canGenerate} onClick={onGenerate}><Icon icon={Sparkles} size={14} strokeWidth={2}/>Generate</button>
   </div>
  </div>
  <p className="vs-hints"><span>Ctrl + Enter to generate</span><span aria-hidden="true">·</span><span>Saved voices use a reference recording and its exact transcript.</span>{model.state==='idle'&&<><span aria-hidden="true">·</span><span>The first run loads the model (about 1 min).</span></>}</p>
  {conversation&&<div className="vs-convo" aria-label="Conversation">
   <div className="vs-convo-head"><b>CONVERSATION ON</b><span>One voice per block, generated in order. Takes are saved together as an arrangement and a mixed WAV.</span></div>
   <ol className="vs-blocks">{sequence.map((t,i)=><li className="vs-block" key={t.id}>
    <div className="vs-block-side"><small>BLOCK {i+1}</small>
     <label className="vs-drop vs-speaker"><Icon icon={User} size={13}/><select aria-label={'Voice for block '+(i+1)} value={t.profile} onChange={e=>onBlock(t.id,{profile:e.target.value})}><option value="">Choose voice…</option>{profiles.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}{t.profile&&!profiles.some(x=>x.id===t.profile)&&<option value={t.profile}>Unavailable voice</option>}</select><Icon icon={ChevronDown} size={13}/></label>
    </div>
    <textarea aria-label={'Text for block '+(i+1)} rows="2" value={t.text} onChange={e=>onBlock(t.id,{text:e.target.value})} onKeyDown={blockKey} placeholder="What this speaker says…"/>
    <div className="vs-block-actions">
     {assist&&<button className="vs-btn vs-btn-tint vs-sm" aria-label={'Rewrite block '+(i+1)} disabled={helpersDisabled} onClick={()=>onRewrite(t)}><Icon icon={WandSparkles} size={13}/>Rewrite</button>}
     <button className="vs-icon-btn" aria-label={'Remove block '+(i+1)} title="Remove block" disabled={generating||sequence.length===1} onClick={()=>onRemoveBlock(t.id)}><Icon icon={X} size={14}/></button>
    </div>
   </li>)}</ol>
   <div className="vs-convo-foot">
    <button className="vs-btn" disabled={generating} onClick={onAddBlock}><Icon icon={Plus} size={14}/>Add block</button>
    <span className="vs-hint">Empty blocks are skipped.{assist?' Rewrite uses the surrounding blocks as context.':''}</span>
    <span className="vs-grow"/>
    {canStop&&<button className="vs-btn" onClick={onStop}><Icon icon={CircleStop} size={14}/>Stop after current job</button>}
    <button className="accent vs-generate" disabled={!canConverse} onClick={onGenerateConversation}><Icon icon={AudioLines} size={14} strokeWidth={2}/>Generate conversation</button>
   </div>
  </div>}
  {children}
 </section>;
}

// Running-job card for the Recordings panel. Progress is client-side (block i of n); the server only reports queued / running / complete / failed.
export function JobCard({progress,job,status,firstRun,onStop}){
 const done=Math.max(0,progress.i-1)/progress.n;
 return <div className="vs-job" role="status" aria-label="Generation in progress">
  <div className="vs-job-head"><i aria-hidden="true"/><b>Generating {progress.i} / {progress.n}…</b></div>
  <small>{progress.n>1?'Conversation · block '+progress.i:'Single line'}{job?.status?' · '+job.status:''}{firstRun?' · first run loads the model (~1 min)':''}</small>
  <div className="vs-job-bar"><span style={{width:Math.max(6,done*100)+'%'}}/></div>
  {status&&/^Stopping/.test(status)?<small>{status}</small>:progress.n>1&&<button className="vs-btn vs-sm" onClick={onStop}>Stop after current job</button>}
 </div>;
}

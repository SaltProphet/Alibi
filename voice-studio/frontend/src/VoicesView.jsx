// Voices screen from the new design (UI plan step 5): tabs Saved / Clone / Design, saved-voice list,
// 3-step clone form, voice design form. Presentational only: state and handlers come from App in main.jsx.
// Profiles have no language field (backend gap), so no per-profile language is shown or saved.
import React,{useRef,useState} from 'react';
import {Icon} from './Shell.jsx';
import {isSample,LANGUAGES} from './GenerateView.jsx';
import {Play,Pause,Mic,Square,Upload,Captions,Save,WandSparkles,Sparkles,Scissors,ChevronDown} from 'lucide';

const AVATARS=[['#3a2a24','#ff6a3d'],['#24303a','#7fb8e6'],['#2e2a3a','#b6a6e8'],['#243a31','#7fd6ae'],['#33332a','#d9cf8a']];
const hash=s=>[...s].reduce((h,c)=>(h*31+c.charCodeAt(0))>>>0,7);
// Plan §3 mapping: Designed = designed; Sample = archetype, or synthetic and not designed; Cloned = everything else.
export const voiceBadge=p=>p.designed?'Designed':isSample(p)?'Sample':'Cloned';
// Same limits as POST /api/profiles (0.5–60 s); 3–15 s is the recommendation, not a rule.
export function referenceProblem(duration){
 if(!(duration>0))return null;
 if(duration<.5)return 'This recording is '+duration.toFixed(2)+' s. A voice reference must be at least 0.5 s.';
 if(duration>60)return 'This recording is '+duration.toFixed(1)+' s. A voice reference can be at most 60 s. Trim it and apply the trim first.';
 return null;
}

function VoiceRow({p,asset,used,playing,onPlay,onUse,compact}){
 const badge=voiceBadge(p),[bg,fg]=AVATARS[hash(p.name)%AVATARS.length];
 const meta=[p.synthetic?(p.designed?'Synthetic · from a description':badge==='Sample'?'Sample voice · synthetic':'Synthetic'):null,asset?'Reference '+asset.duration.toFixed(1)+' s':null,used?'used '+used+'×':null].filter(Boolean).join(' · ');
 return <li className={'vs-voice'+(compact?' compact':'')}>
  <span className="vs-voice-avatar" style={{background:bg,color:fg}} aria-hidden="true">{p.name.trim().charAt(0).toUpperCase()}</span>
  <span className="vs-voice-main"><span className="vs-voice-title"><b title={p.name}>{p.name}</b><em className={'vs-badge'+(badge==='Cloned'?' generated':'')}>{badge}</em></span><small title={used?'Recordings in your library generated with this voice':undefined}>{meta||'\u00a0'}</small></span>
  <button className="vs-icon-btn" aria-label={(playing?'Pause ':'Play ')+p.name+' reference'} disabled={!asset} onClick={onPlay}><Icon icon={playing?Pause:Play} size={14}/></button>
  <button className="vs-btn vs-btn-tint vs-sm" onClick={onUse}>Use</button>
 </li>;
}

function SavedList({profiles,assets,compact,onUse,onSeeAll}){
 const audio=useRef(),[playingId,setPlayingId]=useState(null);
 const byId=Object.fromEntries(assets.map(a=>[a.id,a]));
 const used=id=>assets.reduce((n,a)=>n+(a.profile===id?1:0),0);
 const play=p=>{const el=audio.current;if(!el)return;if(playingId===p.id&&!el.paused){el.pause();return}el.src='/api/assets/'+p.asset+'/audio';setPlayingId(p.id);el.play().catch(()=>setPlayingId(null))};
 return <>
  <audio ref={audio} className="vs-voice-audio" preload="none" onPause={()=>setPlayingId(null)} onEnded={()=>setPlayingId(null)}/>
  <ul className={'vs-voice-list'+(compact?' compact':'')}>{profiles.map(p=><VoiceRow key={p.id} p={p} asset={byId[p.asset]} used={used(p.id)} playing={playingId===p.id} onPlay={()=>play(p)} onUse={()=>onUse(p.id)} compact={compact}/>)}
   {!profiles.length&&<li className="vs-empty">No saved voices yet. Clone one from a recording or design one.</li>}</ul>
 </>;
}

function HintCard({onDesign}){
 return <div className="vs-card vs-voice-hint"><b><Icon icon={Sparkles} size={13}/>Want a voice nobody recorded?</b><p>Use the <button className="vs-link" onClick={onDesign}>Design tab</button>: describe a voice, generate a sample, save it as a profile. It never changes a cloned voice.</p></div>;
}

function Step({n,title,note,children}){
 return <section className="vs-card vs-step"><div className="vs-step-head"><span className="vs-step-n">{n}</span><h2>{title}</h2><span className="vs-grow"/><small>{note}</small></div>{children}</section>;
}

export function VoicesView(p){
 const {tab,onTab,profiles,assets,onUse,
  chosen,selected,onChoose,recording,micPending,onRecord,onStopRecording,onImport,importDisabled,waveRef,trim,onTrim,onPlaySelection,onApplyTrim,applyTrimDisabled,
  transcript,onTranscript,canTranscribe,transcribeReason,onTranscribe,profileName,onProfileName,onSave,saveDisabled,
  description,onDescription,sampleText,onSampleText,language,onLanguage,assist,onShape,helpersDisabled,canDesign,voiceDesignMissing,onDesign}=p;
 const problem=chosen?referenceProblem(chosen.duration):null;
 const trimmed=chosen&&(trim.start>0.005||trim.end<chosen.duration-0.005);
 const side=<aside className="vs-voices-side"><div className="vs-voices-side-head"><h2>Saved voices <span className="vs-count">{profiles.length}</span></h2><span className="vs-grow"/><button className="vs-link vs-accent-link" onClick={()=>onTab('saved')}>See all in Saved</button></div>
  <SavedList profiles={profiles.slice(0,5)} assets={assets} compact onUse={onUse}/><HintCard onDesign={()=>onTab('design')}/></aside>;
 return <div className="vs-voices">
  <div className="vs-voices-bar">
   <div className="vs-tabs" role="tablist" aria-label="Voices">
    {[['saved','Saved',profiles.length],['clone','Clone'],['design','Design']].map(([k,label,count])=><button key={k} role="tab" aria-selected={tab===k} className={tab===k?'on':''} onClick={()=>onTab(k)}>{label}{count!=null&&<small>{count}</small>}</button>)}
   </div>
   <span className="vs-grow"/><span className="vs-hint">Cloning uses Qwen3-TTS Base + your exact transcript</span>
  </div>
  {tab==='saved'&&<div className="vs-voices-saved"><SavedList profiles={profiles} assets={assets} onUse={onUse}/><HintCard onDesign={()=>onTab('design')}/></div>}
  {tab==='clone'&&<div className="vs-voices-grid"><div className="vs-voices-form">
   <Step n="1" title="Reference recording" note="Clean 3–15 s works best">
    <div className="vs-ref-row">
     <label className="vs-drop vs-ref-pick"><select aria-label="Reference recording" value={selected||''} onChange={e=>onChoose(e.target.value)}><option value="">Choose a recording…</option>{assets.map(a=><option key={a.id} value={a.id}>{a.name}  ·  {a.duration.toFixed(1)} s</option>)}</select><Icon icon={ChevronDown} size={13}/></label>
     {recording?<button className="danger vs-rec" onClick={onStopRecording}><Icon icon={Square} size={13}/>Stop</button>:<button className="accent vs-rec" disabled={importDisabled||micPending} onClick={onRecord}><Icon icon={Mic} size={14} strokeWidth={2}/>{micPending?'Waiting…':'Record'}</button>}
     <label className={'vs-btn'+(importDisabled?' disabled':'')}><Icon icon={Upload} size={14}/>Import audio<input type="file" aria-label="Import reference audio" accept=".wav,.mp3,.flac,audio/*" disabled={importDisabled} onChange={e=>{onImport(e.target.files[0]);e.target.value=''}}/></label>
    </div>
    {chosen?<div className="vs-ref-wave"><div className="vs-ref-wave-canvas" ref={waveRef}/>
     <div className="vs-ref-trim"><label className="vs-num"><span>In</span><input type="number" aria-label="Reference in (seconds)" step=".01" min="0" value={trim.start} onChange={e=>onTrim('start',e.target.value)}/><i>s</i></label>
      <span className="vs-hint">Drag handles to trim · apply trims before saving</span>
      <label className="vs-num"><span>Out</span><input type="number" aria-label="Reference out (seconds)" step=".01" min="0" value={trim.end} onChange={e=>onTrim('end',e.target.value)}/><i>s</i></label></div>
     <div className="vs-ref-actions"><button className="vs-btn vs-sm" onClick={onPlaySelection}><Icon icon={Play} size={13}/>Play selection</button><button className="vs-btn vs-sm" disabled={!trimmed||applyTrimDisabled} onClick={onApplyTrim} title="Creates a trimmed copy; the original is kept"><Icon icon={Scissors} size={13}/>Apply trim</button>{trimmed&&<span className="vs-hint vs-warn">Trim not applied yet: saving now uses the whole {chosen.duration.toFixed(1)} s recording.</span>}</div>
    </div>:<p className="vs-empty-ref">Choose a recording above, record one, or import a file.</p>}
    {problem&&<p className="vs-error-inline" role="alert">{problem}</p>}
    <p className="vs-hint">WAV, MP3, FLAC. Originals are kept; edits make a new version.</p>
   </Step>
   <Step n="2" title="Exact reference transcript" note="Must match the recording word for word">
    <label className="vs-field"><span>Transcript</span><textarea aria-label="Exact reference transcript" rows="3" value={transcript} onChange={e=>onTranscript(e.target.value)} placeholder="Type exactly what is said in the reference recording."/></label>
    <div className="vs-ref-actions">{canTranscribe!==null&&<button className="vs-btn vs-btn-tint" disabled={!canTranscribe} onClick={onTranscribe}><Icon icon={Captions} size={14}/>Transcribe recording</button>}<span className="vs-hint">{transcribeReason||'Local faster-whisper. Review the words before saving.'}</span></div>
   </Step>
   <Step n="3" title="Save voice profile" note="Stays on this PC">
    <div className="vs-save-row"><label className="vs-field vs-grow"><span>Profile name</span><input aria-label="Profile name" value={profileName} maxLength={100} onChange={e=>onProfileName(e.target.value)}/></label>
     <button className="accent vs-generate" disabled={saveDisabled||!!problem} onClick={onSave}><Icon icon={Save} size={14} strokeWidth={2}/>Save voice</button></div>
    <p className="vs-hint">Profiles don't store a language; choose the language each time in Generate.</p>
   </Step>
  </div>{side}</div>}
  {tab==='design'&&<div className="vs-voices-grid"><div className="vs-voices-form">
   <section className="vs-card vs-step"><div className="vs-step-head"><span className="vs-step-n"><Icon icon={Sparkles} size={12}/></span><h2>Design a voice from a description</h2><span className="vs-grow"/><small>Synthetic · uses VoiceDesign</small></div>
    <p className="vs-hint">Create a synthetic voice sample, then listen and save it as a reusable reference in Clone. Descriptions do not change an existing cloned voice.</p>
    <label className="vs-field"><span>Voice description</span><textarea aria-label="Voice description" rows="3" value={description} maxLength={2000} onChange={e=>onDescription(e.target.value)} placeholder="Warm, friendly adult voice, slightly raspy, with a relaxed conversational pace."/></label>
    {assist&&<div><button className="vs-btn vs-btn-tint vs-sm" disabled={helpersDisabled} onClick={onShape}><Icon icon={WandSparkles} size={13}/>Shape description</button></div>}
    <label className="vs-field"><span>Sample words</span><textarea aria-label="Sample words" rows="2" value={sampleText} maxLength={1000} onChange={e=>onSampleText(e.target.value)}/></label>
    <div className="vs-save-row"><label className="vs-drop"><span>Language</span><select aria-label="Sample language" value={language} onChange={e=>onLanguage(e.target.value)}>{LANGUAGES.map(l=><option key={l}>{l}</option>)}</select><Icon icon={ChevronDown} size={13}/></label><span className="vs-grow"/>
     <button className="accent vs-generate" disabled={!canDesign} onClick={onDesign}><Icon icon={Sparkles} size={14} strokeWidth={2}/>Generate voice sample</button></div>
    {voiceDesignMissing&&<p className="vs-error-inline">Local VoiceDesign weights are missing. See AI-HELPERS.md.</p>}
    <p className="vs-hint">Switching between voice design and cloning reloads the GPU model. The first generation may take a minute. The sample opens in Clone so you can review its transcript and save it.</p>
   </section>
  </div>{side}</div>}
 </div>;
}

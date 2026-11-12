// Record & Edit screen from the new design (UI plan step 4): header actions, waveform editor card,
// effects card in 3 columns, version compare. Presentational only: state and handlers come from App in main.jsx.
// No Volume control: the backend Edit model has no gain parameter.
import React from 'react';
import {Icon,assetKind} from './Shell.jsx';
import {Mic,Square,Upload,FolderOpen,Download,Play,Pause,Check,ArrowLeftRight,AudioLines,Captions,Trash2,RotateCcw} from 'lucide';

export const DEFAULT_OPS={denoise:false,normalize:false,highpass:false,strength:.7,fade_in:0,fade_out:0,pitch:0,timbre:0,vibrato:0};
const signed=(v,d)=>(v>0?'+':v<0?'−':'')+Math.abs(v).toFixed(d);
const fmtSr=a=>[a.sample_rate?(a.sample_rate/1000).toFixed(a.sample_rate%1000?1:0)+' kHz':null,a.channels===1?'mono':a.channels===2?'stereo':a.channels?a.channels+' ch':null].filter(Boolean).join(' ');

export function EditActions({recording,micPending,recordDisabled,onRecord,onStopRecording,importDisabled,onImport,onChoose}){
 return <div className="vs-head-actions">
  <button className="vs-btn vs-only-narrow" onClick={onChoose}><Icon icon={FolderOpen} size={14}/>Choose recording</button>
  <label className={'vs-btn'+(importDisabled?' disabled':'')}><Icon icon={Upload} size={14}/>Import audio<input type="file" aria-label="Import audio" accept=".wav,.mp3,.flac,audio/*" disabled={importDisabled} onChange={e=>{onImport(e.target.files[0]);e.target.value=''}}/></label>
  {recording?<button className="danger vs-rec" onClick={onStopRecording}><Icon icon={Square} size={13}/>Stop recording</button>
   :<button className="accent vs-rec" disabled={recordDisabled} onClick={onRecord}><Icon icon={Mic} size={14} strokeWidth={2}/>{micPending?'Waiting for microphone…':'Record microphone'}</button>}
 </div>;
}

function Toggle({label,note,checked,onChange}){
 return <label className="vs-toggle"><input type="checkbox" role="switch" checked={checked} onChange={e=>onChange(e.target.checked)}/><i aria-hidden="true"/><span>{label}</span>{note&&<small>{note}</small>}</label>;
}
function Slider({label,value,min,max,step,format,onChange,disabled}){
 const pct=((value-min)/(max-min))*100;
 return <label className={'vs-slider'+(disabled?' dim':'')}><span className="vs-slider-top"><span>{label}</span><b>{format(value)}</b></span>
  <input type="range" min={min} max={max} step={step} value={value} style={{'--fill':pct+'%'}} onChange={e=>onChange(+e.target.value)}/></label>;
}

export function RecordEdit(p){
 const {asset,parentName,waveRef,compare,onCompare,playing,onPlay,onPlaySelection,onStop,trim,onTrim,ops,onOps,onReset,onApply,applyDisabled,
  comparison,onToggleComparison,onSaveReference,onSendTranscribe,folders,onMove,onDelete,actionsDisabled,generating,busy}=p;
 if(!asset)return <section className="vs-card vs-edit-empty"><h2>No recording selected</h2><p>Choose a recording in the Recordings panel, import a file, or record the microphone. WAV, MP3 and FLAC work; originals are always kept, and edits make a new version.</p>{generating&&<p>Recording is unavailable while speech is generating.</p>}<p className="vs-hint">Your browser may ask for microphone permission.</p></section>;
 const kind=assetKind(asset),viewingBefore=compare==='before'&&!!asset.parent,set=(k,v)=>onOps({...ops,[k]:v});
 const changed=JSON.stringify(ops)!==JSON.stringify(DEFAULT_OPS);
 return <>
  <section className="vs-card vs-editor" aria-label="Waveform editor">
   <div className="vs-editor-head">
    <h2 title={asset.name}>{asset.name}</h2>
    <em className={'vs-badge '+kind.toLowerCase()}>{kind==='Edited'?'Edited version':kind}</em>
    <small>{[asset.duration.toFixed(1)+' s',fmtSr(asset)].filter(Boolean).join(' · ')}</small>
    <span className="vs-grow"/>
    <div className="vs-seg" role="group" aria-label="Before or after this edit" title={asset.parent?'Before = '+(parentName||'the version this was made from'):'This recording has no earlier version'}>
     <button aria-pressed={viewingBefore} disabled={!asset.parent} onClick={()=>onCompare('before')}>Before</button>
     <button aria-pressed={!viewingBefore} onClick={()=>onCompare('after')}>After</button>
    </div>
    <a className="vs-btn" href={'/api/assets/'+asset.id+'/audio'} download><Icon icon={Download} size={14}/>Download WAV</a>
   </div>
   <div className={'vs-wave-area'+(viewingBefore?' before':'')}><div className="vs-big-wave" ref={waveRef}/></div>
   {viewingBefore&&<p className="vs-hint">Showing the earlier version{parentName?' “'+parentName+'”':''}. Switch to After to trim and apply effects.</p>}
   <div className="vs-editor-controls">
    <button className="vs-btn" onClick={onPlay}><Icon icon={playing?Pause:Play} size={14}/>{playing?'Pause':'Play'}</button>
    <button className="vs-btn vs-btn-tint" disabled={viewingBefore} onClick={onPlaySelection}><Icon icon={Play} size={14}/>Play selection</button>
    <button className="vs-btn" onClick={onStop}><Icon icon={Square} size={13}/>Stop</button>
    <span className="vs-hint">Drag the handles to trim</span>
    <span className="vs-grow"/>
    <label className="vs-num"><span>In</span><input type="number" aria-label="In (seconds)" step=".01" min="0" value={trim.start} onChange={e=>onTrim('start',e.target.value)}/><i>s</i></label>
    <label className="vs-num"><span>Out</span><input type="number" aria-label="Out (seconds)" step=".01" min="0" value={trim.end} onChange={e=>onTrim('end',e.target.value)}/><i>s</i></label>
   </div>
   <div className="vs-editor-foot">
    <label className="vs-drop vs-folder"><span>Folder</span><select aria-label="Assign selected recording folder" value={asset.folder||''} disabled={busy} onChange={e=>onMove(e.target.value)}><option value="">Unfiled</option>{folders.map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
    <span className="vs-grow"/>
    <button className="vs-btn vs-danger-ghost" disabled={actionsDisabled} onClick={onDelete} title="Delete this recording (Delete key)"><Icon icon={Trash2} size={14}/>Delete recording</button>
   </div>
  </section>
  <section className="vs-card vs-effects" aria-label="Effects">
   <div className="vs-effects-head"><h2>Effects</h2><span className="vs-hint">Non-destructive · every apply makes a new version</span><span className="vs-grow"/><button className="vs-link" disabled={!changed} onClick={onReset}><Icon icon={RotateCcw} size={12}/>Reset</button></div>
   <div className="vs-effects-grid">
    <div className="vs-fx-col"><h3>CLEAN UP</h3>
     <Toggle label="Noise reduction" checked={ops.denoise} onChange={v=>set('denoise',v)}/>
     <Slider label="Strength" value={ops.strength} min={0} max={1} step={.05} format={v=>v.toFixed(2)} onChange={v=>set('strength',v)} disabled={!ops.denoise}/>
     <Toggle label="High-pass 80 Hz" note="cuts rumble" checked={ops.highpass} onChange={v=>set('highpass',v)}/>
     <Toggle label="Peak normalize" note="−1 dBFS" checked={ops.normalize} onChange={v=>set('normalize',v)}/>
    </div>
    <div className="vs-fx-col"><h3>FADES</h3>
     <Slider label="Fade in" value={ops.fade_in} min={0} max={10} step={.05} format={v=>v.toFixed(2)+' s'} onChange={v=>set('fade_in',v)}/>
     <Slider label="Fade out" value={ops.fade_out} min={0} max={10} step={.05} format={v=>v.toFixed(2)+' s'} onChange={v=>set('fade_out',v)}/>
    </div>
    <div className="vs-fx-col"><h3>VOICE SHAPING</h3>
     <Slider label="Pitch" value={ops.pitch} min={-12} max={12} step={.5} format={v=>signed(v,1)+' st'} onChange={v=>set('pitch',v)}/>
     <Slider label="Timbre" value={ops.timbre} min={-1} max={1} step={.05} format={v=>signed(v,2)} onChange={v=>set('timbre',v)}/>
     <Slider label="Vibrato" value={ops.vibrato} min={0} max={1} step={.05} format={v=>v.toFixed(2)} onChange={v=>set('vibrato',v)}/>
    </div>
   </div>
   <div className="vs-effects-actions">
    <button className="accent vs-generate" disabled={applyDisabled||viewingBefore} onClick={onApply}><Icon icon={Check} size={14} strokeWidth={2}/>Apply trim & effects</button>
    <button className="vs-btn" aria-pressed={comparison} disabled={!asset.parent} title={asset.parent?'Play the earlier and this version side by side':'Available after applying an edit'} onClick={onToggleComparison}><Icon icon={ArrowLeftRight} size={14}/>Compare before / after</button>
    <span className="vs-grow"/>
    <button className="vs-btn" onClick={onSaveReference}><Icon icon={AudioLines} size={14}/>Save as voice reference</button>
    <button className="vs-btn" onClick={onSendTranscribe}><Icon icon={Captions} size={14}/>Send to Transcribe</button>
   </div>
   {comparison&&asset.parent&&<div className="vs-comparison"><label>Before{parentName?' · '+parentName:''}<audio controls src={'/api/assets/'+asset.parent+'/audio'}/></label><label>After · {asset.name}<audio controls src={'/api/assets/'+asset.id+'/audio'}/></label></div>}
   <p className="vs-hint">Apply always creates a new recording linked to this one; the original is never changed. Timeline trims in Arrange never alter files.</p>
  </section>
 </>;
}

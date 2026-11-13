// App shell from the new design (UI plan step 2): icon sidebar, recordings panel, bottom player.
// Presentational components only: all state and handlers come from App in main.jsx.
import React,{useEffect,useRef,useState} from 'react';
import WaveSurfer from 'wavesurfer.js';
import {Users,Sparkles,AudioWaveform,Captions,Rows3,Film,Settings,Cpu,Play,Pause,Download,Upload,FolderPlus,Search,Pencil,ListPlus} from 'lucide';

const camel=k=>k.replace(/-([a-z])/g,(_,c)=>c.toUpperCase());
export function Icon({icon,size=20,strokeWidth=1.5,className}){
 const [,attrs,children]=icon;
 return <svg {...Object.fromEntries(Object.entries(attrs).map(([k,v])=>[camel(k),v]))} width={size} height={size} strokeWidth={strokeWidth} className={className} aria-hidden="true" focusable="false">{children.map(([tag,a],i)=>React.createElement(tag,{key:i,...Object.fromEntries(Object.entries(a).map(([k,v])=>[camel(k),v]))}))}</svg>;
}

export const NAV=[
 ['voices','Voices',Users],
 ['generate','Generate',Sparkles],
 ['edit','Record & Edit',AudioWaveform],
 ['transcribe','Transcribe',Captions],
 ['arrange','Arrange',Rows3],
 ['video','Video',Film],
];

export function SideNav({view,onNavigate,health}){
 const inference=health?.inference?.status;
 const state=!health?'checking':inference==='ready'?'ready':'offline';
 const label={checking:'Checking',ready:'Ready',offline:'Offline'}[state];
 return <aside className="vs-side" aria-label="Primary navigation">
  <button className="vs-logo" aria-label="Alibi: go to Generate" onClick={()=>onNavigate('generate')}><Icon icon={AudioWaveform} size={22} strokeWidth={2}/></button>
  <nav className="vs-side-links">{NAV.map(([key,text,icon])=><button key={key} className={view===key?'active':''} aria-current={view===key?'page':undefined} onClick={()=>onNavigate(key)}><Icon icon={icon}/><span>{text}</span></button>)}</nav>
  <div className="vs-side-foot">
   <div className={'vs-model '+state} role="status" title={state==='ready'?'Inference worker ready'+(health?.inference?.model?' ('+health.inference.model+' model)':''):state==='offline'?'Inference worker unavailable':'Checking inference worker'}><span className="vs-model-row"><i/><Icon icon={Cpu} size={14}/></span><span>Models</span><b>{label}</b></div>
   <span className="vs-settings-wrap" title="Settings: coming soon"><button className="vs-settings" disabled aria-disabled="true"><Icon icon={Settings}/><span>Settings</span></button></span>
  </div>
 </aside>;
}

export const assetKind=a=>a.parent?'Edited':a.synthetic?'Synthetic':a.profile?'Generated':'Original';
const ago=t=>{if(!t)return '';const s=Date.now()/1000-t;if(s<60)return 'just now';if(s<3600)return Math.floor(s/60)+' min ago';if(s<86400)return Math.floor(s/3600)+' h ago';if(s<172800)return 'Yesterday';return new Date(t*1000).toLocaleDateString()};
const clock=s=>{if(!isFinite(s))return '0:00';const m=Math.floor(s/60),r=Math.floor(s%60);return m+':'+String(r).padStart(2,'0')};

export function RecordingsPanel({assets,total,selected,onSelect,search,onSearch,folders,folderFilter,onFolderFilter,onImport,onCreateFolder,disabled,children}){
 return <aside className="vs-panel" aria-label="Recordings">
  <div className="vs-panel-head"><h2>Recordings <span className="vs-count">{total}</span></h2><div className="vs-panel-actions">
   <label className={'vs-icon-btn'+(disabled?' disabled':'')} title="Import audio"><Icon icon={Upload} size={16}/><input type="file" aria-label="Import audio from recordings panel" accept=".wav,.mp3,.flac,audio/*" disabled={disabled} onChange={e=>{onImport(e.target.files[0]);e.target.value=''}}/></label>
   <button className="vs-icon-btn" title="Create folder" aria-label="Create folder" onClick={onCreateFolder}><Icon icon={FolderPlus} size={16}/></button>
  </div></div>
  <label className="vs-search"><Icon icon={Search} size={14}/><input type="search" aria-label="Search recordings in panel" placeholder="Search recordings" value={search} onChange={e=>onSearch(e.target.value)}/></label>
  <div className="vs-filters"><select aria-label="Filter recordings by folder" value={folderFilter} onChange={e=>onFolderFilter(e.target.value)}><option value="">All folders</option><option value="__unfiled">Unfiled</option>{folders.map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></div>
  {children}
  <div className="vs-asset-list">{assets.map(a=>{const kind=assetKind(a),on=a.id===selected;return <button key={a.id} className={'vs-asset'+(on?' selected':'')} aria-pressed={on} onClick={()=>onSelect(a.id)}>
   <span className="vs-asset-play"><Icon icon={Play} size={12} strokeWidth={2}/></span>
   <span className="vs-asset-text"><b>{a.name}</b><small>{[kind==='Generated'||kind==='Synthetic'?null:a.original?'Imported':null,a.duration.toFixed(1)+' s',ago(a.created)].filter(Boolean).join(' · ')}</small></span>
   <em className={'vs-badge '+kind.toLowerCase()}>{kind}</em>
  </button>})}{!assets.length&&<p className="vs-empty">No recordings found.</p>}</div>
 </aside>;
}

export function TransportBar({asset,playerRef,onEdit,onAdd,tracks,track,onTrack,onError}){
 const waveEl=useRef(),[playing,setPlaying]=useState(false),[time,setTime]=useState(0),[length,setLength]=useState(0);
 const src=asset?'/api/assets/'+asset.id+'/audio':undefined;
 useEffect(()=>{
  setPlaying(false);setTime(0);setLength(asset?.duration||0);
  if(!asset||!waveEl.current||!playerRef.current)return;
  // Real waveform, bound to the same <audio> element the bar plays.
  const w=WaveSurfer.create({container:waveEl.current,media:playerRef.current,height:34,barWidth:2,barGap:2,barRadius:1,normalize:true,waveColor:'#3a3f49',progressColor:'#ff6a3d',cursorColor:'#ff6a3d',cursorWidth:1});
  w.on('error',e=>{if(e?.name==='AbortError')return;onError?.('Player waveform: '+(e?.message||e))});
  return ()=>w.destroy();
 },[asset?.id]);
 const toggle=()=>{const p=playerRef.current;if(!p)return;if(p.paused)p.play().catch(e=>onError?.(e.message));else p.pause()};
 return <div className="vs-transport" aria-label="Player">
  <audio ref={playerRef} src={src} preload="metadata" onPlay={()=>setPlaying(true)} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} onTimeUpdate={e=>setTime(e.currentTarget.currentTime)} onLoadedMetadata={e=>setLength(e.currentTarget.duration)}/>
  <button className="vs-play" aria-label={playing?'Pause':'Play'} disabled={!asset} onClick={toggle}><Icon icon={playing?Pause:Play} size={18} strokeWidth={2}/></button>
  <div className="vs-now"><b>{asset?.name||'No recording selected'}</b><small>{asset?asset.duration.toFixed(1)+' s · '+(assetKind(asset)==='Original'?'Original input':assetKind(asset)==='Edited'?'Edited version':assetKind(asset)):'Choose a recording, import audio, or generate speech.'}</small></div>
  <span className="vs-time">{asset?clock(time):'–'}</span>
  <div className="vs-wave" ref={waveEl} aria-hidden="true">{!asset&&<span className="vs-wave-empty"/>}</div>
  <span className="vs-time">{asset?clock(length):'–'}</span>
  <button className="vs-btn" disabled={!asset} onClick={onEdit}><Icon icon={Pencil} size={14}/>Edit</button>
  <label className="vs-track"><span>Track</span><select aria-label="Destination track" value={track} onChange={e=>onTrack(e.target.value)}>{tracks.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label>
  <button className="vs-btn vs-btn-tint" disabled={!asset} onClick={onAdd}><Icon icon={ListPlus} size={14}/>Add to Arrange</button>
  <a className={'vs-icon-btn'+(asset?'':' disabled')} href={src} download={asset?asset.name+'.wav':undefined} aria-label="Download WAV" title="Download WAV" aria-disabled={!asset}><Icon icon={Download} size={16}/></a>
 </div>;
}

export function Placeholder({title,children}){
 return <section className="panel vs-placeholder"><h2>{title}</h2>{children}</section>;
}

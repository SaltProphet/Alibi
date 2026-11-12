import React, {useEffect, useRef, useState} from 'react';
import './video-workspace.css';

export default function VideoWorkspace({active, api, profiles, disabled, onGenerating, refresh}) {
 const [videos,setVideos]=useState([]),[video,setVideo]=useState(null),[project,setProject]=useState(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('Import a silent MP4 or WebM to begin.'),[exported,setExported]=useState(null),[pending,setPending]=useState(null),[time,setTime]=useState(0);
 const player=useRef(null), rendered=useRef(null), drag=useRef(null), mounted=useRef(true), audioContext=useRef(null), sources=useRef([]), rangeEnd=useRef(null);
 const blocked=disabled||busy;
 const valid=video&&project&&Number.isFinite(project.start)&&project.start>=0&&project.end>project.start&&project.end<=video.duration;
 function stopAudio(){sources.current.forEach(s=>{try{s.stop()}catch{}});sources.current=[];audioContext.current?.close();audioContext.current=null}
 function stop(){player.current?.pause();rendered.current?.pause();stopAudio();rangeEnd.current=null}
 useEffect(()=>{mounted.current=true;api('/videos').then(v=>{if(mounted.current){setVideos(v);if(v.length){setVideo(v[0]);setProject(v[0].project)}}}).catch(e=>setError(e.message));return()=>{mounted.current=false;stop()}},[]);
 useEffect(()=>{if(!active)stop()},[active]);
 function choose(v){stop();setVideo(v);setProject(v.project);setPending(null);setExported(null);setError('');setTime(0)}
 function update(patch){stop();setProject(p=>({...p,...patch}));setExported(null)}
 async function action(fn){if(blocked)return;setBusy(true);setError('');try{await fn()}catch(e){setError(e.message);setStatus('Action failed. Your video and completed recordings are retained.')}finally{if(mounted.current)setBusy(false)}}
 async function save(next=project){const v=await api('/videos/'+video.id+'/project',next);setVideo(v);setVideos(list=>list.map(x=>x.id===v.id?v:x));setProject(v.project);return v}
 async function importFile(file){if(!file)return;await action(async()=>{stop();setStatus('Importing video…');const f=new FormData();f.append('file',file);const v=await api('/videos/import',f);setVideos(list=>[v,...list]);choose(v);setStatus('Video imported. Select a narration range below. Original file retained.')})}
 function selectPointer(e){if(blocked||!video||e.button!==0)return;stop();const r=e.currentTarget.getBoundingClientRect();const at=x=>Math.max(0,Math.min(video.duration,(x-r.left)/r.width*video.duration));const start=at(e.clientX);drag.current={start,at};e.currentTarget.setPointerCapture(e.pointerId)}
 function movePointer(e){if(!drag.current)return;const {start,at}=drag.current,end=at(e.clientX);if(Math.abs(end-start)>.02){setProject(p=>({...p,start:Math.min(start,end),end:Math.max(start,end)}));setExported(null)}}
 function endPointer(e){movePointer(e);drag.current=null}
 async function place(asset){
  if(!valid)throw Error('Choose a valid video range first.');
  if(asset.duration>project.end-project.start+.001){setPending(asset);throw Error('Speech is '+asset.duration.toFixed(2)+'s, longer than the selected range. Widen the range and place the saved take, or shorten the text and generate again.');}
  const next={...project,clips:[...project.clips,{id:crypto.randomUUID(),asset:asset.id,at:project.start,end:project.end}]};
  await save(next);setPending(null);setExported(null);setStatus('Narration placed at '+project.start.toFixed(2)+'s. Project saved.');
 }
 async function generate(){await action(async()=>{
  stop();onGenerating(true);setStatus('Generating narration locally…');
  try{await save();const j=await api('/generate',{profile:project.profile,text:project.text.trim(),language:'English'});
   for(;;){const result=await api('/jobs/'+j.id);if(result.status==='failed')throw Error(result.error);if(result.status==='complete'){await refresh();if(mounted.current)await place(result.asset);break}await new Promise(r=>setTimeout(r,1200));if(!mounted.current)break}
  }finally{onGenerating(false)}
 })}
 async function preview(){await action(async()=>{
  stop();const target=project.start;if(Math.abs(player.current.currentTime-target)>.001){await new Promise(resolve=>{player.current.addEventListener('seeked',resolve,{once:true});player.current.currentTime=target})}const ctx=new AudioContext();audioContext.current=ctx;await ctx.resume();
  try{
   const clips=await Promise.all(project.clips.map(async c=>{const response=await fetch('/api/assets/'+c.asset+'/audio');if(!response.ok)throw Error('Narration audio unavailable');return [c,await ctx.decodeAudioData(await response.arrayBuffer())]}));
   if(audioContext.current!==ctx)return;
   const start=project.start,end=project.end;rangeEnd.current=end;await player.current.play();
   for(const [c,buffer] of clips){const offset=Math.max(0,start-c.at),when=Math.max(0,c.at-start),length=Math.min(buffer.duration-offset,end-Math.max(start,c.at));if(length<=0)continue;const source=ctx.createBufferSource();source.buffer=buffer;source.connect(ctx.destination);source.start(ctx.currentTime+when,offset,length);sources.current.push(source)}
   setStatus('Playing selected range with narration.');
  }catch(e){stop();throw e}
 })}
 return <section className="panel video-workspace" hidden={!active} aria-label="Video workspace">
  <div className="section"><div><h2>Video narration</h2><p className="muted">Import a video, select a range, then add a saved voice.</p></div><label className="upload">Import video<input aria-label="Import video" type="file" accept=".mp4,.webm,video/mp4,video/webm" disabled={blocked} onChange={e=>{importFile(e.target.files[0]);e.target.value=''}}/></label></div>
  {error&&<div className="error" role="alert">{error}<button onClick={()=>setError('')}>Dismiss video error</button></div>}
  <p role="status">{status}</p>
  {!!videos.length&&<label>Open video project<select aria-label="Open video project" value={video?.id||''} disabled={blocked} onChange={e=>choose(videos.find(v=>v.id===e.target.value))}>{videos.map(v=><option key={v.id} value={v.id}>{v.name}</option>)}</select></label>}
  {video&&project&&<>
   <p className="muted">{video.name} · Duration: {video.duration.toFixed(2)} seconds · {video.width} × {video.height}</p>
   {video.has_audio&&<p className="muted">This video contains audio. Export uses the video picture and your narration only.</p>}
   <video aria-label="Source video preview" ref={player} controls muted playsInline preload="metadata" src={video.url} onError={()=>setError('Your browser cannot preview this video codec. Try an H.264 MP4 or VP9 WebM.')} onSeeking={()=>{stopAudio()}} onPause={stopAudio} onTimeUpdate={e=>{setTime(e.currentTarget.currentTime);if(rangeEnd.current!==null&&e.currentTarget.currentTime>=rangeEnd.current)stop()}}/>
   <div className="video-timeline" aria-label="Video range timeline" onPointerDown={selectPointer} onPointerMove={movePointer} onPointerUp={endPointer} onPointerCancel={()=>{drag.current=null}}>
    <div className="video-range" style={{left:100*project.start/video.duration+'%',width:100*(project.end-project.start)/video.duration+'%'}}/>
    {project.clips.map((c,i)=><div className="video-take" key={c.id} title={'Narration '+(i+1)} style={{left:100*c.at/video.duration+'%',width:100*(c.end-c.at)/video.duration+'%'}}>Voice {i+1}</div>)}
    <div className="video-playhead" style={{left:100*time/video.duration+'%'}}/>
   </div><p className="muted">Drag across the timeline to select a range, or enter exact times. Green blocks show narration ranges.</p>
   <div className="row"><label>Range start (seconds)<input aria-label="Video range start" type="number" min="0" max={video.duration} step=".01" disabled={blocked} value={project.start} onChange={e=>update({start:Number(e.target.value)})}/></label><label>Range end (seconds)<input aria-label="Video range end" type="number" min="0" max={video.duration} step=".01" disabled={blocked} value={project.end} onChange={e=>update({end:Number(e.target.value)})}/></label><button disabled={blocked||!valid} onClick={preview}>Play range with narration</button><button onClick={stop}>Stop video</button></div>
   {!valid&&<p role="alert">Range start must be before its end and both must be inside the video.</p>}
   <label>Narration text<textarea aria-label="Video narration text" rows="4" maxLength={10000} disabled={blocked} value={project.text} onChange={e=>update({text:e.target.value})}/></label>
   <label>Saved voice<select aria-label="Video saved voice" disabled={blocked} value={project.profile} onChange={e=>update({profile:e.target.value})}><option value="">Choose a saved voice</option>{profiles.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
   {!profiles.length&&<p className="muted">Save a voice reference in Record & edit first.</p>}
   <div className="row"><button className="accent" disabled={blocked||!valid||!project.text.trim()||!profiles.some(p=>p.id===project.profile)} onClick={generate}>Generate & place narration</button><button disabled={blocked||!valid} onClick={()=>action(async()=>{await save();setStatus('Video project saved.')})}>Save video project</button><button disabled={blocked||!valid||!project.clips.length} onClick={()=>action(async()=>{stop();setStatus('Rendering MP4 locally…');const result=await api('/videos/'+video.id+'/export',project);await save();setExported(result);setStatus('MP4 ready. Preview it below or download.')})}>Export narrated MP4</button></div>
   <p className="muted">Speech starts at the range start at its natural speed. Short takes leave silence; longer takes must be placed in a wider range. Overlapping clips are mixed. Generation uses English.</p>
   {pending&&<div className="video-pending"><p>Saved take: {pending.duration.toFixed(2)} seconds</p><audio controls src={'/api/assets/'+pending.id+'/audio'}/><button disabled={blocked||!valid} onClick={()=>action(()=>place(pending))}>Place saved take in current range</button></div>}
   {project.clips.map((c,i)=><div className="video-clip-row" key={c.id}><p>Narration {i+1} · {c.at.toFixed(2)}–{c.end.toFixed(2)}s</p><audio controls src={'/api/assets/'+c.asset+'/audio'}/><button disabled={blocked} onClick={()=>action(async()=>{stop();await save({...project,clips:project.clips.filter(x=>x.id!==c.id)});setExported(null);setStatus('Narration removed. Original recording retained.')})}>Remove narration {i+1}</button></div>)}
   {exported&&<div className="video-export"><h3>Rendered video with narration</h3><video aria-label="Rendered narration preview" ref={rendered} controls playsInline src={exported.url}/><a href={exported.url} download>Download narrated MP4</a></div>}
  </>}
 </section>
}

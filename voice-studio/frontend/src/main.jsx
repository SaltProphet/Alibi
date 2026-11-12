import React,{useEffect,useRef,useState} from 'react';
import {createRoot} from 'react-dom/client';
import WaveSurfer from 'wavesurfer.js';
import Regions from 'wavesurfer.js/dist/plugins/regions.esm.js';
import Timeline from 'wavesurfer.js/dist/plugins/timeline.esm.js';
import './style.css';
import './studio-theme.css';
import AssistDialog from './AssistDialog.jsx';
import VideoWorkspace from './VideoWorkspace.jsx';
import './immersive-shell.css';
import {SideNav,RecordingsPanel,TransportBar,Placeholder} from './Shell.jsx';
import './shell.css';
import {GenerateView,JobCard,modelInfo} from './GenerateView.jsx';
import './generate.css';
import {RecordEdit,EditActions,DEFAULT_OPS} from './RecordEdit.jsx';
import {VoicesView} from './VoicesView.jsx';
import './voices.css';
import './record-edit.css';
const id=()=>crypto.randomUUID();
const empty=()=>({name:'Untitled session',tracks:[{id:id(),name:'Voice 1',volume:1,mute:false},{id:id(),name:'Voice 2',volume:1,mute:false}],clips:[]});
async function api(path,body){const r=await fetch('/api'+path,body instanceof FormData?{method:'POST',body}:body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});if(!r.ok){let e;try{e=await r.json()}catch{e={detail:r.statusText}}throw Error(typeof e.detail==='string'?e.detail:JSON.stringify(e.detail))}return r.json()}
function App(){
 const [view,setView]=useState('generate'),[generating,setGenerating]=useState(false),[micPending,setMicPending]=useState(false),[drawerOpen,setDrawerOpen]=useState(false),[search,setSearch]=useState(''),[referenceOpen,setReferenceOpen]=useState(false),[voicesTab,setVoicesTab]=useState('saved'),[highlight,setHighlight]=useState(''),[sequence,setSequence]=useState(()=>{try{const d=JSON.parse(localStorage.getItem('auravoice-dialogue')||'[]');if(Array.isArray(d)&&d.length)return d.map(t=>({id:t.id||id(),profile:t.profile||'',text:t.text||''}))}catch{}return [{id:id(),profile:'',text:''}]}),[sequenceOpen,setSequenceOpen]=useState(false);
 const [videoGenerating,setVideoGenerating]=useState(false),[progress,setProgress]=useState(null),[compare,setCompare]=useState('after'),[comparison,setComparison]=useState(false),[wavePlaying,setWavePlaying]=useState(false);
 const openTools=(assetId)=>{if(assetId)choose(assetId);navigate('edit')};
 const [assets,setAssets]=useState([]),[folders,setFolders]=useState([]),[folderFilter,setFolderFilter]=useState(''),[selected,setSelected]=useState(null),[profiles,setProfiles]=useState([]),[sessions,setSessions]=useState([]),[profile,setProfile]=useState(''),[session,setSession]=useState(empty),[error,setError]=useState(''),[status,setStatus]=useState('Ready'),[busy,setBusy]=useState(false),[recording,setRecording]=useState(false),[transcript,setTranscript]=useState(''),[profileName,setProfileName]=useState('My voice'),[text,setText]=useState(''),[language,setLanguage]=useState('English'),[health,setHealth]=useState(null),[before,setBefore]=useState(null),[result,setResult]=useState(null),[exported,setExported]=useState(null),[trim,setTrim]=useState({start:0,end:0}),[ops,setOps]=useState(DEFAULT_OPS),[playing,setPlaying]=useState(false),[track,setTrack]=useState(''),[job,setJob]=useState(null);
 const [assistTarget,setAssistTarget]=useState(null),[capabilities,setCapabilities]=useState(null),[description,setDescription]=useState(''),[sampleText,setSampleText]=useState('Hello, welcome to the studio. Let us bring this story to life.');
 const latestAssist=useRef();
 latestAssist.current={text,transcript,description,sequence,selected};
 const helpersDisabled=busy||generating||recording||micPending;
 function openWand(kind,source,key){setAssistTarget({kind,source,key,language,label:kind==='voice'?'Shape voice description':kind==='dialogue'?'Rewrite dialogue block':'Draft script',context:kind==='dialogue'?sequence.map((t,i)=>'Block '+(i+1)+': '+t.text).join('\n').slice(0,6000):''})}
 function applySuggestion(value,destination){
  const t=assistTarget,c=latestAssist.current;
  const current=t.kind==='script'?c.text:t.kind==='voice'?c.description:t.kind==='dialogue'?c.sequence.find(b=>b.id===t.key)?.text:c.transcript;
  if(current!==t.source||(t.kind==='transcript'&&c.selected!==t.asset)){setError('The source changed while the assistant was open. Copy the suggestion or close and try again.');return}
  if(t.kind==='script')setText(value);
  else if(t.kind==='voice')setDescription(value);
  else if(t.kind==='dialogue')setSequence(q=>q.map(b=>b.id===t.key?{...b,text:value}:b));
  else if(destination==='script'){setText(value);navigate('generate')}
  else {setTranscript(value);setReferenceOpen(true)}
  setAssistTarget(null);setStatus('Suggestion applied. Review before generating or saving.');
 }
 async function designVoice(){
  if(helpersDisabled)return;
  setGenerating(true);setError('');setStatus('Designing voice locally…');
  try{
   const j=await api('/assist/voice-design',{description,text:sampleText,language});
   let a;
   for(;;){const v=await api('/jobs/'+j.id);if(v.status==='failed')throw Error(v.error);if(v.status==='complete'){a=v.result;break}await new Promise(r=>setTimeout(r,1200))}
   await refresh();setSelected(a.id);setTrim({start:0,end:a.duration});setTranscript(sampleText);setProfileName('Designed voice');setVoicesTab('clone');navigate('voices');setStatus('Voice sample saved. Listen and review its transcript, then save a voice reference.');
  }catch(e){setError(e.message);setStatus('Voice design failed')}finally{setGenerating(false)}
 }
 const waveEl=useRef(),wave=useRef(),region=useRef(),rec=useRef(),stream=useRef(),chunks=useRef([]),mixContext=useRef(),sources=useRef([]),drag=useRef(null),timer=useRef(),draftTrims=useRef({}),drawer=useRef(),drawerTrigger=useRef(),drawerReturn=useRef(),player=useRef(),stopSequence=useRef(false),mounted=useRef(true),micAttempt=useRef(0);
 const chosen=assets.find(a=>a.id===selected);
 const viewRef=useRef(view);viewRef.current=view;
 const visibleAssets=assets.filter(a=>(!folderFilter||(folderFilter==='__unfiled'&&!a.folder)||a.folder===folderFilter)&&a.name.toLowerCase().includes(search.toLowerCase()));
 const refresh=async()=>{const [a,f,p,s]=await Promise.all([api('/assets'),api('/folders'),api('/profiles'),api('/sessions')]);setAssets(a);setFolders(f);setProfiles(p);setSessions(s)};
 const work=async(fn)=>{setError('');setBusy(true);try{await fn()}catch(e){setError(e.message);setStatus('Action failed')}finally{setBusy(false)}};
 const currentTrim=()=>draftTrims.current[selected]||{start:0,end:chosen?.duration||0};
 function choose(assetId){setSelected(assetId);setTrim(draftTrims.current[assetId]||{start:0,end:assets.find(a=>a.id===assetId)?.duration||0})}
 async function deleteAsset(assetId){const a=assets.find(x=>x.id===assetId);if(!a)return;if(!window.confirm(`Delete “${a.name}”? This removes the recording and its original file. This cannot be undone.`))return;await work(async()=>{const r=await fetch('/api/assets/'+assetId,{method:'DELETE'});if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw Error(e.detail||r.statusText)};if(selected===assetId){setSelected(null);setBefore(null);setTrim({start:0,end:0})}await refresh();setStatus('Recording deleted')})}
 async function createFolder(){const name=window.prompt('Folder name');if(!name?.trim())return;await work(async()=>{const f=await api('/folders',{name:name.trim()});await refresh();setFolderFilter(f.id);setStatus('Folder created')})}
 async function moveAsset(assetId,folder){await work(async()=>{await api('/assets/'+assetId+'/folder',{folder});await refresh();setStatus('Recording moved')})}
 function silence(except){document.querySelectorAll('audio,video').forEach(a=>{if(a!==except)a.pause()});if(wave.current?.getMediaElement()!==except)wave.current?.pause();stopMix()}
 function navigate(next){silence();setView(next);window.scrollTo(0,0)}
 useEffect(()=>{mounted.current=true;work(async()=>{await refresh();setHealth(await api('/health'));setCapabilities(await api('/assist/capabilities'))});const exclusive=e=>silence(e.target);document.addEventListener('play',exclusive,true);return()=>{mounted.current=false;micAttempt.current++;stream.current?.getTracks().forEach(t=>t.stop());clearTimeout(timer.current);sources.current.forEach(s=>{try{s.stop()}catch{}});document.removeEventListener('play',exclusive,true)}},[]);
 useEffect(()=>{try{localStorage.setItem('auravoice-dialogue',JSON.stringify(sequence))}catch{}},[sequence]);
 useEffect(()=>{if(!profile&&profiles.length)setProfile(profiles.find(p=>p.archetype==='nova')?.id||profiles[0].id)},[profiles,profile]);
 useEffect(()=>{const onKey=e=>{if(e.key!=='Delete'||view!=='edit'||!selected||recording||busy)return;const tag=e.target?.tagName?.toLowerCase();if(['input','textarea','select'].includes(tag))return;e.preventDefault();deleteAsset(selected)};window.addEventListener('keydown',onKey);return()=>window.removeEventListener('keydown',onKey)},[view,selected,recording,busy,assets]);
 useEffect(()=>{if(drawerOpen){drawer.current.showModal();drawer.current.querySelector('input')?.focus()}else if(drawer.current?.open){drawer.current.close();(drawerReturn.current||drawerTrigger.current)?.focus()}},[drawerOpen]);
 useEffect(()=>{setCompare('after');setComparison(false)},[selected]);
 useEffect(()=>{
  const cloneWave=view==='voices'&&voicesTab==='clone';
  if(!chosen||!(view==='edit'||cloneWave)||!waveEl.current)return;
  const showParent=!cloneWave&&compare==='before'&&chosen.parent;
  const selection=draftTrims.current[selected]||{start:0,end:chosen.duration};setTrim(selection);
  // Token colours: --vs-text-3-design bars, --vs-accent progress and selection, --vs-text-1 cursor.
  const regions=Regions.create(),timeline=Timeline.create({height:16,style:{color:'#7d838f',fontSize:'9px'}}),w=WaveSurfer.create({container:waveEl.current,waveColor:'#5c626d',progressColor:'#ff6a3d',cursorColor:'#eceef1',cursorWidth:1,height:cloneWave?72:110,barWidth:2,barGap:2,barRadius:1,normalize:true,plugins:[regions,timeline],url:'/api/assets/'+(showParent?chosen.parent:chosen.id)+'/audio'});wave.current=w;region.current=null;
  w.on('play',()=>{silence(w.getMediaElement());setWavePlaying(true)});w.on('pause',()=>setWavePlaying(false));w.on('finish',()=>setWavePlaying(false));w.on('decode',()=>{if(!showParent)region.current=regions.addRegion({...selection,color:'rgba(255,106,61,.14)',drag:false,resize:true})});
  regions.on('region-updated',r=>{const t={start:r.start,end:r.end};draftTrims.current[selected]=t;setTrim(t)});w.on('error',e=>{if(mounted.current)setError('Playback: '+e.message)});return()=>{w.destroy();wave.current=null;region.current=null;setWavePlaying(false)}
 },[selected,view,compare,voicesTab]);
 const updateTrim=(key,value)=>{const next={...trim,[key]:Number(value)};setTrim(next);draftTrims.current[selected]=next;if(next.start>=0&&next.end>next.start&&next.end<=chosen.duration)region.current?.setOptions(next)};
 async function upload(file){if(!file)return;const f=new FormData();f.append('file',file);setStatus('Importing audio…');const a=await api('/import',f);await refresh();setSelected(a.id);setTrim({start:0,end:a.duration});if(viewRef.current!=='voices')navigate('edit');setBefore(null);setStatus('Audio imported; original preserved')}
 async function startRecording(){
  if(generating||recording||micPending||busy)return;const attempt=++micAttempt.current;setMicPending(true);setError('');try{
   if(!navigator.mediaDevices?.getUserMedia)throw Error('Microphone recording requires a localhost browser with microphone support.');
   const inputStream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
   if(attempt!==micAttempt.current||!mounted.current){inputStream.getTracks().forEach(t=>t.stop());return}
   stream.current=inputStream;
   silence();const mime=['audio/webm;codecs=opus','audio/mp4'].find(t=>MediaRecorder.isTypeSupported(t));
   chunks.current=[];rec.current=new MediaRecorder(stream.current,mime?{mimeType:mime}:{});
   rec.current.ondataavailable=e=>{if(e.data.size)chunks.current.push(e.data)};
   rec.current.onstop=()=>{stream.current.getTracks().forEach(t=>t.stop());setRecording(false);const ext=rec.current.mimeType.includes('mp4')?'m4a':'webm';work(()=>upload(new File(chunks.current,'Recording-'+new Date().toISOString().replaceAll(':','-')+'.'+ext,{type:rec.current.mimeType})))};
   rec.current.start();setRecording(true);setStatus('Recording microphone…');
  }catch(e){if(attempt===micAttempt.current){stream.current?.getTracks().forEach(t=>t.stop());setError('Microphone: '+e.message)}}finally{if(attempt===micAttempt.current)setMicPending(false)}
 }
 async function saveProfile(){if(!chosen)throw Error('Select a reference recording first.');const p=await api('/profiles',{name:profileName,asset:chosen.id,transcript});await refresh();setProfile(p.id);setStatus('Voice profile saved')}
 async function waitJob(jid){for(;;){if(!mounted.current)throw Error('Studio closed');const j=await api('/jobs/'+jid);setJob(j);if(j.status==='failed')throw Error(j.error);if(j.status==='complete')return j.asset;await new Promise(r=>{timer.current=setTimeout(r,1200)})}}
 async function generate(useSequence=false){
  if(generating||recording||micPending||busy)return;
  const queue=useSequence?sequence.filter(t=>t.text.trim()).map(t=>({...t})):[{profile,text}];
  if(!queue.length||queue.some(t=>!t.text.trim()||!profiles.some(p=>p.id===t.profile))){setError('Choose a voice and enter text for each nonempty dialogue block.');return}
  setGenerating(true);stopSequence.current=false;setError('');silence();const clips=[];let at=0;
  try{for(let i=0;i<queue.length;i++){
   if(stopSequence.current)break;setProgress({i:i+1,n:queue.length});setStatus('Generating '+(i+1)+' / '+queue.length+'…');const j=await api('/generate',{profile:queue[i].profile,text:queue[i].text.trim(),language});const a=await waitJob(j.id);await refresh();setSelected(a.id);setTrim({start:0,end:a.duration});clips.push({id:id(),asset:a.id,track:'dialogue',at,in:0,out:a.duration});at+=a.duration;
  }
  if(!stopSequence.current&&clips.length>1){const saved=await api('/sessions',{name:'AuraVoice dialogue',tracks:[{id:'dialogue',name:'Dialogue',volume:1,mute:false}],clips});setSession(saved);setTrack('');setHighlight('');setExported(await api('/export',saved));await refresh()}
  setStatus(stopSequence.current?'Sequence stopped after the current job. Completed takes are saved.':'Speech generated');
  }catch(e){setError(e.message);setStatus('Generation failed. Completed takes remain in Recordings.')}finally{setGenerating(false);setProgress(null)}
 }
 const applyReferenceTrim=()=>work(async()=>{if(!chosen)return;setStatus('Trimming…');const a=await api('/assets/'+chosen.id+'/process',{...DEFAULT_OPS,...trim});await refresh();setSelected(a.id);setTrim({start:0,end:a.duration});setStatus('Trimmed copy created; original kept')}),cleanup=()=>work(async()=>{if(!chosen)return;setStatus('Processing…');const a=await api('/assets/'+chosen.id+'/process',{...ops,...trim});setBefore(chosen.id);await refresh();setSelected(a.id);setTrim({start:0,end:a.duration});setStatus('New edited version created')});
 function addClip(){if(!chosen)return;const t=currentTrim();if(!(t.end>t.start&&t.end<=chosen.duration+.002)){setError('Choose a valid trim before adding this recording.');return}const clipId=id();setSession(s=>{const tid=s.tracks.some(t=>t.id===track)?track:s.tracks[0].id;const at=Math.max(0,...s.clips.filter(c=>c.track===tid).map(c=>c.at+c.out-c.in));return {...s,clips:[...s.clips,{id:clipId,asset:chosen.id,track:tid,at,in:t.start,out:t.end}]}});setHighlight(clipId);setExported(null);navigate('arrange');setStatus('Clip appended to arrangement.')}

 function changeClip(cid,patch){setSession(s=>({...s,clips:s.clips.map(c=>c.id===cid?{...c,...patch}:c)}));setExported(null)}
 function beginClipDrag(e,c){
  if(e.button!==0)return;e.preventDefault();
  const node=e.currentTarget,rect=node.getBoundingClientRect(),offset=e.clientX-rect.left,startX=e.clientX,startY=e.clientY;
  node.style.zIndex='10';
  const move=ev=>{node.style.transform=`translate(${ev.clientX-startX}px,${ev.clientY-startY}px)`;};
  const up=ev=>{
   node.style.transform='';node.style.zIndex='';
   const lane=document.elementsFromPoint(ev.clientX,ev.clientY).find(el=>el.classList.contains('lane'));
   if(lane){const r=lane.getBoundingClientRect();changeClip(c.id,{track:lane.dataset.track,at:Math.round(Math.max(0,(ev.clientX-r.left-offset)/55)*100)/100})}
   window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',up);window.removeEventListener('pointercancel',cancel);
  };
  const cancel=()=>{node.style.transform='';node.style.zIndex='';window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',up);window.removeEventListener('pointercancel',cancel)};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',up);window.addEventListener('pointercancel',cancel);
 }
 function changeTrack(tid,patch){setSession(s=>({...s,tracks:s.tracks.map(t=>t.id===tid?{...t,...patch}:t)}));setExported(null)}
 function stopMix(){sources.current.forEach(s=>{try{s.stop()}catch{}});sources.current=[];mixContext.current?.close();mixContext.current=null;setPlaying(false)}
 async function playMix(){document.querySelectorAll('audio').forEach(a=>a.pause());wave.current?.pause();stopMix();setError('');try{const ctx=new AudioContext();mixContext.current=ctx;await ctx.resume();const decoded=await Promise.all(session.clips.map(async c=>{const response=await fetch('/api/assets/'+c.asset+'/audio');if(!response.ok)throw Error('Audio missing');return [c,await ctx.decodeAudioData(await response.arrayBuffer())]}));if(mixContext.current!==ctx)return;const start=ctx.currentTime+.1;let last=0;decoded.forEach(([c,buffer])=>{const t=session.tracks.find(t=>t.id===c.track);if(t.mute)return;const src=ctx.createBufferSource(),gain=ctx.createGain();src.buffer=buffer;gain.gain.value=t.volume;src.connect(gain).connect(ctx.destination);src.start(start+c.at,c.in,c.out-c.in);sources.current.push(src);last=Math.max(last,c.at+c.out-c.in)});setPlaying(true);setTimeout(()=>{if(mixContext.current===ctx)stopMix()},(last+.2)*1000)}catch(e){stopMix();setError(e.message)}}
 const duration=Math.max(15,...session.clips.map(c=>c.at+c.out-c.in+2));const scale=55;
 const chosenProfile=profiles.find(p=>p.id===profile);
 const pages={voices:['Voices','Clone a voice from a reference recording, design one from a description, or pick a saved profile.'],generate:['Generate','Type a line, pick a voice, generate. Runs locally, nothing leaves this PC.'],edit:['Record & Edit','Record or import, then trim and clean up. Originals are always kept.'],transcribe:['Transcribe','Local faster-whisper turns a recording into text. The audio is never changed.'],arrange:['Arrange','Lay takes out on tracks, balance them, export one mixed WAV.'],video:['Video','Add narration to a video using a local voice.']};
 const showPanel=['generate','edit','transcribe'].includes(view);
 const model=modelInfo(health),stopAfterCurrent=()=>{stopSequence.current=true;setStatus('Stopping after the current server job.')};
 const canGenerate=!(busy||generating||recording||micPending||!profile||!text.trim()),canConverse=!(busy||generating||recording||micPending);
 return <div className={'vs-app'+(showPanel?' with-panel':'')}>
 <SideNav view={view} onNavigate={navigate} health={health}/>
 <main className="focused-studio vs-main">
 {pages[view]&&<header className="vs-page-head"><div><h1>{pages[view][0]}</h1><p>{pages[view][1]}</p></div>{view==='edit'?<EditActions recording={recording} micPending={micPending} recordDisabled={busy||generating||micPending} onRecord={startRecording} onStopRecording={()=>rec.current?.stop()} importDisabled={busy||recording||generating} onImport={f=>work(()=>upload(f))} onChoose={e=>{drawerReturn.current=e.currentTarget;setDrawerOpen(true)}}/>:view==='generate'?<span className="vs-pills">{health?.demo&&<span className="vs-pill"><i/>PRIVATE DEMO</span>}<span className={'vs-pill vs-model-pill '+model.state} title="From /api/health (read-only)"><i/>{model.pill}</span></span>:<span className="vs-pill"><i/>{health?.demo?'PRIVATE DEMO':'ON DEVICE'}</span>}</header>}
 <div className="status" role="status"><span>{status}</span><span>{!health?'Checking inference…':health.inference?.status==='ready'?'Inference available':'Inference unavailable'}</span>{recording&&<button className="danger" onClick={()=>rec.current?.stop()}>Stop recording</button>}{generating&&!videoGenerating&&<button className={showPanel?'vs-stop-fallback':undefined} onClick={()=>{stopSequence.current=true;setStatus('Stopping after the current server job.')}}>Stop sequence after current job</button>}{micPending&&<button onClick={()=>{micAttempt.current++;setMicPending(false);setStatus('Microphone request cancelled.')}}>Cancel microphone request</button>}</div>
 {health?.demo&&<p className="demo-notice">Shared demo: invited guests can see files saved here. Personal studio files are separate.</p>}
 {error&&<div className="error" role="alert">{error}<button onClick={()=>setError('')}>Dismiss</button></div>}
 {view==='generate'&&<GenerateView profiles={profiles} profile={profile} onProfile={setProfile} language={language} onLanguage={setLanguage} text={text} onText={setText} health={health} capabilities={capabilities} canGenerate={canGenerate} onGenerate={()=>generate(false)} onDraft={()=>openWand('script',text)} helpersDisabled={helpersDisabled} conversation={sequenceOpen} onConversation={setSequenceOpen} sequence={sequence} onBlock={(bid,patch)=>setSequence(q=>q.map(v=>v.id===bid?{...v,...patch}:v))} onAddBlock={()=>setSequence(q=>[...q,{id:id(),profile,text:''}])} onRemoveBlock={bid=>setSequence(q=>q.filter(v=>v.id!==bid))} onRewrite={t=>openWand('dialogue',t.text,t.id)} canConverse={canConverse} onGenerateConversation={()=>generate(true)} generating={generating} canStop={generating&&!videoGenerating&&progress?.n>1} onStop={stopAfterCurrent} onLoadReference={()=>chosenProfile&&choose(chosenProfile.asset)}>
  <p className="vs-hint vs-gen-voices-link">Need another voice? <button className="vs-link" onClick={()=>{setVoicesTab('clone');navigate('voices')}}>Clone</button> or <button className="vs-link" onClick={()=>{setVoicesTab('design');navigate('voices')}}>design one</button> in Voices.</p>
 </GenerateView>}
 {view==='edit'&&<><RecordEdit asset={chosen} parentName={assets.find(a=>a.id===chosen?.parent)?.name} waveRef={waveEl} compare={compare} onCompare={setCompare} playing={wavePlaying} onPlay={()=>wave.current?.playPause()} onPlaySelection={()=>wave.current?.play(trim.start,trim.end)} onStop={()=>wave.current?.stop()} trim={trim} onTrim={updateTrim} ops={ops} onOps={setOps} onReset={()=>setOps(DEFAULT_OPS)} onApply={cleanup} applyDisabled={!chosen||busy||generating} comparison={comparison} onToggleComparison={()=>setComparison(c=>!c)} onSaveReference={()=>{setVoicesTab('clone');navigate('voices')}} onSendTranscribe={()=>navigate('transcribe')} folders={folders} onMove={f=>moveAsset(selected,f)} onDelete={()=>deleteAsset(selected)} actionsDisabled={busy||recording||generating} generating={generating} busy={busy}/>
 </>}
 {view==='voices'&&<VoicesView tab={voicesTab} onTab={setVoicesTab} profiles={profiles} assets={assets} onUse={id=>{setProfile(id);navigate('generate')}} chosen={chosen} selected={selected} onChoose={id=>{if(id)choose(id)}} recording={recording} micPending={micPending} onRecord={startRecording} onStopRecording={()=>rec.current?.stop()} onImport={f=>work(()=>upload(f))} importDisabled={busy||recording||generating} waveRef={waveEl} trim={trim} onTrim={updateTrim} onPlaySelection={()=>wave.current?.play(trim.start,trim.end)} onApplyTrim={applyReferenceTrim} applyTrimDisabled={busy||generating||recording} transcript={transcript} onTranscript={setTranscript} canTranscribe={capabilities?.enabled?!!(chosen&&!helpersDisabled&&capabilities?.transcription?.available):null} transcribeReason={capabilities?.enabled&&!capabilities?.transcription?.available?capabilities?.transcription?.reason:''} onTranscribe={()=>setAssistTarget({kind:'transcript',asset:selected,source:transcript,label:'Transcribe recording'})} profileName={profileName} onProfileName={setProfileName} onSave={()=>work(saveProfile)} saveDisabled={!chosen||!transcript.trim()||!profileName.trim()||busy||generating} description={description} onDescription={setDescription} sampleText={sampleText} onSampleText={setSampleText} language={language} onLanguage={setLanguage} assist={!!capabilities?.enabled} onShape={()=>openWand('voice',description)} helpersDisabled={helpersDisabled} canDesign={!(helpersDisabled||!capabilities?.enabled||!capabilities?.voice_design||!description.trim()||!sampleText.trim())} voiceDesignMissing={!!(capabilities?.enabled&&!capabilities.voice_design)} onDesign={designVoice}/>}
 {view==='transcribe'&&<Placeholder title="Transcribe: the full screen comes in a later step">{chosen&&<p className="vs-selected-rec">Selected recording: <b>{chosen.name}</b> · {chosen.duration.toFixed(1)} s</p>}<p className="muted">Transcription currently runs in Voices → Clone (step 2, “Transcribe recording”) for the selected recording.</p>{capabilities?.enabled&&!capabilities?.transcription?.available&&<p className="muted">{capabilities.transcription.reason}</p>}<div className="row"><button className="accent" onClick={()=>{setVoicesTab('clone');navigate('voices')}}>Open Voices → Clone</button></div></Placeholder>}
 <VideoWorkspace active={view==='video'} api={api} profiles={profiles} disabled={helpersDisabled} onGenerating={value=>{setGenerating(value);setVideoGenerating(value);setStatus(value?'Generating video narration locally…':'Video narration job ended. Review the Video workspace.')}} refresh={refresh}/>
 {view==='arrange'&&<> <section className="panel timeline"><div className="section"><div><h2>Arrange & export</h2><p className="muted">Drag clips to move them in time or between tracks. Use clip fields for precise trims.</p></div><div className="row"><button onClick={()=>setSession(s=>({...s,tracks:[...s.tracks,{id:id(),name:'Voice '+(s.tracks.length+1),volume:1,mute:false}]}))}>＋ Track</button><button disabled={!session.clips.length} onClick={playing?stopMix:playMix}>{playing?'Stop arrangement':'Play arrangement'}</button><button disabled={!session.clips.length||busy||generating} className="accent" onClick={()=>work(async()=>{setExported(await api('/export',session));setStatus('Mixed WAV exported')})}>Export mixed WAV</button></div></div>
 <div className="session-bar"><label>Session name<input aria-label="Session name" value={session.name} onChange={e=>setSession({...session,name:e.target.value})}/></label><button disabled={busy} onClick={()=>work(async()=>{const s=await api('/sessions',session);setSession(s);await refresh();setStatus('Session saved')})}>Save session</button><select aria-label="Open saved session" defaultValue="" onChange={e=>{const val=e.target.value;if(val)work(async()=>{stopMix();setSession(await api('/sessions/'+val));setExported(null);setTrack('');setStatus('Session reopened')})}}><option value="">Open saved session…</option>{sessions.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}</select><button onClick={()=>{stopMix();setSession(empty());setTrack('');setExported(null)}}>New session</button></div>
 <div className="timeline-scroll"><div style={{width:Math.max(900,duration*scale+180)}}><div className="ruler" style={{marginLeft:180}}>{Array.from({length:Math.ceil(duration/2)},(_,i)=><span key={i} style={{left:i*2*scale}}>{i*2}s</span>)}</div>{session.tracks.map(t=><div className="track" key={t.id}><div className="track-head"><input aria-label={'Track name '+t.id} value={t.name} onChange={e=>changeTrack(t.id,{name:e.target.value})}/><div><button className={t.mute?'muted-active':''} onClick={()=>changeTrack(t.id,{mute:!t.mute})}>{t.mute?'Unmute':'Mute'}</button><input aria-label={t.name+' volume'} title={'Volume '+t.volume.toFixed(2)} type="range" min="0" max="2" step=".05" value={t.volume} onChange={e=>changeTrack(t.id,{volume:+e.target.value})}/></div></div><div className="lane" data-track={t.id} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();if(drag.current){const r=e.currentTarget.getBoundingClientRect();changeClip(drag.current.id,{track:t.id,at:Math.max(0,(e.clientX-r.left-drag.current.offset)/scale)});drag.current=null}}}>{session.clips.filter(c=>c.track===t.id).map(c=><div className={"clip "+(highlight===c.id?"new-clip":"")} onPointerDown={e=>beginClipDrag(e,c)} key={c.id} style={{left:c.at*scale,width:Math.max(32,(c.out-c.in)*scale)}} onDragStart={e=>{drag.current={id:c.id,offset:e.nativeEvent.offsetX};e.dataTransfer.setData('text/plain',c.id)}}><span>≋ {assets.find(a=>a.id===c.asset)?.name||'Audio'}</span><small>{(c.out-c.in).toFixed(2)}s</small></div>)}</div></div>)}</div></div>
 {session.clips.length>0&&<div className="clip-fields">{session.clips.map((c,i)=><div className="clip-row" key={c.id}><span>Clip {i+1}: {assets.find(a=>a.id===c.asset)?.name}</span><label>Track<select value={c.track} onChange={e=>changeClip(c.id,{track:e.target.value})}>{session.tracks.map(t=><option value={t.id} key={t.id}>{t.name}</option>)}</select></label>{[['at','Position'],['in','Trim in'],['out','Trim out']].map(([k,v])=><label key={k}>{v}<input type="number" min="0" step=".01" value={c[k]} onChange={e=>changeClip(c.id,{[k]:+e.target.value})}/></label>)}<button onClick={()=>{setSession(s=>({...s,clips:s.clips.filter(x=>x.id!==c.id)}));setExported(null)}}>Remove</button></div>)}</div>}
 {exported&&<div className="export"><audio controls src={exported.url}/><a href={exported.url} download>Download mixed WAV ↗</a><span>{exported.duration.toFixed(2)}s · 48 kHz stereo{exported.gain<1?' · Gain reduced to prevent clipping':''}</span></div>}
</section></>}
 <dialog ref={drawer} className="recordings-drawer" onCancel={e=>{e.preventDefault();setDrawerOpen(false)}} onClick={e=>{if(e.target===e.currentTarget)setDrawerOpen(false)}}><div className="drawer-content"><div className="section"><h2>Recordings</h2><button onClick={()=>setDrawerOpen(false)}>Close recordings</button></div><label>Search recordings<input aria-label="Search recordings" value={search} onChange={e=>setSearch(e.target.value)}/></label>{assets.filter(a=>a.name.toLowerCase().includes(search.toLowerCase())).map(a=><button className="asset" key={a.id} onClick={()=>{choose(a.id);setDrawerOpen(false)}}><span>{a.name}<small>{a.duration.toFixed(2)} s · {a.parent?'Edited':a.synthetic?'Synthetic voice':a.profile?'Generated':'Original input'}</small></span></button>)}{!assets.filter(a=>a.name.toLowerCase().includes(search.toLowerCase())).length&&<p>No recordings found.</p>}</div></dialog>
 {assistTarget&&<AssistDialog key={assistTarget.key||assistTarget.kind} target={assistTarget} api={api} onClose={()=>setAssistTarget(null)} onApply={applySuggestion} onBusy={setBusy}/>}
 <footer>Original recordings are retained. Save arrangements before reloading; unsaved form values are not part of a saved session.</footer>
 </main>
 {showPanel&&<RecordingsPanel assets={visibleAssets} total={assets.length} selected={selected} onSelect={choose} search={search} onSearch={setSearch} folders={folders} folderFilter={folderFilter} onFolderFilter={setFolderFilter} onImport={f=>work(()=>upload(f))} onCreateFolder={createFolder} disabled={busy||recording||generating}>{generating&&!videoGenerating&&progress&&<JobCard progress={progress} job={job} status={status} firstRun={health?.inference?.loaded===false} onStop={stopAfterCurrent}/>}</RecordingsPanel>}
 <TransportBar asset={chosen} playerRef={player} onEdit={()=>openTools(selected)} onAdd={addClip} tracks={session.tracks} track={track||session.tracks[0]?.id||''} onTrack={setTrack} onError={setError}/>
 </div>
}
createRoot(document.getElementById('root')).render(<App/>);

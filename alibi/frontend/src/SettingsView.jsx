// Settings workspace: what is true about this machine and this workspace.
// Per-clip controls stay in the editors; nothing here edits a recording.
import React,{useEffect,useState} from 'react';
import {Cpu,HardDrive,RotateCcw,FolderOpen,ScrollText,Info,RefreshCw,Zap,Trash2,Copy,Check} from 'lucide';
import {Icon} from './Shell.jsx';
import './settings.css';

const SECTIONS=[
 ['models','Models & hardware',Cpu],
 ['services','Services & diagnostics',ScrollText],
 ['workspace','Workspace & storage',HardDrive],
 ['preferences','Preferences',Zap],
 ['about','About',Info],
];

const size=bytes=>{
 if(!bytes)return '0 MB';
 const mb=bytes/1024**2;
 return mb>=1024?(mb/1024).toFixed(mb>=10240?0:1)+' GB':Math.round(mb)+' MB';
};

const secondsAgo=value=>{
 if(!value)return 'never';
 const s=Date.now()/1000-value;
 if(s<60)return 'just now';
 if(s<3600)return Math.floor(s/60)+' min ago';
 return Math.floor(s/3600)+' h ago';
};

function Row({label,children}){
 return <div className="settings-row"><span>{label}</span><div>{children}</div></div>;
}

export function SettingsView({api,health,onRefreshHealth,onSettings}){
 const [section,setSection]=useState('models');
 const [settings,setSettings]=useState(null);
 const [models,setModels]=useState(null);
 const [storage,setStorage]=useState(null);
 const [logs,setLogs]=useState(null);
 const [logService,setLogService]=useState('inference');
 const [busy,setBusy]=useState('');
 const [error,setError]=useState('');
 const [notice,setNotice]=useState('');
 const [days,setDays]=useState(30);
 const [copied,setCopied]=useState(false);

 const inference=health?.inference;
 const workerReady=inference?.status==='ready';
 const build=health?.build;

 async function guard(label,fn){
  setBusy(label);setError('');setNotice('');
  try{await fn()}
  catch(e){setError(e.message)}
  finally{setBusy('')}
 }

 async function loadAll(){
  const [s,m,st]=await Promise.all([api('/settings'),api('/models'),api('/settings/storage')]);
  setSettings(s.settings);setModels(m);setStorage(st);onSettings?.(s.settings);
 }

 useEffect(()=>{loadAll().catch(e=>setError(e.message))},[]);

 async function save(patch){
  await guard('save',async()=>{
   const r=await api('/settings',patch,'PATCH');
   setSettings(r.settings);onSettings?.(r.settings);
   setNotice('preload_model' in patch?'Saved. The preload applies the next time Alibi starts.':'Saved.');
  });
 }

 async function modelAction(kind,action){
  await guard(action+':'+kind,async()=>{
   if(action==='load')await api('/models/load',{kind});
   else await api('/models/unload',{});
   setModels(await api('/models'));
   await onRefreshHealth?.();
   setNotice(action==='load'?kind+' model loaded.':'Model unloaded; memory freed.');
  });
 }

 async function restart(){
  await guard('restart',async()=>{
   await api('/settings/restart-inference',{});
   setNotice('Restarting the inference worker…');
   for(let i=0;i<40;i++){
    await new Promise(r=>setTimeout(r,1500));
    const m=await api('/models');
    if(m.available){setModels(m);await onRefreshHealth?.();setNotice('Inference worker restarted.');return}
   }
   throw Error('The inference worker did not come back. Close Alibi and start it again.');
  });
 }

 async function reveal(name){
  await guard('reveal:'+name,async()=>{await api('/settings/reveal',{name})});
 }

 async function cleanup(){
  if(!window.confirm(`Delete exports older than ${days} days? Recordings and voices are not touched.`))return;
  await guard('cleanup',async()=>{
   const r=await api('/settings/cleanup',{days});
   setStorage(await api('/settings/storage'));
   setNotice(r.removed?`Removed ${r.removed} export${r.removed===1?'':'s'}, freeing ${size(r.freed)}.`:'No exports were older than that.');
  });
 }

 async function readLogs(service){
  await guard('logs',async()=>{
   setLogService(service);
   setLogs(await api('/settings/logs?service='+service+'&lines=200'));
  });
 }

 function diagnostics(){
  return [
   'Alibi '+(build?.version||'unknown')+' ('+(build?.commit||'unknown').slice(0,12)+')',
   'source: '+(build?.source||'unknown')+' · built '+(build?.built_at||'unknown'),
   'platform: '+navigator.platform+' · '+navigator.userAgent,
   'backend: '+(health?.status||'unknown'),
   'inference: '+(inference?.status||'unknown')+' · model '+(inference?.model||'none')+' · device '+(inference?.device||'unknown'),
   'data: '+(storage?.data||'unknown'),
   'models: '+(storage?.models_path||'unknown'),
   'settings: '+JSON.stringify(settings||{}),
  ].join('\n');
 }

 async function copyDiagnostics(){
  const text=diagnostics();
  try{await navigator.clipboard.writeText(text)}
  catch{
   const area=document.createElement('textarea');area.value=text;document.body.appendChild(area);
   area.select();document.execCommand('copy');area.remove();
  }
  setCopied(true);setTimeout(()=>setCopied(false),2000);
 }

 const modelList=models?.models||[];
 const loadedKind=inference?.model||models?.loaded||null;
 const vram=inference?.vram;
 const vramUsed=vram&&vram.total>0?Math.max(0,vram.total-vram.free):0;
 const vramPercent=vram&&vram.total>0?Math.min(100,Math.round(100*vramUsed/vram.total)):0;

 return <section className="settings">
  <nav className="settings-nav" aria-label="Settings sections">
   {SECTIONS.map(([key,label,icon])=><button key={key} className={section===key?'active':''} aria-current={section===key?'page':undefined} onClick={()=>setSection(key)}><Icon icon={icon} size={15}/><span>{label}</span></button>)}
  </nav>
  <div className="settings-body">
   <div className="settings-alerts" aria-live="polite">
    {error&&<p className="settings-error" role="alert">{error}<button onClick={()=>setError('')}>Dismiss</button></p>}
    {notice&&!error&&<p className="settings-notice"><Icon icon={Check} size={14}/>{notice}</p>}
   </div>

   {section==='models'&&<div className="settings-panel">
    <header><h2>Models & hardware</h2><p className="muted">Two local models share one worker. Loading one unloads the other; nothing leaves this PC.</p></header>

    <div className="settings-card">
     <div className="settings-card-head"><h3>This machine</h3><button className="settings-link" onClick={()=>guard('refresh',loadAll)} disabled={!!busy}><Icon icon={RefreshCw} size={13}/>Refresh</button></div>
     <Row label="Inference worker"><span className="settings-status"><span className={'settings-dot '+(workerReady?'ok':'bad')}/>{workerReady?'Ready':'Offline'}</span></Row>
     <Row label="Device">{inference?.gpu||inference?.device||'unknown'}</Row>
     <Row label="Precision">{inference?.dtype||'unknown'}</Row>
     <Row label="Loaded model">{loadedKind||'Nothing loaded'}</Row>
     <Row label="Last used">{secondsAgo(inference?.last_used)}</Row>
     {vram&&vram.total>0&&<div className="settings-vram">
      <div className="settings-vram-label"><span>GPU memory</span><span>{size(vramUsed)} used of {size(vram.total)}</span></div>
      <div className="settings-bar"><i style={{width:vramPercent+'%'}}/></div>
     </div>}
    </div>

    <div className="settings-card">
     <div className="settings-card-head"><h3>Installed models</h3><span className="muted">{models?.available?'worker online':'worker offline'}</span></div>
     {!models?.available&&<p className="settings-hint">The inference worker is offline, so models cannot be listed or loaded. Start Alibi from its launcher, or restart the worker under Services.{models?.error?' '+models.error:''}</p>}
     {modelList.map(m=><div className="settings-model" key={m.kind}>
      <div className="settings-model-text">
       <b>{m.kind}</b>
       <small>{m.present?size(m.bytes):'not installed'}{m.loaded?' · loaded':''}</small>
      </div>
      {m.present
       ?(m.loaded
         ?<button disabled={!!busy} onClick={()=>modelAction(m.kind,'unload')}>{busy==='unload:'+m.kind?'Unloading…':'Unload'}</button>
         :<button className="accent" disabled={!!busy||!workerReady} onClick={()=>modelAction(m.kind,'load')}>{busy==='load:'+m.kind?'Loading…':'Load'}</button>)
       :<span className="muted">Rerun the installer to add it</span>}
     </div>)}
    </div>

    <div className="settings-card">
     <div className="settings-card-head"><h3>Loading behaviour</h3></div>
     <Row label="Load at startup">
      <select value={settings?.preload_model??''} disabled={!settings||!!busy} onChange={e=>save({preload_model:e.target.value})}>
       <option value="">Don't preload</option>
       <option value="Base">Base (cloning)</option>
       <option value="VoiceDesign">VoiceDesign</option>
      </select>
     </Row>
     <Row label="Unload after idle">
      <select value={String(settings?.idle_unload_minutes??0)} disabled={!settings||!!busy} onChange={e=>save({idle_unload_minutes:Number(e.target.value)})}>
       <option value="0">Keep loaded</option>
       <option value="5">5 minutes</option>
       <option value="15">15 minutes</option>
       <option value="30">30 minutes</option>
       <option value="60">1 hour</option>
      </select>
     </Row>
     <p className="settings-hint">Keeping a model loaded avoids a one-minute first run. Unloading frees GPU memory for other apps.</p>
    </div>
   </div>}

   {section==='services'&&<div className="settings-panel">
    <header><h2>Services & diagnostics</h2><p className="muted">Alibi runs a studio API and a model worker on this machine. Restarting the worker is the fix for a stuck inference job.</p></header>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Status</h3></div>
     <Row label="Studio API"><span className="settings-status"><span className={'settings-dot '+(health?'ok':'bad')}/>{health?'Ready':'Unreachable'}</span></Row>
     <Row label="Inference worker"><span className="settings-status"><span className={'settings-dot '+(workerReady?'ok':'bad')}/>{workerReady?'Ready':'Offline'}</span></Row>
     <Row label="Version">{build?.version||'unknown'}{build?.commit&&build.commit!=='unknown'?' · '+build.commit.slice(0,7):''}</Row>
     <div className="settings-actions">
      <button disabled={!!busy} onClick={restart}>{busy==='restart'?'Restarting…':'Restart inference worker'}</button>
      <button disabled={!!busy} onClick={()=>reveal('logs')}><Icon icon={FolderOpen} size={13}/>Open log folder</button>
     </div>
    </div>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Logs</h3>
      <div className="settings-actions">
       <button className={logService==='inference'?'active':''} onClick={()=>readLogs('inference')}>Inference</button>
       <button className={logService==='backend'?'active':''} onClick={()=>readLogs('backend')}>Studio API</button>
      </div>
     </div>
     {logs?<pre className="settings-log" aria-label={'Last lines of the '+logs.service+' log'}>{logs.text||'The log is empty.'}</pre>:<p className="settings-hint">Choose a service to read its last 200 lines.</p>}
     {logs&&<p className="settings-hint settings-path">{logs.path}</p>}
    </div>
   </div>}

   {section==='workspace'&&<div className="settings-panel">
    <header><h2>Workspace & storage</h2><p className="muted">Recordings, voices, and exports live in your data folder. Models and cache live beside it.</p></header>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Folders</h3><button className="settings-link" onClick={()=>guard('storage',async()=>setStorage(await api('/settings/storage')))} disabled={!!busy}><Icon icon={RefreshCw} size={13}/>Recalculate</button></div>
     {[
      {label:'Data',path:storage?.data,bytes:storage?.data_total,open:'data'},
      {label:'Recordings',bytes:storage?.recordings},
      {label:'Exports',path:storage?.exports_path,bytes:storage?.exports,open:'exports'},
      {label:'Models',path:storage?.models_path,bytes:storage?.models,open:'models'},
      {label:'Cache',path:storage?.cache_path,bytes:storage?.cache,open:'cache'},
     ].map(row=>
      <div className="settings-row settings-folder" key={row.label}>
       <span>{row.label}</span>
       <div>
        {row.path&&<code>{row.path}</code>}
        {row.bytes!==undefined&&<em>{size(row.bytes)}</em>}
        {row.open&&<button className="settings-icon" title={'Open '+row.label} aria-label={'Open '+row.label+' folder'} onClick={()=>reveal(row.open)}><Icon icon={FolderOpen} size={14}/></button>}
       </div>
      </div>)}
     <div className="settings-totals">
      <span><b>{size(storage?.recordings)}</b> recordings</span>
      <span><b>{size(storage?.models)}</b> models</span>
      <span><b>{size(storage?.cache)}</b> cache</span>
      <span><b>{storage?.exports_count??0}</b> exports</span>
     </div>
    </div>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Clean up exports</h3></div>
     <p className="settings-hint">Exports are mixed WAVs from Arrange. Deleting old ones never touches recordings or saved voices.</p>
     <div className="settings-actions">
      <label className="settings-inline">Older than
       <input type="number" min="1" max="3650" value={days} onChange={e=>setDays(Math.max(1,Math.min(3650,Number(e.target.value)||1)))}/> days
      </label>
      <button className="settings-danger" disabled={!!busy} onClick={cleanup}><Icon icon={Trash2} size={13}/>{busy==='cleanup'?'Deleting…':'Delete old exports'}</button>
     </div>
    </div>
   </div>}

   {section==='preferences'&&<div className="settings-panel">
    <header><h2>Preferences</h2><p className="muted">Defaults for new work. Existing recordings keep the settings they were made with.</p></header>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Defaults</h3></div>
     <Row label="Generation language">
      <select value={settings?.default_language||'English'} disabled={!settings||!!busy} onChange={e=>save({default_language:e.target.value})}>
       {(settings?.languages||['English']).map(language=><option key={language} value={language}>{language}</option>)}
      </select>
     </Row>
     <p className="settings-hint">Used by Generate, dialogue blocks, and voice design.</p>
    </div>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Appearance</h3></div>
     <label className="settings-toggle"><input type="checkbox" checked={!!settings?.reduce_motion} disabled={!settings||!!busy} onChange={e=>save({reduce_motion:e.target.checked})}/><span><b>Reduce motion</b><small>Skip decorative animation.</small></span></label>
     <label className="settings-toggle"><input type="checkbox" checked={!!settings?.compact_sidebar} disabled={!settings||!!busy} onChange={e=>save({compact_sidebar:e.target.checked})}/><span><b>Compact sidebar</b><small>Smaller navigation for short windows.</small></span></label>
    </div>
   </div>}

   {section==='about'&&<div className="settings-panel">
    <header><h2>About</h2><p className="muted">Everything runs locally: no account, no cloud, no telemetry.</p></header>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Build</h3></div>
     <Row label="Version">{build?.version||'unknown'}</Row>
     <Row label="Commit"><code>{build?.commit||'unknown'}</code></Row>
     <Row label="Built">{build?.built_at||'unknown'}</Row>
     <Row label="Running from">{build?.source==='build'?'installed build':build?.source==='source'?'Git checkout':'unknown'}</Row>
     <Row label="Data folder"><code className="settings-path">{storage?.data||'…'}</code></Row>
     <div className="settings-actions">
      <button onClick={copyDiagnostics}><Icon icon={copied?Check:Copy} size={13}/>{copied?'Copied':'Copy diagnostics'}</button>
      <a className="settings-button" href="https://github.com/SaltProphet/Alibi/releases" target="_blank" rel="noreferrer">Check for updates</a>
     </div>
     <p className="settings-hint">Updates are installed from GitHub Releases, not from inside the app.</p>
    </div>
    <div className="settings-card">
     <div className="settings-card-head"><h3>Reset</h3></div>
     <p className="settings-hint">Restores language, loading behaviour, and appearance. Recordings, voices, and exports are not touched.</p>
     <button className="settings-danger" disabled={!!busy} onClick={()=>guard('reset',async()=>{const r=await api('/settings/reset',{});setSettings(r.settings);onSettings?.(r.settings);setNotice('Settings reset to defaults.')})}><Icon icon={RotateCcw} size={13}/>Reset settings</button>
    </div>
   </div>}
  </div>
 </section>;
}

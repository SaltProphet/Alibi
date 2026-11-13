import React,{useState,useRef} from 'react';

export default function AudioWelcome({assets,onOpen}) {
  const full=assets.find(a=>a.onboarding_key==='guide-full');
  const [expanded,setExpanded]=useState(true);
  const player=useRef();
  if(!full)return null;
  return <section className="panel audio-welcome" aria-label="Spoken welcome">
    <div className="welcome-heading">
      <div className="host-icon" aria-hidden="true">♫</div>
      <div className="welcome-copy"><span className="eyebrow">MEET YOUR STUDIO HOST</span><h2>A voice to show you around.</h2><p>A quick spoken tour. Press play, settle in, and explore.</p></div>
      <button className="welcome-toggle" onClick={()=>{if(expanded)player.current?.pause();setExpanded(!expanded)}} aria-expanded={expanded}>{expanded?'Hide welcome':'Listen to the walkthrough'}</button>
    </div>
    {expanded&&<div className="welcome-audio"><audio ref={player} aria-label="Alibi spoken walkthrough" controls preload="metadata" src={'/api/assets/'+full.id+'/audio'}/><div className="welcome-foot"><span>Synthetic adult female narrator · {Math.round(full.duration)} seconds</span><button onClick={()=>onOpen(full.id)}>Open audio in editor</button><a href={'/api/assets/'+full.id+'/audio'} download>Download walkthrough ↗</a></div></div>}
  </section>;
}

"""Generate real onboarding and install only explicitly packaged samples in both workspaces."""
from pathlib import Path
import json,uuid,time,shutil,sys
import httpx,numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'content/onboarding'
CHAPTERS=json.loads((PACK/'chapters.json').read_text(encoding='utf-8'))
SAMPLE_TRANSCRIPT='Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.'
SAMPLE_REFERENCE=ROOT/'data/tests/official-reference.wav'
REFERENCE=ROOT/'data/onboarding-narrator/reference.wav'
if (ROOT/'content/narrator/reference.wav').exists():
    REFERENCE=ROOT/'content/narrator/reference.wav'
TRANSCRIPT=json.loads((REFERENCE.parent/'reference.json').read_text(encoding='utf-8'))['transcript']
if not SAMPLE_REFERENCE.exists():
    SAMPLE_REFERENCE.parent.mkdir(parents=True,exist_ok=True)
    response=httpx.get('https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/clone.wav',timeout=60,follow_redirects=True)
    response.raise_for_status();SAMPLE_REFERENCE.write_bytes(response.content)

def install_asset(data,source,key,name,**extra):
    folder=data/'audio';folder.mkdir(parents=True,exist_ok=True)
    matches=[(p,json.loads(p.read_text(encoding='utf-8'))) for p in folder.glob('*.json')]
    existing=next((obj for p,obj in matches if obj.get('onboarding_key')==key),None)
    if existing:
        if key=='narrator-reference' or key.startswith('guide-'):
            dest=folder/existing['file'];shutil.copyfile(source,dest);info=sf.info(dest)
            existing.update(name=name,duration=info.duration,sample_rate=info.samplerate,channels=info.channels,**extra)
            (folder/(existing['id']+'.json')).write_text(json.dumps(existing,indent=2),encoding='utf-8')
        return existing
    id=uuid.uuid4().hex;dest=folder/(id+'.wav');shutil.copyfile(source,dest);info=sf.info(dest)
    obj=dict(id=id,file=dest.name,name=name,duration=info.duration,sample_rate=info.samplerate,channels=info.channels,created=time.time(),onboarding_key=key,**extra)
    (folder/(id+'.json')).write_text(json.dumps(obj,indent=2),encoding='utf-8');return obj

def install(data):
    ref=install_asset(data,SAMPLE_REFERENCE,'sample-reference','Demo voice reference · Qwen sample',transcript=SAMPLE_TRANSCRIPT,provenance='Official Qwen3-TTS README reference; not the user voice')
    profiles=data/'profiles';profiles.mkdir(parents=True,exist_ok=True)
    profile=next((json.loads(p.read_text(encoding='utf-8')) for p in profiles.glob('*.json') if json.loads(p.read_text(encoding='utf-8')).get('onboarding_key')=='sample-voice'),None)
    if profile is None:
        id=uuid.uuid4().hex;(data/'references').mkdir(parents=True,exist_ok=True);shutil.copyfile(SAMPLE_REFERENCE,data/'references'/(id+'.wav'))
        profile=dict(id=id,name='Demo voice · Qwen sample (not your voice)',asset=ref['id'],reference=id+'.wav',transcript=SAMPLE_TRANSCRIPT,onboarding_key='sample-voice')
        (profiles/(id+'.json')).write_text(json.dumps(profile,indent=2),encoding='utf-8')
    originals=[('demo-hello',ROOT/'content/demo/hello.wav','Demo 01 · Hello','Hello. This is a local voice cloning test for Alibi.'),('demo-welcome',ROOT/'content/demo/welcome.wav','Demo 02 · Welcome','Welcome to Alibi. This speech was generated entirely on this computer.'),('demo-restart',ROOT/'content/demo/saved-voice.wav','Demo 03 · Saved voice','The studio has restarted. Your saved voice is ready.')]
    for key,source,name,text in originals:install_asset(data,source,key,name,profile=profile['id'],text=text,provenance='Restored real Qwen3-TTS generation from installation tests')
    narrator_ref=install_asset(data,REFERENCE,'narrator-reference','Studio host · Synthetic adult female voice reference',transcript=TRANSCRIPT,synthetic=True)
    narrator=next((json.loads(p.read_text(encoding='utf-8')) for p in profiles.glob('*.json') if json.loads(p.read_text(encoding='utf-8')).get('onboarding_key')=='narrator-voice'),None)
    if narrator is None:
        id=uuid.uuid4().hex;shutil.copyfile(REFERENCE,data/'references'/(id+'.wav'))
        narrator=dict(id=id,name='Studio host · Friendly synthetic female narrator',asset=narrator_ref['id'],reference=id+'.wav',transcript=TRANSCRIPT,onboarding_key='narrator-voice',synthetic=True)
        (profiles/(id+'.json')).write_text(json.dumps(narrator,indent=2),encoding='utf-8')
    else:
        shutil.copyfile(REFERENCE,data/'references'/narrator['reference'])
        narrator.update(name='Studio host · Friendly synthetic female narrator',transcript=TRANSCRIPT)
        (profiles/(narrator['id']+'.json')).write_text(json.dumps(narrator,indent=2),encoding='utf-8')
    return narrator

if '--samples-only' in sys.argv:
    for data in [ROOT/'data',ROOT/'data/demo']:
        install(data)
    print('Original demo clips restored in both workspaces.',flush=True)
    raise SystemExit(0)

with httpx.Client(timeout=1800,trust_env=False) as c:
    for chapter in CHAPTERS:
        path=PACK/(chapter['key']+'.wav')
        if path.exists():print('Already generated',chapter['key'],flush=True);continue
        print('Generating',chapter['title'],flush=True)
        # The inference worker restricts writes to data/, so stage output there before packaging.
        stage=ROOT/'data/tests'/('onboarding-'+chapter['key']+'.wav')
        r=c.post('http://127.0.0.1:8766/generate',json={'reference':str(REFERENCE),'transcript':TRANSCRIPT,'text':chapter['text'],'language':'English','output':str(stage)})
        r.raise_for_status();x,sr=sf.read(stage)
        assert sr==24000 and len(x)>sr and np.isfinite(x).all() and np.max(np.abs(x))>.001
        shutil.copyfile(stage,path)
        chapter['generation']=r.json();(PACK/(chapter['key']+'.json')).write_text(json.dumps(chapter,indent=2),encoding='utf-8')
        print('Generated',chapter['key'],len(x)/sr,'seconds',flush=True)
    chunks=[];rate=24000
    for chapter in CHAPTERS:
        x,sr=sf.read(PACK/(chapter['key']+'.wav'));assert sr==rate;chunks.extend([x,np.zeros(round(rate*.5))])
    sf.write(PACK/'full-guide.wav',np.concatenate(chunks),rate,subtype='PCM_16')
    for data in [ROOT/'data',ROOT/'data/demo']:
        profile=install(data);assets=[];at=0
        for chapter in CHAPTERS:
            a=install_asset(data,PACK/(chapter['key']+'.wav'),'guide-'+chapter['key'],chapter['title'],profile=profile['id'],text=chapter['text'],generation=json.loads((PACK/(chapter['key']+'.json')).read_text())['generation'])
            assets.append(dict(id=uuid.uuid4().hex,asset=a['id'],track='narration',at=at,**{'in':0,'out':a['duration']}));at+=a['duration']+.5
        install_asset(data,PACK/'full-guide.wav','guide-full','Start here · Alibi audio walkthrough',profile=profile['id'],text='\n\n'.join(ch['text'] for ch in CHAPTERS))
        sessions=data/'sessions';sessions.mkdir(parents=True,exist_ok=True)
        existing=next((json.loads(p.read_text(encoding='utf-8')) for p in sessions.glob('*.json') if json.loads(p.read_text(encoding='utf-8')).get('onboarding_key')=='guide-session'),None)
        if not existing:
            obj={'id':uuid.uuid4().hex,'name':'Walkthrough · Studio host','tracks':[{'id':'narration','name':'Spoken guide','volume':1,'mute':False}],'clips':assets,'onboarding_key':'guide-session'}
            (sessions/(obj['id']+'.json')).write_text(json.dumps(obj,indent=2),encoding='utf-8')
        print('Installed guide and demo clips in',data,flush=True)
print('ONBOARDING COMPLETE',flush=True)

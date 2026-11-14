from pathlib import Path
import sys,json,httpx,soundfile as sf,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.audio import process
TEST=ROOT/'data/tests/immersive';TEST.mkdir(parents=True,exist_ok=True)
sr=48000;t=np.arange(sr*2)/sr;p=TEST/'sine-input.wav';sf.write(p,.25*np.sin(2*np.pi*440*t),sr,subtype='FLOAT')
y,rate=process(p,{'start':0,'end':2,'pitch':12,'timbre':.4,'vibrato':0});middle=y[sr//2:sr*3//2,0];freq=np.fft.rfftfreq(len(middle),1/sr)[np.argmax(abs(np.fft.rfft(middle)))];assert abs(freq-880)<8,(freq,len(y))
z,_=process(p,{'start':0,'end':2,'vibrato':.6});assert len(z)==len(t) and np.isfinite(z).all() and not np.allclose(z[:,0],.25*np.sin(2*np.pi*440*t));sf.write(TEST/'fx-verified.wav',y,rate)
c=httpx.Client(base_url='http://127.0.0.1:8875',timeout=90,trust_env=False);health=c.get('/api/health').json();assert Path(health['data']).is_relative_to(ROOT/'data/tests')
for key in ['nova','atlas','cyra','echo']:
 v=json.loads((ROOT/'content/archetypes'/(key+'.json')).read_text(encoding='utf-8'))
 existing=next((p for p in c.get('/api/profiles').json() if p.get('archetype')==key),None)
 if existing:continue
 with (ROOT/'content/archetypes'/(key+'.wav')).open('rb') as f:r=c.post('/api/import',files={'file':(v['name']+'.wav',f)})
 r.raise_for_status();a=r.json();r=c.post('/api/profiles',json={'name':v['name'],'asset':a['id'],'transcript':v['text']});r.raise_for_status();p=r.json();p.update(archetype=key,synthetic=True)
 (TEST/'profiles'/(p['id']+'.json')).write_text(json.dumps(p,indent=2),encoding='utf-8')
print(json.dumps({'pitch_12_semitones_dominant_hz':float(freq),'vibrato_modifies_audio':True,'isolated_profiles':len(c.get('/api/profiles').json()),'status':'passed'}))

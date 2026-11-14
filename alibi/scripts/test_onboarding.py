"""Verify packaged walkthrough, restored samples, and matching voice profile in both apps."""
from pathlib import Path
import json,hashlib
import httpx,numpy as np,soundfile as sf
ROOT=Path(__file__).resolve().parents[1];results=[]
for port in [8765,8767]:
 with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=30,trust_env=False) as c:
  assets=c.get('/api/assets').json();profiles=c.get('/api/profiles').json();sessions=c.get('/api/sessions').json()
  keys={a.get('onboarding_key'):a for a in assets if a.get('onboarding_key')}
  required=['sample-reference','narrator-reference','demo-hello','demo-welcome','demo-restart','guide-welcome','guide-record','guide-clone','guide-finish','guide-full']
  assert all(key in keys for key in required),list(keys)
  p=next(p for p in profiles if p.get('onboarding_key')=='narrator-voice');assert p['synthetic'] and p['asset']==keys['narrator-reference']['id']
  for key in required:
   a=keys[key];r=c.get('/api/assets/'+a['id']+'/audio');assert r.is_success
   import io
   x,sr=sf.read(io.BytesIO(r.content));assert sr==24000 and len(x)>sr and np.isfinite(x).all() and np.max(np.abs(x))>.001
  total=sum(keys['guide-'+k]['duration']+.5 for k in ['welcome','record','clone','finish']);assert abs(keys['guide-full']['duration']-total)<.001
  for key,source in [('demo-hello',ROOT/'content/demo/hello.wav'),('demo-welcome',ROOT/'content/demo/welcome.wav'),('demo-restart',ROOT/'content/demo/saved-voice.wav')]:
   assert hashlib.sha256(c.get('/api/assets/'+keys[key]['id']+'/audio').content).digest()==hashlib.sha256(source.read_bytes()).digest()
  session=next(s for s in sessions if s.get('onboarding_key')=='guide-session');assert len(session['clips'])==4
  results.append({'port':port,'walkthrough_seconds':total,'profile':p['id'],'full_asset':keys['guide-full']['id'],'original_demo_bytes_preserved':True,'chapters':4,'status':'passed'})
(ROOT/'data/tests/onboarding-verification.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))

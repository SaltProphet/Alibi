"""Functional API checks; run only with Launch-Voice-Studio.ps1 -TestWorkspace."""
from pathlib import Path
import httpx,json,subprocess,hashlib,time,sys
import soundfile as sf
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
c=httpx.Client(base_url='http://127.0.0.1:8765',timeout=180,trust_env=False)
checks={}
def ok(r):
    assert r.is_success,r.text
    return r.json()
health=ok(c.get('/api/health'));assert Path(health['data']).is_relative_to(ROOT/'data/tests')
def upload(p):
    with p.open('rb') as f:return ok(c.post('/api/import',files={'file':(p.name,f)}))
a=upload(ROOT/'data/tests/official-reference.wav');checks['wav_import']=a
original=c.get('/api/assets/'+a['id']+'/original');assert original.content==(ROOT/'data/tests/official-reference.wav').read_bytes();checks['original_bytes_preserved']=True
for ext in ['mp3','flac']:
    p=ROOT/'data/tests'/('reference.'+ext)
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'data/tests/official-reference.wav'),str(p)],check=True)
    imported=upload(p);assert imported['duration']>7;checks[ext+'_import']=True
edited=ok(c.post('/api/assets/'+a['id']+'/process',json={'start':.5,'end':6.5,'denoise':True,'normalize':True,'highpass':True,'fade_in':.1,'fade_out':.2,'strength':.5}))
assert abs(edited['duration']-6)<.001
p=ROOT/'data/tests/studio/audio'/edited['file'];x,sr=sf.read(p);assert np.isfinite(x).all() and np.max(np.abs(x))<=.892
checks['cleanup_trim_fades_normalize']=edited
assert c.get('/api/assets/'+a['id']+'/original').content==original.content
profile=ok(c.post('/api/profiles',json={'name':'Official reference TEST','asset':a['id'],'transcript':'Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.'}));checks['voice_reference_profile']=profile
session={'name':'Functional verification TEST','tracks':[{'id':'t1','name':'Reference','volume':.65,'mute':False},{'id':'t2','name':'Edited','volume':.8,'mute':False},{'id':'t3','name':'Muted','volume':1,'mute':True}], 'clips':[{'id':'c1','asset':a['id'],'track':'t1','at':0,'in':.2,'out':2.2},{'id':'c2','asset':edited['id'],'track':'t2','at':1,'in':1,'out':3},{'id':'c3','asset':a['id'],'track':'t3','at':.5,'in':0,'out':1}]}
saved=ok(c.post('/api/sessions',json=session));assert ok(c.get('/api/sessions/'+saved['id']))==saved;checks['session_save_reopen']=saved['id']
export=ok(c.post('/api/export',json=saved));wav=c.get(export['url']);p=ROOT/'data/tests/verified-mix.wav';p.write_bytes(wav.content);x,sr=sf.read(p);assert sr==48000 and x.shape==(144000,2) and np.max(np.abs(x))>0;checks['mixed_wav']=export
assert c.post('/api/profiles',json={'name':'bad','asset':a['id'],'transcript':''}).status_code==422
assert c.post('/api/assets/'+a['id']+'/process',json={'start':4,'end':2}).status_code==400
assert c.post('/api/export',json={**session,'clips':[]}).status_code==400
assert c.post('/api/generate',json={'profile':'bad','text':'test'}).status_code==400
assert c.get('/api/health',headers={'Origin':'https://example.com'}).status_code==403
assert c.get('/api/health',headers={'Host':'example.com'}).status_code==400
checks['invalid_inputs_and_origin_rejected']=True
(ROOT/'data/tests/api-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))

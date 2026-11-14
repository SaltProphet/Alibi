from pathlib import Path
import json,time,shutil,httpx
ROOT=Path(__file__).resolve().parents[1];demo=ROOT/'data/demo';out=ROOT/'data/tests';c=httpx.Client(base_url='http://127.0.0.1:8767',timeout=120,trust_env=False);personal=httpx.Client(base_url='http://127.0.0.1:8765',trust_env=False);before=personal.get('/api/assets').json();created=[]
def ok(r):assert r.is_success,r.text;return r.json()
def track(folder,name):created.append((demo/folder/name).resolve())
try:
 with (out/'official-reference.wav').open('rb') as f:a=ok(c.post('/api/import',files={'file':('Sharing test.wav',f)}))
 track('audio',a['id']+'.json');track('audio',a['file']);track('originals',a['original'])
 assert not any(x['id']==a['id'] for x in personal.get('/api/assets').json())
 p=ok(c.post('/api/profiles',json={'name':'Sharing verification TEST','asset':a['id'],'transcript':'Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.'}));track('profiles',p['id']+'.json');track('references',p['reference'])
 j=ok(c.post('/api/generate',json={'profile':p['id'],'text':'This is the private sharing demo.','language':'English'}))
 for _ in range(120):
  job=ok(c.get('/api/jobs/'+j['id']))
  if job['status'] in ['complete','failed']:break
  time.sleep(1)
 assert job['status']=='complete',job
 g=job['asset'];track('audio',g['id']+'.json');track('audio',g['file']);shutil.copyfile(demo/'audio'/g['file'],out/'sharing-generated.wav')
 assert personal.get('/api/assets').json()==before
 (out/'demo-functional-checks.json').write_text(json.dumps({'isolated_from_personal':True,'generation':g,'status':'passed'},indent=2))
 print(json.dumps({'status':'passed','duration':g['duration'],'generation':g['generation'],'isolated_from_personal':True}))
finally:
 for path in created:
  assert path.is_relative_to(demo.resolve())
  path.unlink(missing_ok=True)

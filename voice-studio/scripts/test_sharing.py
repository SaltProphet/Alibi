from pathlib import Path
import httpx,json
r=Path('voice-studio');state=json.loads((r/'logs/sharing.json').read_text());url=state['url'];checks={}
with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
 for path in ['/','/api/assets','/api/profiles','/api/sessions']:
  x=c.get(url+path);checks[path]={'status':x.status_code,'location':x.headers.get('location','')[:200],'content_type':x.headers.get('content-type')}
  print(path,x.status_code,x.headers.get('location','')[:150])
  assert x.status_code in [302,303,307,401,403],x.text[:400]
 for port in [8765,8767]:
  h=c.get(f'http://127.0.0.1:{port}/api/health').json();a=c.get(f'http://127.0.0.1:{port}/api/assets').json();print(port,{'demo':h.get('demo',False),'assets':len(a)})
  if port==8767:
   assert h.get('demo') and 'data' not in h
   assert c.get('http://127.0.0.1:8767/api/health',headers={'Origin':url}).status_code==200
   assert c.get('http://127.0.0.1:8767/api/health',headers={'Origin':'https://evil.example'}).status_code==403
(r/'data/tests/sharing-checks.json').write_text(json.dumps(checks,indent=2))

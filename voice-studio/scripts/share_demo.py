"""Start/stop a temporary EMAIL-PROTECTED Cloudflare demo. Never create an open tunnel."""
from pathlib import Path
import sys,os,json,time,subprocess,re,shutil
import httpx
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'logs/sharing.json'
ALLOW=ROOT/'logs/sharing-allowlist.json'

def write(state):
    tmp=STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state,indent=2),encoding='utf-8');tmp.replace(STATE)

def alive(pid):
    import psutil
    try:return psutil.Process(pid).is_running()
    except psutil.Error:return False

def stop():
    import psutil
    if not STATE.exists():print('Demo sharing is already off.');return
    state=json.loads(STATE.read_text(encoding='utf-8'))
    # Check PID creation time and exact command before stopping only our processes.
    for name in ['tunnel','demo']:
        item=state.get(name,{})
        try:
            p=psutil.Process(item['pid'])
            if abs(p.create_time()-item['created'])>.1:continue
            cmd=p.cmdline()
            expected='cloudflared' if name=='tunnel' else str(ROOT/'scripts/run_server.py')
            if not any(expected.lower() in part.lower() for part in cmd):continue
            children=p.children(recursive=True)
            for child in children:child.terminate()
            p.terminate()
        except (KeyError,psutil.Error):pass
    state['status']='stopped';write(state)
    print('Demo sharing stopped. Your personal studio remains running.')

def start():
    import psutil
    if not ALLOW.exists():raise SystemExit('Add invited email addresses to logs/sharing-allowlist.json first. No tunnel was started.')
    emails=json.loads(ALLOW.read_text(encoding='utf-8'))
    if not isinstance(emails,list) or not emails or not all(isinstance(e,str) and re.fullmatch(r'[^\s@*]+@[^\s@*]+\.[^\s@*]+',e) for e in emails):
        raise SystemExit('A nonempty list of individual email addresses is required. Wildcard access is not allowed.')
    if STATE.exists():
        previous=json.loads(STATE.read_text(encoding='utf-8'))
        if previous.get('status')=='running' and alive(previous.get('tunnel',{}).get('pid',0)):
            print('Already sharing:',previous['url']);return
    exe=shutil.which('cloudflared')
    if not exe:raise SystemExit('cloudflared is missing. No tunnel was started.')
    help=subprocess.run([exe,'tunnel','--help'],capture_output=True,text=True).stdout
    if '--allowed-mail' not in help:raise SystemExit('This cloudflared does not support email protection. No tunnel was started.')
    with httpx.Client(trust_env=False,timeout=3) as client:
        try:
            inference=client.get('http://127.0.0.1:8766/health');inference.raise_for_status()
        except httpx.HTTPError:raise SystemExit('Start your personal Alibi first so the local inference worker is available.')
        try:client.get('http://127.0.0.1:8767/api/health')
        except httpx.ConnectError:pass
        else:raise SystemExit('Port 8767 is already occupied. Stop the existing demo before starting another.')
    state={'status':'starting','url':'','started':time.time()};write(state)
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    def record(p):return {'pid':p.pid,'created':psutil.Process(p.pid).create_time()}
    try:
        with (ROOT/'logs/demo.log').open('w') as log:
            demo=subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts/run_server.py'),'demo'],cwd=ROOT,stdout=log,stderr=log,creationflags=flags)
        state['demo']=record(demo);write(state)
        ready=False
        for _ in range(40):
            if demo.poll() is not None:raise RuntimeError('Demo server exited. Inspect logs/demo.log.')
            try:
                r=httpx.get('http://127.0.0.1:8767/api/health',timeout=2,trust_env=False)
                if r.is_success and r.json().get('demo'):ready=True;break
            except httpx.HTTPError:pass
            time.sleep(1)
        if not ready:raise RuntimeError('Demo server did not become ready.')
        args=[exe,'tunnel','--url','http://127.0.0.1:8767','--http-host-header','127.0.0.1','--no-autoupdate']
        for email in emails:args+=['--allowed-mail',email]
        with (ROOT/'logs/demo-tunnel.log').open('w') as log:
            tunnel=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=log,creationflags=flags)
        state['tunnel']=record(tunnel);write(state)
        for _ in range(60):
            if tunnel.poll() is not None:raise RuntimeError('Protected tunnel exited. Inspect logs/demo-tunnel.log.')
            log=(ROOT/'logs/demo-tunnel.log').read_text(encoding='utf-8',errors='replace')
            match=re.search(r'https://[a-z0-9-]+\.trycloudflare\.com',log)
            if match:
                state.update(url=match.group(),status='running');write(state)
                print('Email-protected demo:',state['url'])
                print('Only allowlisted emails may sign in. All guests share the demo workspace.')
                print('Stop sharing with Stop-Demo-Sharing.cmd.');return
            time.sleep(1)
        raise RuntimeError('No protected tunnel URL was returned.')
    except Exception:
        stop();raise

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='stop':stop()
    else:start()

"""Video media contracts using real FFmpeg; isolated data, no mocked codecs."""
import hashlib,json,os,sys,uuid,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
os.environ['VOICE_STUDIO_DATA']=str(root/'data/tests'/('video-contract-'+uuid.uuid4().hex))
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from backend import app as studio
c=TestClient(studio.app)

def check(response):
    assert response.status_code==200,response.text
    return response.json()

def main():
    ffmpeg=__import__('shutil').which('ffmpeg'); assert ffmpeg
    originals=[]; videos=[]
    fixture_dir=studio.DATA/'fixtures';fixture_dir.mkdir()
    subprocess.run([ffmpeg,'-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=24','-t','12','-an','-c:v','libx264','-pix_fmt','yuv420p',str(fixture_dir/'video-fixture.mp4')],check=True)
    subprocess.run([ffmpeg,'-nostdin','-v','error','-i',str(fixture_dir/'video-fixture.mp4'),'-an','-c:v','libvpx-vp9',str(fixture_dir/'video-fixture.webm')],check=True)
    for ext in ('mp4','webm'):
        fixture=fixture_dir/('video-fixture.'+ext)
        with fixture.open('rb') as f:v=check(c.post('/api/videos/import',files={'file':(fixture.name,f)}))
        assert v['duration']==12 and v['width']==640 and not v['has_audio']
        source=studio.DATA/'videos'/v['file'];originals.append((source,hashlib.sha256(source.read_bytes()).hexdigest()))
        r=c.get(v['url'],headers={'Range':'bytes=0-99'});assert r.status_code==206 and len(r.content)==100
        videos.append(v)
    assert c.post('/api/videos/import',files={'file':('invalid.mp4',b'bad-video')}).status_code==400
    assert c.post('/api/videos/import',files={'file':('audio.wav',b'bad')}).status_code==400
    assert len(list((studio.DATA/'videos').glob('*.mp4')))==1
    assert c.get('/api/videos/bad/source').status_code==400
    clips=[]
    for at in (2,6):
        p=studio.DATA/'audio'/(studio.uid()+'.wav');t=np.arange(48000)/48000;sf.write(p,.2*np.sin(2*np.pi*440*t),48000)
        a=studio.register(p,'timing tone');clips.append({'id':studio.uid(),'asset':a['id'],'at':at,'end':at+2})
    project={'start':2,'end':10,'clips':clips,'text':'Timing test','profile':''}
    v=videos[0]
    assert c.post('/api/videos/'+v['id']+'/project',json={**project,'start':11,'end':10}).status_code==400
    bad=[{**clips[0],'end':2.1}];assert c.post('/api/videos/'+v['id']+'/export',json={**project,'clips':bad}).status_code==400
    assert c.post('/api/videos/'+v['id']+'/export',json={**project,'clips':[]}).status_code==400
    assert c.post('/api/videos/'+v['id']+'/project',json={**project,'end':13}).status_code==400
    check(c.post('/api/videos/'+v['id']+'/project',json=project))
    metrics=[]
    for v in videos:
        result=check(c.post('/api/videos/'+v['id']+'/export',json=project))
        output=studio.DATA/'video-exports'/(result['id']+'.mp4')
        assert c.get(result['url']).status_code==200
        decoded=output.with_suffix('.wav');subprocess.run([ffmpeg,'-nostdin','-v','error','-i',str(output),'-vn',str(decoded)],check=True)
        x,sr=sf.read(decoded)
        rms=lambda start,end:float(np.sqrt(np.mean(x[int(start*sr):int(end*sr)]**2)))
        levels=[rms(0,1.8),rms(2.1,2.9),rms(3.2,5.8),rms(6.1,6.9),rms(7.2,11.8)]
        assert levels[1]>.1 and levels[3]>.1 and max(levels[0],levels[2],levels[4])<.001,levels
        metrics.append({'input':v['name'],'export':str(output),'rms_windows':levels})
    # Existing audio import/edit/reference/session/mix path still completes with actual audio.
    fixture=studio.DATA/'audio'/(clips[0]['asset']+'.wav')
    with fixture.open('rb') as f:a=check(c.post('/api/import',files={'file':('tone.wav',f)}))
    edited=check(c.post('/api/assets/'+a['id']+'/process',json={'start':.1,'end':.9,'normalize':True}))
    check(c.post('/api/profiles',json={'name':'test reference','asset':edited['id'],'transcript':'test tone'}))
    session={'name':'audio regression','tracks':[{'id':'voice','name':'Voice'}],'clips':[{'id':'take','asset':edited['id'],'track':'voice','at':.5,'in':0,'out':edited['duration']}]}
    saved=check(c.post('/api/sessions',json=session));assert c.get('/api/sessions/'+saved['id']).json()['clips']==saved['clips']
    result=check(c.post('/api/export',json=session));assert c.get(result['url']).status_code==200 and result['duration']>1
    for path,digest in originals:assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
    print(json.dumps({'pass':True,'media':metrics,'audio_regression':'import, trim, normalize, reference, save/reopen session, mixed WAV','originals_unchanged':True},indent=2))
if __name__=='__main__': main()

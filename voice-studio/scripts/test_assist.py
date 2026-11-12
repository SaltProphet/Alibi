"""AI helper contracts, isolated temporary data; no models or live services needed."""
import os,sys,time,hashlib,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
test_root=Path(__file__).resolve().parents[1]/'data/tests'
test_root.mkdir(parents=True,exist_ok=True)
os.environ['VOICE_STUDIO_DATA']=str(test_root/('assist-contract-'+uuid.uuid4().hex))
import numpy as np,soundfile as sf
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend import app as studio
from backend import assist
c=TestClient(studio.app)

def done(response):
    assert response.status_code==200,response.text
    id=response.json()['id']
    for _ in range(100):
        j=c.get('/api/jobs/'+id).json()
        if j['status'] in ('complete','failed'): return j
        time.sleep(.01)
    raise AssertionError('Job did not finish')

def test_assist():
    id=studio.uid();p=studio.DATA/'audio'/(id+'.wav');sf.write(p,np.zeros(48000),48000)
    studio.register(p,'test');before=hashlib.sha256(p.read_bytes()).hexdigest()
    with patch.object(assist,'transcribe',return_value={'text':'Hello studio.','language':'en','model':'test','segments':[{'start':0,'end':1,'text':'Hello studio.'}]}):
        j=done(c.post('/api/assets/'+id+'/transcribe',json={}))
    assert j['status']=='complete' and j['result']['asset']==id
    assert studio.load('transcripts',j['result']['id'])==j['result']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==before
    assert c.post('/api/assets/not-an-id/transcribe',json={}).status_code==400
    assert c.post('/api/assist/draft',json={'target':'unknown','text':'x','instruction':'rewrite'}).status_code==422
    assert c.post('/api/assist/voice-design',json={'description':'x','text':''}).status_code==422
    with patch.object(assist,'draft',return_value={'text':'An edited line.','model':'test'}):
        assert done(c.post('/api/assist/draft',json={'target':'dialogue','text':'Hello','instruction':'rewrite','context':'Other speaker says goodbye'}))['result']['text']=='An edited line.'
    with patch.object(assist,'asr_status',return_value={'available':False,'reason':'Missing local model'}):
        assert done(c.post('/api/assets/'+id+'/transcribe',json={}))['error']=='Missing local model'
    assert c.post('/api/assist/draft',headers={'Origin':'https://example.com'},json={'text':'','instruction':'x'}).status_code==403
    os.environ['VOICE_STUDIO_DEMO']='1'
    try:
        assert c.get('/api/assist/capabilities').json()=={'enabled':False}
        assert c.post('/api/assist/draft',json={'text':'','instruction':'x'}).status_code==403
        assert c.post('/api/assets/'+id+'/transcribe',json={}).status_code==403
        assert c.post('/api/assist/voice-design',json={'description':'warm','text':'hello'}).status_code==403
    finally: os.environ.pop('VOICE_STUDIO_DEMO')
    print('PASS: transcript provenance, immutable audio, draft validation, missing model, origin rejection, demo isolation')

if __name__=='__main__': test_assist()

"""Voice Studio API; all original inputs are immutable and each edit creates a derivative."""
from pathlib import Path
import json,uuid,shutil,subprocess,os,time,threading
from concurrent.futures import ThreadPoolExecutor
import soundfile as sf
import numpy as np
import httpx
from fastapi import FastAPI,HTTPException,UploadFile,File,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
from .audio import process,mix
from . import assist
ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('VOICE_STUDIO_DATA',ROOT/'data')).resolve()
WORKER=os.environ.get('VOICE_STUDIO_WORKER_URL','http://127.0.0.1:8766').rstrip('/')
for folder in ['originals','audio','references','profiles','sessions','exports','tests','folders']: (DATA/folder).mkdir(parents=True,exist_ok=True)
app=FastAPI(title='Voice Studio'); app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
pool=ThreadPoolExecutor(max_workers=1); jobs={}; guard=threading.Lock()
@app.middleware('http')
async def local_origin(request:Request,call_next):
    origin=request.headers.get('origin')
    allowed=['http://127.0.0.1:8765','http://localhost:8765','http://127.0.0.1:5178','http://localhost:5178']
    allowed.append(str(request.base_url).rstrip('/'))
    if os.environ.get('VOICE_STUDIO_DEMO')=='1':
        allowed += ['http://127.0.0.1:8767','http://localhost:8767']
        config=ROOT/'logs/sharing.json'
        if config.exists():
            try:
                public=json.loads(config.read_text(encoding='utf-8')).get('url','')
                if public.startswith('https://') and public.endswith('.trycloudflare.com'):
                    allowed.append(public)
            except (ValueError,OSError): pass
    if origin and origin not in allowed: return JSONResponse({'detail':'This browser origin is not allowed.'},status_code=403)
    return await call_next(request)
def uid(): return uuid.uuid4().hex
def key(s):
    if len(s)!=32 or any(c not in '0123456789abcdef' for c in s): raise HTTPException(400,'Invalid identifier.')
    return s

def load(folder,id):
    p=DATA/folder/(key(id)+'.json')
    if not p.exists(): raise HTTPException(404,'Item not found.')
    return json.loads(p.read_text(encoding='utf-8'))
def save(folder,item):
    p=DATA/folder/(key(item['id'])+'.json'); temp=p.with_suffix('.tmp')
    with guard: temp.write_text(json.dumps(item,indent=2),encoding='utf-8'); temp.replace(p)
    return item
def entries(folder): return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((DATA/folder).glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)]
def assetpath(id): return DATA/'audio'/load('audio',id)['file']
def register(path,name,**extra):
    id=path.stem; info=sf.info(path)
    return save('audio',dict(id=id,file=path.name,name=name,duration=info.duration,sample_rate=info.samplerate,channels=info.channels,created=time.time(),**extra))
@app.exception_handler(ValueError)
async def value_error(request,exc): return JSONResponse({'detail':str(exc)},status_code=400)
@app.get('/api/health')
def health():
    try: worker=httpx.get(WORKER+'/health',timeout=2,trust_env=False).json()
    except Exception: worker={'status':'unavailable'}
    if os.environ.get('VOICE_STUDIO_DEMO')=='1':
        return {'status':'ready','inference':worker,'demo':True,'notice':'Shared demo workspace: invited guests can see files saved here. Personal studio files are separate.'}
    return {'status':'ready','inference':worker,'data':str(DATA)}
@app.get('/api/assets')
def assets(): return entries('audio')
@app.get('/api/folders')
def folders(): return entries('folders')
class Folder(BaseModel):
    name:str=Field(min_length=1,max_length=80)
@app.post('/api/folders')
def create_folder(f:Folder):
    name=' '.join(f.name.split())
    if not name: raise HTTPException(400,'Folder name cannot be empty.')
    if any(x['name'].casefold()==name.casefold() for x in entries('folders')): raise HTTPException(409,'A folder with that name already exists.')
    return save('folders',{'id':uid(),'name':name,'created':time.time()})
@app.post('/api/assets/{id}/folder')
def move_asset(id:str, payload:dict):
    a=load('audio',id); folder=payload.get('folder') or ''
    if folder: load('folders',folder)
    a['folder']=folder; return save('audio',a)
@app.delete('/api/assets/{id}')
def delete_asset(id:str):
    a=load('audio',id)
    profiles_using=[p['name'] for p in entries('profiles') if p.get('asset')==id]
    session_using=any(any(c.get('asset')==id for c in s.get('clips',[])) for s in entries('sessions'))
    if profiles_using or session_using:
        used=[]
        if profiles_using: used.append('saved voice profile: '+', '.join(profiles_using))
        if session_using: used.append('saved arrangement')
        raise HTTPException(409,'Recording is still used by '+'; '.join(used)+'. Remove that reference first.')
    for key_name in ('file','original'):
        value=a.get(key_name)
        if value:
            base='audio' if key_name=='file' else 'originals'
            (DATA/base/value).unlink(missing_ok=True)
    (DATA/'audio'/(id+'.json')).unlink(missing_ok=True)
    return {'deleted':id}
@app.get('/api/assets/{id}/audio')
def audio(id:str): return FileResponse(assetpath(id),media_type='audio/wav',filename=load('audio',id)['name']+'.wav')
@app.get('/api/assets/{id}/original')
def original(id:str):
    a=load('audio',id)
    if not a.get('original'): raise HTTPException(404,'This asset has no imported original.')
    return FileResponse(DATA/'originals'/a['original'],filename=a.get('original_name',a['original']))
@app.post('/api/import')
async def import_audio(file:UploadFile=File(...)):
    name=Path(file.filename or 'recording.webm').name; suffix=Path(name).suffix.lower()
    if suffix not in ['.wav','.mp3','.flac','.webm','.ogg','.m4a','.mp4']: raise HTTPException(400,'Use WAV, MP3, FLAC, or a browser audio recording.')
    id=uid(); source=DATA/'originals'/(id+suffix); target=DATA/'audio'/(id+'.wav')
    size=0
    with source.open('wb') as out:
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size>250*1024*1024: raise HTTPException(413,'The upload limit is 250 MB.')
            out.write(chunk)
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise HTTPException(503,'FFmpeg is missing from PATH.')
    result=subprocess.run([ffmpeg,'-nostdin','-v','error','-i',str(source),'-vn','-ar','48000','-ac','1','-c:a','pcm_s16le',str(target)],capture_output=True,text=True,timeout=180)
    if result.returncode: raise HTTPException(400,'Cannot decode audio: '+result.stderr[-1200:])
    return register(target,Path(name).stem,original=source.name,original_name=name)
class Edit(BaseModel):
    start:float=Field(default=0,ge=0); end:float=Field(gt=0)
    highpass:bool=False; denoise:bool=False; normalize:bool=False
    strength:float=Field(default=.7,ge=0,le=1)
    fade_in:float=Field(default=0,ge=0,le=60); fade_out:float=Field(default=0,ge=0,le=60)
    pitch:float=Field(default=0,ge=-12,le=12)
    timbre:float=Field(default=0,ge=-1,le=1)
    vibrato:float=Field(default=0,ge=0,le=1)
@app.post('/api/assets/{id}/process')
def cleanup(id:str,ops:Edit):
    a=load('audio',id); x,sr=process(assetpath(id),ops.model_dump()); p=DATA/'audio'/(uid()+'.wav'); sf.write(p,x,sr,subtype='PCM_16')
    return register(p,a['name']+' edited',parent=id,operations=ops.model_dump())
class Profile(BaseModel):
    name:str=Field(min_length=1,max_length=100); asset:str
    transcript:str=Field(min_length=1,max_length=10000)
@app.get('/api/profiles')
def profiles(): return entries('profiles')
@app.post('/api/profiles')
def profile(p:Profile):
    a=load('audio',p.asset)
    if not .5<=a['duration']<=60: raise HTTPException(400,'Choose a voice reference between 0.5 and 60 seconds.')
    id=uid(); dest=DATA/'references'/(id+'.wav'); shutil.copyfile(assetpath(p.asset),dest)
    extra={'synthetic':True,'designed':True,'voice_description':a['voice_description']} if a.get('voice_description') else {}
    return save('profiles',dict(id=id,reference=dest.name,**p.model_dump(),**extra))
class Generation(BaseModel):
    profile:str; text:str=Field(min_length=1,max_length=10000)
    language:str='English'
def run_generation(id,g):
    try:
        jobs[id]['status']='running'; p=load('profiles',g.profile); target=DATA/'audio'/(uid()+'.wav')
        with httpx.Client(timeout=1800,trust_env=False) as client:
            result=client.post(WORKER+'/generate',json={'reference':str(DATA/'references'/p['reference']),'transcript':p['transcript'],'text':g.text,'language':g.language,'output':str(target)})
        if not result.is_success: raise RuntimeError(result.json().get('detail',result.text))
        provenance={'synthetic':True,'voice_description':p['voice_description']} if p.get('voice_description') else {}
        asset=register(target,'Speech '+time.strftime('%H-%M-%S'),profile=g.profile,text=g.text,generation=result.json(),**provenance)
        jobs[id].update(status='complete',asset=asset)
    except httpx.ConnectError:
        jobs[id].update(status='failed',error='The local inference worker is unavailable. Restart Voice Studio using its launcher, then try again.')
    except Exception as e: jobs[id].update(status='failed',error=str(e))
@app.post('/api/generate')
def generate(g:Generation):
    load('profiles',g.profile)
    with guard:
        if any(j['status'] in ['queued','running'] for j in jobs.values()): raise HTTPException(409,'A studio job is already running.')
        id=uid(); jobs[id]={'id':id,'status':'queued'}
    pool.submit(run_generation,id,g); return jobs[id]
@app.get('/api/jobs/{id}')
def job(id:str):
    if id not in jobs: raise HTTPException(404,'Job not found. It may have ended during a restart.')
    return jobs[id]
class Track(BaseModel):
    id:str; name:str; volume:float=Field(default=1,ge=0,le=2); mute:bool=False
class Clip(BaseModel):
    id:str; asset:str; track:str; at:float=Field(ge=0); in_:float=Field(alias='in',ge=0); out:float=Field(gt=0)
class Session(BaseModel):
    name:str=Field(min_length=1,max_length=100); tracks:list[Track]; clips:list[Clip]
    id:str|None=None

def validated(s):
    obj=s.model_dump(by_alias=True)
    ids={t['id'] for t in obj['tracks']}
    for c in obj['clips']:
        a=load('audio',c['asset'])
        if c['track'] not in ids or not c['in']<c['out']<=a['duration']+.002: raise ValueError('Invalid clip or track.')
    return obj
@app.get('/api/sessions')
def sessions(): return entries('sessions')
@app.post('/api/sessions')
def save_session(s:Session):
    obj=validated(s); obj['id']=s.id or uid(); return save('sessions',obj)
@app.get('/api/sessions/{id}')
def session(id:str): return load('sessions',id)
@app.post('/api/export')
def export(s:Session):
    obj=validated(s); x,sr,gain=mix(obj['tracks'],obj['clips'],assetpath)
    id=uid(); p=DATA/'exports'/(id+'.wav'); sf.write(p,x,sr,subtype='PCM_16')
    result={'id':id,'name':s.name,'duration':len(x)/sr,'gain':gain,'url':'/api/exports/'+id}; save('exports',result); return result
@app.get('/api/exports/{id}')
def download_export(id:str):
    obj=load('exports',id); return FileResponse(DATA/'exports'/(key(id)+'.wav'),media_type='audio/wav',filename='Voice-Studio-Mix.wav')
@app.get('/api/assist/capabilities')
def assist_capabilities():
    if os.environ.get('VOICE_STUDIO_DEMO')=='1': return {'enabled':False}
    return {'enabled':True,'transcription':assist.asr_status(),
            'writing_model':os.environ.get('VOICE_STUDIO_AI_MODEL','gpt-oss:20b'),
            'voice_design':(Path(os.environ.get('VOICE_STUDIO_MODELS',ROOT/'models'))/'Qwen3-TTS-12Hz-1.7B-VoiceDesign/config.json').is_file()}

def assist_job(fn):
    assist.require_private()
    with guard:
        if any(j['status'] in ['queued','running'] for j in jobs.values()):
            raise HTTPException(409,'A studio job is already running. Wait for it to finish.')
        id=uid(); jobs[id]={'id':id,'status':'queued'}
    def run():
        jobs[id]['status']='running'
        try: jobs[id].update(status='complete',result=fn())
        except HTTPException as e: jobs[id].update(status='failed',error=str(e.detail))
        except Exception as e: jobs[id].update(status='failed',error=str(e))
    pool.submit(run)
    return jobs[id]

@app.post('/api/assist/draft')
def draft_text(r:assist.Draft): return assist_job(lambda:assist.draft(r))

@app.post('/api/assets/{id}/transcribe')
def transcribe_asset(id:str):
    assist.require_private()
    a=load('audio',id)
    if a['duration']>600: raise HTTPException(400,'Choose a recording of at most 10 minutes for transcription.')
    def run():
        result=assist.transcribe(assetpath(id))
        item={'id':uid(),'asset':id,'created':time.time(),**result}
        save('transcripts',item)
        return item
    return assist_job(run)

class VoiceDesign(BaseModel):
    description:str=Field(min_length=1,max_length=2000)
    text:str=Field(min_length=1,max_length=1000)
    language:str=Field(default='English',max_length=40)

@app.post('/api/assist/voice-design')
def design_voice(r:VoiceDesign):
    def run():
        target=DATA/'audio'/(uid()+'.wav')
        with httpx.Client(timeout=1800,trust_env=False) as c:
            response=c.post(WORKER+'/design',json={**r.model_dump(),'output':str(target)})
        if not response.is_success: raise HTTPException(503,response.json().get('detail','Voice design failed.'))
        return register(target,'Designed voice '+time.strftime('%H-%M-%S'),synthetic=True,
                        voice_description=r.description,text=r.text,generation=response.json())
    return assist_job(run)

(DATA/'transcripts').mkdir(parents=True,exist_ok=True)
from .video import create_router as video_router
app.include_router(video_router(DATA,load,save,entries,uid,assetpath))
DIST=ROOT/'frontend/dist'
if DIST.exists(): app.mount('/',StaticFiles(directory=DIST,html=True),name='studio')

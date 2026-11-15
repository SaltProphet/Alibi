"""Local inference worker. The studio backend never imports torch."""
from pathlib import Path
import os,threading,time
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME',str(ROOT/'cache/huggingface'))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['GRADIO_ANALYTICS_ENABLED']='False'
from fastapi import FastAPI,HTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
app=FastAPI(); lock=threading.Lock(); model=None; model_kind=None; model_last_used=None
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost'])
MODELS={'Base':'Qwen3-TTS-12Hz-1.7B-Base','VoiceDesign':'Qwen3-TTS-12Hz-1.7B-VoiceDesign'}
DEVICE={'device':None,'dtype':None,'gpu':None,'vram':None,'error':None}

def model_root(): return Path(os.environ.get('ALIBI_MODELS',ROOT/'models'))

def probe_device():
    """Learn the accelerator once, off the request path, so /health stays instant."""
    try:
        import torch
        if torch.cuda.is_available():
            free,total=torch.cuda.mem_get_info()
            DEVICE.update(device='cuda:0',dtype='bfloat16',gpu=torch.cuda.get_device_name(0),vram={'total':total,'free':free})
        else:
            DEVICE.update(device='cpu',dtype='float32',gpu=None,vram=None)
    except Exception as e:
        DEVICE['error']=f'{type(e).__name__}: {e}'
threading.Thread(target=probe_device,daemon=True).start()

def live_vram():
    if DEVICE.get('device')!='cuda:0': return None
    try:
        import torch
        free,total=torch.cuda.mem_get_info()
        return {'total':total,'free':free}
    except Exception:
        return DEVICE.get('vram')

def touch():
    global model_last_used
    model_last_used=time.time()

def unload_model():
    global model,model_kind,model_last_used
    import gc
    model=None; model_kind=None; model_last_used=None
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available(): torch.cuda.empty_cache()
    except Exception: pass

class Request(BaseModel):
    reference:str
    transcript:str=Field(min_length=1,max_length=10000)
    text:str=Field(min_length=1,max_length=10000)
    language:str='English'
    output:str

@app.get('/health')
def health(): return {'status':'ready','loaded':model is not None,'model':model_kind,'last_used':model_last_used,
                     'device':DEVICE.get('device'),'dtype':DEVICE.get('dtype'),'gpu':DEVICE.get('gpu'),'vram':live_vram()}

@app.get('/models')
def models():
    entries=[]
    for kind,folder in MODELS.items():
        path=model_root()/folder
        size=0
        if path.exists():
            for root,_dirs,files in os.walk(path):
                for name in files:
                    try: size+=os.path.getsize(os.path.join(root,name))
                    except OSError: pass
        entries.append({'kind':kind,'folder':folder,'present':(path/'config.json').is_file(),'bytes':size,'loaded':model_kind==kind})
    return {'loaded':model_kind,'device':DEVICE.get('device'),'gpu':DEVICE.get('gpu'),'error':DEVICE.get('error'),'models':entries}

class ModelRequest(BaseModel):
    kind:str

@app.post('/models/load')
def load_endpoint(r:ModelRequest):
    if r.kind not in MODELS: raise HTTPException(400,'Unknown model.')
    if not lock.acquire(blocking=False): raise HTTPException(409,'Inference is busy. Wait for the current job.')
    try:
        load_model(r.kind)
        return {'loaded':model_kind}
    except Exception as e: raise HTTPException(500,f'{type(e).__name__}: {e}')
    finally: lock.release()

@app.post('/models/unload')
def unload_endpoint():
    if not lock.acquire(blocking=False): raise HTTPException(409,'Inference is busy. Wait for the current job.')
    try:
        unload_model(); return {'loaded':None}
    finally: lock.release()

@app.post('/admin/shutdown')
def shutdown():
    def stop():
        time.sleep(0.2); os._exit(0)
    threading.Thread(target=stop,daemon=True).start()
    return {'status':'stopping'}

def load_model(kind):
    global model,model_kind
    import torch,gc
    from qwen_tts import Qwen3TTSModel
    if model is not None and model_kind==kind: touch(); return model
    cuda=torch.cuda.is_available(); device='cuda:0' if cuda else 'cpu'; dtype=torch.bfloat16 if cuda else torch.float32
    model=None; model_kind=None; gc.collect()
    if cuda: torch.cuda.empty_cache()
    if cuda:
        free,_=torch.cuda.mem_get_info()
        if free<6*2**30: raise RuntimeError('Less than 6 GiB GPU memory is free. Free resources before generating.')
    path=model_root()/MODELS[kind]
    if not (path/'config.json').is_file(): raise RuntimeError('Local '+kind+' model is missing. See AI-HELPERS.md.')
    model=Qwen3TTSModel.from_pretrained(str(path),device_map=device,dtype=dtype,attn_implementation='sdpa',local_files_only=True)
    model_kind=kind; touch()
    return model
@app.post('/generate')
def generate(r:Request):
    global model
    reference=Path(r.reference).resolve(); output=Path(r.output).resolve()
    if not reference.is_relative_to(ROOT/'data') or not output.is_relative_to(ROOT/'data'): raise HTTPException(400,'Audio must be inside the studio data folder.')
    if not lock.acquire(blocking=False): raise HTTPException(409,'Inference is busy. Wait for the current generation.')
    try:
        import torch,soundfile as sf
        from qwen_tts import Qwen3TTSModel
        torch.set_num_threads(4)
        load_model('Base')
        t=time.time()
        # On some Windows/CUDA driver combinations this bookkeeping call raises
        # OSError(22) even though inference itself is available. Treat memory
        # telemetry as optional so it cannot fail a generation.
        if torch.cuda.is_available():
            try: torch.cuda.reset_peak_memory_stats()
            except OSError: pass
        wavs,sr=model.generate_voice_clone(text=r.text,language=r.language,ref_audio=str(reference),ref_text=r.transcript,max_new_tokens=2048)
        import numpy as np
        if len(wavs[0]) == 0 or not np.isfinite(wavs[0]).all():
            raise RuntimeError('The model returned empty or invalid audio.')
        sf.write(output,wavs[0],sr,subtype='PCM_16')
        touch()
        try: peak_gpu_gib=torch.cuda.max_memory_allocated()/2**30 if torch.cuda.is_available() else None
        except OSError: peak_gpu_gib=None
        return {'seconds':len(wavs[0])/sr,'elapsed':time.time()-t,'peak_gpu_gib':peak_gpu_gib}
    except Exception as e:
        raise HTTPException(500,f'{type(e).__name__}: {e}')
    finally: lock.release()

class DesignRequest(BaseModel):
    description:str=Field(min_length=1,max_length=2000)
    text:str=Field(min_length=1,max_length=1000)
    language:str='English'
    output:str

@app.post('/design')
def design(r:DesignRequest):
    output=Path(r.output).resolve()
    if not output.is_relative_to(ROOT/'data'): raise HTTPException(400,'Audio must be inside the studio data folder.')
    if not lock.acquire(blocking=False): raise HTTPException(409,'Inference is busy. Wait for the current generation.')
    try:
        import torch,soundfile as sf,numpy as np
        torch.set_num_threads(4)
        m=load_model('VoiceDesign'); t=time.time()
        wavs,sr=m.generate_voice_design(text=r.text,language=r.language,instruct=r.description,max_new_tokens=1024)
        if not len(wavs[0]) or not np.isfinite(wavs[0]).all(): raise RuntimeError('The model returned empty or invalid audio.')
        sf.write(output,wavs[0],sr,subtype='PCM_16')
        touch()
        return {'seconds':len(wavs[0])/sr,'elapsed':time.time()-t,'model':'VoiceDesign'}
    except Exception as e: raise HTTPException(500,f'{type(e).__name__}: {e}')
    finally: lock.release()

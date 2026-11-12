from pathlib import Path
import os,time,json
ROOT=Path(__file__).resolve().parents[1]
os.environ['HF_HOME']=str(ROOT/'cache'/'huggingface')
import torch,soundfile as sf,numpy as np
from qwen_tts import Qwen3TTSModel
print({'torch':torch.__version__,'cuda':torch.version.cuda,'available':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name(0)},flush=True)
torch.set_num_threads(4)
t=time.time()
model=Qwen3TTSModel.from_pretrained(str(ROOT/'models/Qwen3-TTS-12Hz-1.7B-Base'),device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')
wavs,sr=model.generate_voice_clone(text='Hello. This is a local voice cloning test for Voice Studio.',language='English',ref_audio=str(ROOT/'data/tests/official-reference.wav'),ref_text='Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it! And thanks to you.',max_new_tokens=512)
p=ROOT/'data/tests/phase1-generated.wav'
sf.write(p,wavs[0],sr,subtype='PCM_16')
x,sr=sf.read(p)
result={'path':str(p),'sample_rate':sr,'seconds':len(x)/sr,'peak':float(np.max(np.abs(x))),'finite':bool(np.isfinite(x).all()),'elapsed':time.time()-t,'peak_gpu_allocated_gib':torch.cuda.max_memory_allocated()/2**30}
assert result['seconds']>1 and result['peak']>0 and result['finite']
(ROOT/'data/tests/phase1-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)

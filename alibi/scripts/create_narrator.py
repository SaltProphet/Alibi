from pathlib import Path
import os,json,time,shutil
ROOT=Path(__file__).resolve().parents[1]
os.environ['HF_HOME']=str(ROOT/'cache/huggingface')
from huggingface_hub import snapshot_download
path=ROOT/'models/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
print('Downloading official VoiceDesign model',flush=True)
snapshot_download('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',local_dir=path)
import torch,soundfile as sf,numpy as np
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
cuda=torch.cuda.is_available();device='cuda:0' if cuda else 'cpu';dtype=torch.bfloat16 if cuda else torch.float32
print('Loading VoiceDesign with',device,flush=True)
m=Qwen3TTSModel.from_pretrained(str(path),device_map=device,dtype=dtype,attn_implementation='sdpa',local_files_only=True)
text="Welcome to Alibi. Let's take a quick look around, from recording your voice to creating your final mix."
instruct='A clearly adult woman in her thirties with a friendly, natural speaking voice. Warm, confident, and welcoming, like a helpful podcast host introducing her studio. Medium pitch, clear full-voiced pronunciation, normal conversational pace and breathing, gently upbeat. Relaxed and approachable, with restrained expression. No seductive delivery, no sultry tone, no breathy or husky effect, no whispering, no exaggerated vocal fry, no background music.'
print('Generating friendly natural adult female narrator',flush=True)
wavs,sr=m.generate_voice_design(text=text,language='English',instruct=instruct,max_new_tokens=512)
p=ROOT/'data/onboarding-narrator';p.mkdir(exist_ok=True)
sf.write(p/'reference.wav',wavs[0],sr,subtype='PCM_16')
assert len(wavs[0])>sr and np.isfinite(wavs[0]).all()
(p/'reference.json').write_text(json.dumps({'transcript':text,'voice_description':instruct,'model':'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign','sample_rate':sr,'seconds':len(wavs[0])/sr,'synthetic':True},indent=2))
pack=ROOT/'content/narrator';pack.mkdir(parents=True,exist_ok=True)
for name in ['reference.wav','reference.json']:
    shutil.copyfile(p/name,pack/name)
print('NARRATOR READY',len(wavs[0])/sr,flush=True)

"""Create four synthetic character voices, preserving all existing user profiles."""
from pathlib import Path
import os,json,uuid,time,shutil
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'content/archetypes';PACK.mkdir(exist_ok=True)
os.environ['HF_HOME']=str(ROOT/'cache/huggingface');os.environ['HF_HUB_OFFLINE']='1'
voices=[
 {'key':'nova','name':'Nova Prime','description':'An adult woman with a clear, friendly, confident natural American English voice. Medium pitch, bright but relaxed, articulate podcast presenter. No breathy effect or seductive tone.','text':'This is Nova Prime. A clear voice, a fresh idea, and a whole studio waiting for you.'},
 {'key':'atlas','name':'Atlas Deep','description':'An adult man in his forties with a deep resonant baritone, warm, grounded and calm. Natural American English, articulate, unhurried cinematic storyteller. A human speaking voice, not a growl.','text':'This is Atlas Deep. Rich resonance, quiet confidence, and room for every word to land.'},
 {'key':'cyra','name':'Cyra Synth','description':'An adult woman with a bright, precise, agile voice. Crisp American English, slightly higher medium pitch, an energetic futuristic assistant with a subtle smile. Clear human pronunciation, not robotic, no childlike qualities.','text':'This is Cyra Synth. Crisp edges, bright ideas, and a little spark of the unexpected.'},
 {'key':'echo','name':'Echo ASMR','description':'An adult woman with a gentle, softly spoken, intimate voice. Warm and lightly airy, calm clear American English, quiet reading voice. Not seductive, no moaning, no exaggerated breath sounds.','text':'This is Echo. A softer voice, a quieter space, and a moment to listen closely.'}
]
model=None
for v in voices:
 p=PACK/(v['key']+'.wav')
 if not p.exists():
  if v['key']=='nova':shutil.copyfile(ROOT/'content/narrator/reference.wav',p);v['text']=json.loads((ROOT/'content/narrator/reference.json').read_text())['transcript']
  else:
   if model is None:
    import torch,soundfile as sf
    from qwen_tts import Qwen3TTSModel
    torch.set_num_threads(4)
    cuda=torch.cuda.is_available();device='cuda:0' if cuda else 'cpu';dtype=torch.bfloat16 if cuda else torch.float32
    model=Qwen3TTSModel.from_pretrained(str(ROOT/'models/Qwen3-TTS-12Hz-1.7B-VoiceDesign'),device_map=device,dtype=dtype,attn_implementation='sdpa',local_files_only=True)
   print('Designing',v['name'],flush=True)
   wavs,sr=model.generate_voice_design(text=v['text'],language='English',instruct=v['description'],max_new_tokens=512)
   sf.write(p,wavs[0],sr,subtype='PCM_16')
  (PACK/(v['key']+'.json')).write_text(json.dumps(v,indent=2),encoding='utf-8')
 else:v=json.loads((PACK/(v['key']+'.json')).read_text(encoding='utf-8'))
 for data in [ROOT/'data',ROOT/'data/demo']:
  for sub in ['audio','profiles','references']:(data/sub).mkdir(parents=True,exist_ok=True)
  profiles=[json.loads(f.read_text(encoding='utf-8')) for f in (data/'profiles').glob('*.json')]
  if any(x.get('archetype')==v['key'] for x in profiles):continue
  import soundfile as sf
  aid=uuid.uuid4().hex;pid=uuid.uuid4().hex;info=sf.info(p)
  shutil.copyfile(p,data/'audio'/(aid+'.wav'));shutil.copyfile(p,data/'references'/(pid+'.wav'))
  asset=dict(id=aid,file=aid+'.wav',name=v['name']+' · Voice preview',duration=info.duration,sample_rate=info.samplerate,channels=info.channels,created=time.time(),synthetic=True,archetype=v['key'])
  profile=dict(id=pid,name=v['name'],asset=aid,reference=pid+'.wav',transcript=v['text'],synthetic=True,archetype=v['key'],description=v['description'])
  (data/'audio'/(aid+'.json')).write_text(json.dumps(asset,indent=2),encoding='utf-8');(data/'profiles'/(pid+'.json')).write_text(json.dumps(profile,indent=2),encoding='utf-8')
 print('Installed',v['name'],flush=True)
print('ALL FOUR VOICES READY',flush=True)

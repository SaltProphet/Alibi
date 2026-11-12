from pathlib import Path
import argparse,os
ROOT=Path(__file__).resolve().parents[1]
os.environ['HF_HOME']=str(ROOT/'cache'/'huggingface')
os.environ['GRADIO_ANALYTICS_ENABLED']='False'
from huggingface_hub import snapshot_download
parser=argparse.ArgumentParser()
parser.add_argument('--voice-design',action='store_true',help='Also download the optional VoiceDesign model.')
args=parser.parse_args()
repos=['Qwen/Qwen3-TTS-12Hz-1.7B-Base','Qwen/Qwen3-TTS-Tokenizer-12Hz']
if args.voice_design: repos.append('Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign')
for repo in repos:
    print('Downloading',repo,flush=True)
    snapshot_download(repo,local_dir=ROOT/'models'/repo.split('/')[-1])
print('DOWNLOAD COMPLETE',flush=True)

"""Dedicated loopback test instance; never opens personal data."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));os.chdir(ROOT)
os.environ['VOICE_STUDIO_DATA']=str(ROOT/'data/tests/immersive')
import uvicorn
uvicorn.run('backend.app:app',host='127.0.0.1',port=8875)

"""Signal-level checks for filter attenuation, fades, mute, and mix gain."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,soundfile as sf
from backend.audio import process,mix
folder=ROOT/'data/tests';sr=48000;t=np.arange(sr*2)/sr
x=.2*np.sin(2*np.pi*20*t)+.2*np.sin(2*np.pi*1000*t)
p=folder/'dsp-input.wav';sf.write(p,x,sr,subtype='FLOAT')
y,_=process(p,{'start':0,'end':2,'highpass':True})
def amplitude(y,f):return abs(np.sum(y[sr:,0]*np.exp(-2j*np.pi*f*t[sr:])))*2/sr
assert amplitude(y,20)<.01 and amplitude(y,1000)>.19
f,_=process(p,{'start':0,'end':2,'fade_in':.2,'fade_out':.2})
assert abs(f[0,0])<1e-7 and abs(f[-1,0])<1e-7
tracks=[{'id':'a','volume':.3,'mute':False},{'id':'b','volume':1,'mute':True}]
clips=[{'asset':'input','track':'a','at':.5,'in':.25,'out':1.25},{'asset':'input','track':'b','at':0,'in':0,'out':1}]
out,rate,gain=mix(tracks,clips,lambda _:p)
assert np.max(abs(out[:24000]))==0
source,_=sf.read(p,always_2d=True)
assert np.allclose(out[24000:,0],source[12000:60000,0]*.3,atol=1e-7)
tracks[0]['volume']=10
out,rate,gain=mix(tracks,clips,lambda _:p);assert gain<1 and np.max(abs(out))<=.99001
print('PASS: 80 Hz high-pass attenuation, fade endpoints, clip offsets/trims, track volume/mute, clipping prevention')

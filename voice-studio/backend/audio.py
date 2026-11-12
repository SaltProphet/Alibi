"""Non-destructive processing and mixing using SoundFile, SciPy, and noisereduce."""
import numpy as np
import soundfile as sf
from scipy import signal
import noisereduce as nr
from math import gcd

def read(path, rate=None):
    x,sr=sf.read(path,dtype='float32',always_2d=True)
    if rate and rate!=sr:
        g=gcd(rate,sr); x=signal.resample_poly(x,rate//g,sr//g,axis=0); sr=rate
    return x,sr

def process(path,ops):
    x,sr=read(path)
    start=float(ops.get('start',0)); end=float(ops.get('end',len(x)/sr))
    if not 0<=start<end<=len(x)/sr+0.001: raise ValueError('Trim must fall inside the recording.')
    x=x[int(start*sr):int(end*sr)].copy()
    if any(ops.get(key,0) for key in ['pitch','timbre','vibrato']):
        from pedalboard import Pedalboard,HighShelfFilter,LowShelfFilter,Chorus
        effects=[]
        if ops.get('pitch'):
            import librosa
            x=librosa.effects.pitch_shift(x.T,sr=sr,n_steps=float(ops['pitch'])).T
        if ops.get('timbre'):
            color=float(ops['timbre'])
            effects.extend([LowShelfFilter(cutoff_frequency_hz=350,gain_db=-color*6),HighShelfFilter(cutoff_frequency_hz=2500,gain_db=color*8)])
        if ops.get('vibrato'):effects.append(Chorus(rate_hz=5,depth=float(ops['vibrato'])*.6,centre_delay_ms=7,feedback=0,mix=1))
        if effects:x=Pedalboard(effects)(x.T.copy(),sr).T
    if ops.get('highpass'):
        x=signal.sosfilt(signal.butter(4,80,fs=sr,btype='highpass',output='sos'),x,axis=0)
    if ops.get('denoise'):
        x=nr.reduce_noise(y=x.T,sr=sr,prop_decrease=float(ops.get('strength',0.7)),stationary=False).T
    if ops.get('normalize'):
        peak=np.max(np.abs(x))
        if peak>1e-8: x=x/peak*10**(-1/20)
    for key,reverse in [('fade_in',False),('fade_out',True)]:
        n=min(len(x),int(float(ops.get(key,0))*sr))
        if n:
            ramp=np.linspace(0,1,n)[:,None]
            if reverse: x[-n:]*=ramp[::-1]
            else: x[:n]*=ramp
    return np.clip(x,-1,1),sr

def mix(tracks,clips,lookup):
    sr=48000; length=0; pieces=[]
    trackmap={t['id']:t for t in tracks}
    for c in clips:
        t=trackmap.get(c['track'])
        if t is None: raise ValueError('Clip refers to a missing track.')
        x,_=read(lookup(c['asset']),sr)
        start=float(c['in']); end=float(c['out']); at=float(c['at'])
        if not 0<=start<end<=len(x)/sr+0.002 or at<0: raise ValueError('Invalid clip bounds.')
        x=x[int(start*sr):int(end*sr)]
        if x.shape[1]==1: x=np.repeat(x,2,axis=1)
        x=x[:,:2]*float(t.get('volume',1))*(0 if t.get('mute') else 1)
        offset=round(at*sr); length=max(length,offset+len(x)); pieces.append((offset,x))
    if not pieces: raise ValueError('Add at least one clip before exporting.')
    if length>sr*3600: raise ValueError('Mix duration exceeds the one-hour limit.')
    out=np.zeros((length,2),dtype=np.float32)
    for offset,x in pieces: out[offset:offset+len(x)]+=x
    peak=float(np.max(np.abs(out)))
    # Apply a uniform gain only when summing would clip.
    gain=min(1,0.99/peak) if peak else 1
    return out*gain,sr,gain

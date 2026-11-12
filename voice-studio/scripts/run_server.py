from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import uvicorn
if sys.argv[1] == 'backend':
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8765)
elif sys.argv[1] == 'inference':
    uvicorn.run('inference.app:app', host='127.0.0.1', port=8766)
elif sys.argv[1] == 'demo':
    os.environ['VOICE_STUDIO_DATA'] = str(ROOT / 'data' / 'demo')
    os.environ['VOICE_STUDIO_DEMO'] = '1'
    uvicorn.run('backend.app:app', host='127.0.0.1', port=8767)

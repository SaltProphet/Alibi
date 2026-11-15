from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import uvicorn
def port(default, name):
    try: return int(os.environ.get(name, default))
    except ValueError: return int(default)
if sys.argv[1] == 'backend':
    uvicorn.run('backend.app:app', host='127.0.0.1', port=port(8765, 'ALIBI_PORT'))
elif sys.argv[1] == 'inference':
    uvicorn.run('inference.app:app', host='127.0.0.1', port=port(8766, 'ALIBI_INFERENCE_PORT'))
elif sys.argv[1] == 'demo':
    os.environ['ALIBI_DATA'] = str(ROOT / 'data' / 'demo')
    os.environ['ALIBI_DEMO'] = '1'
    uvicorn.run('backend.app:app', host='127.0.0.1', port=port(8767, 'ALIBI_DEMO_PORT'))

"""Private video projects: immutable uploads and bounded narration-only MP4 exports."""
import json
import math
import shutil
import subprocess
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict

class VideoClip(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: str
    asset: str
    at: float = Field(ge=0)
    end: float = Field(gt=0)

class VideoProject(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(default='', max_length=10000)
    profile: str = ''
    clips: list[VideoClip] = Field(default_factory=list, max_length=100)

def create_router(data, load, save, entries, uid, assetpath):
    router = APIRouter(prefix='/api')
    for folder in ('videos', 'video-exports'):
        (data / folder).mkdir(parents=True, exist_ok=True)

    def tool(name):
        path = shutil.which(name)
        if not path:
            raise HTTPException(503, f'{name} is missing from PATH. Restart with FFmpeg and FFprobe available.')
        return path

    def run(args, timeout=600):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise HTTPException(408, 'Video processing timed out. Try a shorter video.')
        if result.returncode:
            raise HTTPException(400, 'Cannot process this video: ' + result.stderr[-1200:])
        return result.stdout

    @router.get('/videos')
    def videos():
        return entries('videos')

    @router.post('/videos/import')
    async def import_video(file: UploadFile = File(...)):
        name = Path(file.filename or 'video').name
        suffix = Path(name).suffix.lower()
        if suffix not in ('.mp4', '.webm'):
            raise HTTPException(400, 'Choose an MP4 or WebM video.')
        probe = tool('ffprobe')
        id = uid()
        source = data / 'videos' / (id + suffix)
        try:
            size = 0
            with source.open('wb') as out:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > 250 * 1024 * 1024:
                        raise HTTPException(413, 'The video upload limit is 250 MB.')
                    out.write(chunk)
            # Inspect container streams rather than trusting the filename or browser metadata.
            from starlette.concurrency import run_in_threadpool
            raw = await run_in_threadpool(run, [probe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(source)], 30)
            meta = json.loads(raw)
            video = next((s for s in meta['streams'] if s['codec_type'] == 'video'), None)
            if not video:
                raise HTTPException(400, 'The file has no video stream.')
            duration = float(video.get('duration') or meta['format'].get('duration') or 0)
            if not math.isfinite(duration) or not 0 < duration <= 3600:
                raise HTTPException(400, 'Choose a video with a known duration of up to one hour.')
            return save('videos', {'id': id, 'name': name, 'file': source.name, 'duration': duration,
                'width': video['width'], 'height': video['height'],
                'has_audio': any(s['codec_type'] == 'audio' for s in meta['streams']),
                'url': f'/api/videos/{id}/source', 'project': {'start': 0, 'end': duration, 'text': '', 'profile': '', 'clips': []}})
        except Exception:
            source.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    @router.get('/videos/{id}/source')
    def source(id: str):
        v = load('videos', id)
        return FileResponse(data / 'videos' / v['file'], media_type='video/webm' if v['file'].endswith('.webm') else 'video/mp4')

    def validate(v, project):
        if not 0 <= project.start < project.end <= v['duration'] + .001:
            raise HTTPException(400, 'Choose a range inside the video.')
        ids = set()
        for clip in project.clips:
            a = load('audio', clip.asset)
            if clip.id in ids or not clip.at < clip.end <= v['duration'] + .001:
                raise HTTPException(400, 'Invalid narration range or duplicate clip.')
            ids.add(clip.id)
            if clip.at + a['duration'] > clip.end + .001:
                raise HTTPException(400, 'Speech is longer than its range. Widen the range or regenerate shorter text.')
        return project.model_dump()

    @router.post('/videos/{id}/project')
    def project(id: str, project: VideoProject):
        v = load('videos', id)
        v['project'] = validate(v, project)
        return save('videos', v)

    @router.post('/videos/{id}/export')
    def export(id: str, project: VideoProject):
        v = load('videos', id)
        obj = validate(v, project)
        if not project.clips:
            raise HTTPException(400, 'Place a narration clip before exporting.')
        ffmpeg = tool('ffmpeg')
        export_id = uid()
        target = data / 'video-exports' / (export_id + '.mp4')
        args = [ffmpeg, '-nostdin', '-v', 'error', '-i', str(data / 'videos' / v['file'])]
        filters = []
        for i, clip in enumerate(project.clips, 1):
            args += ['-i', str(assetpath(clip.asset))]
            filters.append(f'[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,adelay={round(clip.at*48000)}S:all=1[a{i}]')
        labels = ''.join(f'[a{i}]' for i in range(1, len(project.clips)+1))
        filters.append(f'{labels}amix=inputs={len(project.clips)}:normalize=0,alimiter=limit=0.95:level=false:latency=true,apad,atrim=duration={v["duration"]}[narration]')
        args += ['-filter_complex', ';'.join(filters), '-map', '0:v:0', '-map', '[narration]',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-t', str(v['duration']), '-movflags', '+faststart', str(target)]
        try:
            run(args)
            v['project'] = obj
            save('videos', v)
            return save('video-exports', {'id': export_id, 'video': id, 'duration': v['duration'], 'url': f'/api/video-exports/{export_id}', 'name': Path(v['name']).stem + '-narrated.mp4'})
        except Exception:
            target.unlink(missing_ok=True)
            raise

    @router.get('/video-exports/{id}')
    def download(id: str):
        e = load('video-exports', id)
        return FileResponse(data / 'video-exports' / (e['id'] + '.mp4'), media_type='video/mp4', filename=e['name'])

    return router

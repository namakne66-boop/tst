"""
Syntiox DL  –  REST API
=======================
Endpoints:
  GET  /                        health check
  POST /info                    get video / playlist info + available qualities
  POST /download/video          download video as MP4
  POST /download/audio          download audio as MP3
  GET  /status/{job_id}         poll async job progress
  GET  /ffmpeg                  check if ffmpeg is installed

Run:
  pip install fastapi uvicorn yt-dlp
  uvicorn app:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import asyncio
import threading
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import engine  # api/engine.py

# ─────────────────────────────────────────────
#  App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="Syntiox DL API",
    description="YouTube video & audio downloader API powered by yt-dlp",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  In-memory job store  (replace with Redis for prod)
# ─────────────────────────────────────────────
jobs: dict[str, dict] = {}


# ─────────────────────────────────────────────
#  Request / Response models
# ─────────────────────────────────────────────
class InfoRequest(BaseModel):
    url: str

class VideoDownloadRequest(BaseModel):
    url: str
    format_id: str = "best"   # 'best' | '480' | yt-dlp format id
    save_dir: Optional[str] = None

class AudioDownloadRequest(BaseModel):
    url: str
    save_dir: Optional[str] = None


# ─────────────────────────────────────────────
#  Helper: progress hook → job store update
# ─────────────────────────────────────────────
def _make_hook(job_id: str):
    def hook(d: dict):
        job = jobs.get(job_id, {})
        if d["status"] == "downloading":
            raw = d.get("_percent_str", "0%").strip()
            pct = "".join(c for c in raw if c.isprintable() and c != "\x1b")
            job.update({
                "state":    "downloading",
                "percent":  pct,
                "speed":    d.get("_speed_str", "N/A").strip(),
                "eta":      d.get("_eta_str", "N/A").strip(),
            })
        elif d["status"] == "finished":
            job.update({
                "state":   "merging",
                "percent": "100%",
                "file":    d.get("filename", ""),
            })
        jobs[job_id] = job
    return hook


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """API health check."""
    return {"status": "ok", "service": "Syntiox DL API", "version": "1.0.0"}


@app.get("/ffmpeg", tags=["Health"])
def ffmpeg_check():
    """Check whether ffmpeg is available on the server."""
    ok = engine.check_ffmpeg()
    return {"ffmpeg_available": ok}


@app.post("/info", tags=["Info"])
def get_info(body: InfoRequest):
    """
    Fetch metadata for a YouTube video or playlist.

    Returns video title, thumbnail, duration, uploader,
    and a list of available video qualities.
    """
    result = engine.get_info(body.url)
    if result.get("type") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/download/video", tags=["Download"])
def download_video(body: VideoDownloadRequest):
    """
    Start an **async** video download job.

    Returns a `job_id` – poll `/status/{job_id}` for progress.

    `format_id` options:
    - `"best"` – highest quality (default)
    - `"480"`  – 480p max
    - Any yt-dlp format id from `/info` response
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"state": "queued", "type": "video", "percent": "0%"}

    def _run():
        jobs[job_id]["state"] = "downloading"
        result = engine.download_video(
            url=body.url,
            format_id=body.format_id,
            save_dir=body.save_dir,
            progress_hook=_make_hook(job_id),
        )
        if result["status"] == "success":
            jobs[job_id].update({"state": "done", "file": result.get("file", "")})
        else:
            jobs[job_id].update({"state": "error", "message": result.get("message", "Unknown error")})

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id, "message": "Video download started"}


@app.post("/download/audio", tags=["Download"])
def download_audio(body: AudioDownloadRequest):
    """
    Start an **async** audio download job (MP3 192 kbps).

    Returns a `job_id` – poll `/status/{job_id}` for progress.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"state": "queued", "type": "audio", "percent": "0%"}

    def _run():
        jobs[job_id]["state"] = "downloading"
        result = engine.download_audio(
            url=body.url,
            save_dir=body.save_dir,
            progress_hook=_make_hook(job_id),
        )
        if result["status"] == "success":
            jobs[job_id].update({"state": "done", "file": result.get("file", "")})
        else:
            jobs[job_id].update({"state": "error", "message": result.get("message", "Unknown error")})

    threading.Thread(target=_run, daemon=True).start()
    return {"job_id": job_id, "message": "Audio download started"}


@app.get("/status/{job_id}", tags=["Download"])
def get_status(job_id: str):
    """
    Poll the progress of a download job.

    States: `queued` → `downloading` → `merging` → `done` | `error`
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}

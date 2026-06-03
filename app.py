from __future__ import annotations

import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import engine  # api/engine.py

# ─────────────────────────────────────────────
#  App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="Syntiox Smart DL API",
    description="වීඩියෝ විස්තර සමඟ Direct Download ලින්ක් එකම ලබාදෙන API එක",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Request Models
# ─────────────────────────────────────────────
class InfoRequest(BaseModel):
    url: str

# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """API health check."""
    return {"status": "ok", "service": "Syntiox DL API", "version": "2.0.0"}


@app.get("/ffmpeg", tags=["Health"])
def ffmpeg_check():
    """Check whether ffmpeg is available on the server."""
    ok = engine.check_ffmpeg()
    return {"ffmpeg_available": ok}


@app.post("/info", tags=["Info"])
def get_info(body: InfoRequest, request: Request):
    """
    YouTube URL එකක් ලබා දී වීඩියෝ විස්තර (Thumbnail, Title) සමඟ 
    කෙලින්ම බාගත හැකි Direct Download Links ලබාගන්න.
    """
    result = engine.get_info(body.url)
    if result.get("type") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    # දැනට API එක රන් වෙන සර්වර් එකේ Base URL එක ගනිමු (ලෝකල් හෝ ඔන්ලයින්)
    base_url = str(request.base_url).rstrip("/")
    video_url = body.url

    # 1. කෙලින්ම හොඳම වීඩියෝ Quality එක සහ Audio එක බාන්න ප්‍රධාන ලින්ක්ස් දෙකක් හදමු
    result["best_video_download_url"] = f"{base_url}/direct-download?url={video_url}&format_id=best&type=video"
    result["audio_download_url"] = f"{base_url}/direct-download?url={video_url}&type=audio"

    # 2. ඔයාට Quality එක තෝරන්න ඕන නම්, හැම format ID එකකටම වෙන වෙනම Download ලින්ක්ස් හදමු
    if "formats" in result:
        for fmt in result["formats"]:
            fmt_id = fmt.get("id")
            fmt["download_url"] = f"{base_url}/direct-download?url={video_url}&format_id={fmt_id}&type=video"

    return result


@app.get("/direct-download", tags=["Download"])
def direct_download(
    url: str = Query(..., description="YouTube URL"),
    type: str = Query("video", description="'video' හෝ 'audio'"),
    format_id: str = Query("best", description="Format ID එක")
):
    """
    මෙම Endpoint එක මගින් සර්වර් එක ඇතුලේ වීඩියෝව බාගෙන, 
    එසැණින් එය පරිශීලකයාගේ උපාංගයට Direct File එකක් ලෙස ලබාදෙයි.
    """
    # සර්වර් එකේ තාවකාලිකව සේව් කරන්න ඕනේ නිසා save_dir එක null (None) කරමු
    if type == "video":
        result = engine.download_video(
            url=url,
            format_id=format_id,
            save_dir=None,
            progress_hook=lambda d: None  # සින්ක්‍රනස් නිසා හුක්ස් අවශ්‍ය නැත
        )
    else:
        result = engine.download_audio(
            url=url,
            save_dir=None,
            progress_hook=lambda d: None
        )

    # ෆයිල් එක සාර්ථකව බාගත්තා නම් කෙලින්ම බ්‍රවුසර් එකට push කරමු
    if result.get("status") == "success":
        file_path = result.get("file")
        if file_path and os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                filename=os.path.basename(file_path),
                media_type="application/octet-stream"
            )

    raise HTTPException(status_code=400, detail=result.get("message", "Download failed"))

# Syntiox DL — REST API

YouTube video & audio downloader API built with **FastAPI** + **yt-dlp**.  
Same core engine as the desktop GUI app — 100% working.

---

## 🚀 Quick Start

```bash
cd api
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Or just double-click **`run_api.bat`**

Swagger UI → **http://localhost:8000/docs**

---

## 📡 Endpoints

### Health
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API health check |
| `GET` | `/ffmpeg` | Check if ffmpeg is installed |

### Info
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/info` | Get video/playlist info + all available qualities |

**Request:**
```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

**Response (video):**
```json
{
  "type": "video",
  "title": "Rick Astley - Never Gonna Give You Up",
  "thumb": "https://...",
  "duration": 212,
  "uploader": "Rick Astley",
  "formats": [
    { "id": "137", "res": "1080p", "ext": "mp4" },
    { "id": "136", "res": "720p",  "ext": "mp4" },
    { "id": "135", "res": "480p",  "ext": "mp4" },
    { "id": "134", "res": "360p",  "ext": "mp4" }
  ]
}
```

**Response (playlist):**
```json
{
  "type": "playlist",
  "title": "My Playlist",
  "count": 12,
  "videos": [
    { "title": "Song 1", "url": "https://..." }
  ]
}
```

---

### Download Video
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/download/video` | Start async video download (MP4) |

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "best",
  "save_dir": "C:/Users/YourName/Videos"
}
```

> `format_id` options:
> - `"best"` — highest quality (default)
> - `"480"` — max 480p
> - Any format `id` from `/info` response (e.g. `"137"` for 1080p)

**Response:**
```json
{ "job_id": "abc-123", "message": "Video download started" }
```

---

### Download Audio (Song)
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/download/audio` | Start async audio download (MP3 192kbps) |

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "save_dir": "C:/Users/YourName/Music"
}
```

**Response:**
```json
{ "job_id": "xyz-456", "message": "Audio download started" }
```

---

### Poll Job Status
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status/{job_id}` | Get download progress |

**Response states:**

| `state` | Meaning |
|---------|---------|
| `queued` | Job created, waiting to start |
| `downloading` | Actively downloading |
| `merging` | Merging video + audio (ffmpeg) |
| `done` | Finished ✅ |
| `error` | Failed ❌ |

**Example (downloading):**
```json
{
  "job_id": "abc-123",
  "state":   "downloading",
  "percent": "67.4%",
  "speed":   "3.21 MiB/s",
  "eta":     "00:12"
}
```

**Example (done):**
```json
{
  "job_id": "abc-123",
  "state": "done",
  "file":  "C:/Users/YourName/Videos/Syntiox DL/Rick Astley_[Best].mp4"
}
```

---

## 📁 Folder Structure

```
api/
├── app.py            ← FastAPI routes
├── engine.py         ← yt-dlp download engine
├── requirements.txt  ← Python dependencies
├── run_api.bat       ← One-click Windows start script
└── README.md         ← This file
```

---

## ⚙️ Default Save Paths

| Type | Default Path |
|------|-------------|
| Video | `~/Videos/Syntiox DL/` |
| Audio | `~/Music/Syntiox DL/` |

Override with `"save_dir"` in the request body.

---

## 🛠 Requirements

- Python 3.10+
- ffmpeg (for high-quality merging & MP3 conversion)
  - Download: https://ffmpeg.org/download.html
  - Add to system PATH

import yt_dlp
import os
import shutil
import uuid

# ──────────────────────────────────────────────
#  Silent logger (suppress yt-dlp console noise)
# ──────────────────────────────────────────────
class _SilentLogger:
    def debug(self, msg):   pass
    def warning(self, msg): pass
    def error(self, msg):   print(f"[ENGINE ERROR] {msg}")


# ──────────────────────────────────────────────
#  Shared yt-dlp headers & extractor args
# ──────────────────────────────────────────────
_COMMON_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'nocheckcertificate': True,
    'source_address': '0.0.0.0',
    'extractor_args': {'youtube': ['player_client=android,web']},
    'http_headers': {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
    },
}


# ──────────────────────────────────────────────
#  Helper: extract & rank video formats
# ──────────────────────────────────────────────
def _extract_formats(info: dict) -> list[dict]:
    formats_dict: dict[str, dict] = {}
    for f in info.get('formats', []):
        vcodec    = f.get('vcodec', '')
        ext       = f.get('ext', '')
        height    = f.get('height')
        format_id = f.get('format_id')

        if vcodec != 'none' and height:
            res   = f"{height}p"
            score = 0
            if 'avc' in vcodec: score += 10
            if ext == 'mp4':    score += 5

            if res not in formats_dict or score > formats_dict[res]['score']:
                formats_dict[res] = {
                    'id':    format_id,
                    'res':   res,
                    'ext':   ext,
                    'score': score,
                }

    sorted_formats = sorted(
        formats_dict.values(),
        key=lambda x: int(x['res'].replace('p', '')),
        reverse=True,
    )
    return [{'id': f['id'], 'res': f['res'], 'ext': f['ext']} for f in sorted_formats]


# ──────────────────────────────────────────────
#  Public API functions
# ──────────────────────────────────────────────

def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on this machine."""
    return shutil.which('ffmpeg') is not None or os.path.exists('ffmpeg.exe')


def get_info(url: str) -> dict:
    """
    Fetch metadata for a single video or a playlist.

    Returns:
        {type: 'video',    title, thumb, duration, uploader, formats: [...]}
      | {type: 'playlist', title, count, videos: [{title, url}]}
      | {type: 'error',   message}
    """
    opts = {
        **_COMMON_OPTS,
        'extract_flat': 'in_playlist',
        'logger': _SilentLogger(),
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:               # playlist
                videos = [
                    {'title': e.get('title'), 'url': e.get('url')}
                    for e in info['entries'] if e.get('url')
                ]
                return {
                    'type':   'playlist',
                    'title':  info.get('title'),
                    'count':  len(videos),
                    'videos': videos,
                }
            else:                               # single video
                return {
                    'type':     'video',
                    'title':    info.get('title'),
                    'thumb':    info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'formats':  _extract_formats(info),
                }
    except Exception as exc:
        return {'type': 'error', 'message': str(exc)}


def download_video(
    url: str,
    format_id: str = 'best',
    save_dir: str | None = None,
    progress_hook=None,
) -> dict:
    """
    Download a video (MP4).

    Args:
        url:           YouTube / playlist URL
        format_id:     yt-dlp format id, or 'best' / '480'
        save_dir:      folder to save; defaults to ~/Videos/Syntiox DL
        progress_hook: optional yt-dlp progress hook callable

    Returns:
        {status: 'success', file: <path>} | {status: 'error', message: ...}
    """
    save_dir = save_dir or os.path.join(os.path.expanduser('~'), 'Videos', 'Syntiox DL')
    os.makedirs(save_dir, exist_ok=True)

    resolution_tag = '_[Best]' if format_id == 'best' else f'_[{format_id}p]'

    if format_id == '480':
        fmt = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
    elif format_id == 'best':
        fmt = 'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        fmt = f'{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/best'

    opts = {
        **_COMMON_OPTS,
        'quiet':   False,
        'verbose': False,
        'logger':  _SilentLogger(),
        'format':               fmt,
        'merge_output_format':  'mp4',
        'outtmpl':              f'{save_dir}/%(title)s{resolution_tag}.%(ext)s',
        'live_from_start':      True,
        'retries':              15,
        'fragment_retries':     15,
        'continuedl':           True,
    }

    if progress_hook:
        opts['progress_hooks'] = [progress_hook]

    saved_file: list[str] = []

    def _capture_hook(d):
        if d['status'] == 'finished':
            saved_file.append(d.get('filename', ''))
        if progress_hook:
            progress_hook(d)

    opts['progress_hooks'] = [_capture_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return {'status': 'success', 'file': saved_file[0] if saved_file else ''}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}


def download_audio(
    url: str,
    save_dir: str | None = None,
    progress_hook=None,
) -> dict:
    """
    Download audio as MP3 (192 kbps).

    Args:
        url:           YouTube URL
        save_dir:      folder to save; defaults to ~/Music/Syntiox DL
        progress_hook: optional yt-dlp progress hook callable

    Returns:
        {status: 'success', file: <path>} | {status: 'error', message: ...}
    """
    save_dir = save_dir or os.path.join(os.path.expanduser('~'), 'Music', 'Syntiox DL')
    os.makedirs(save_dir, exist_ok=True)

    opts = {
        **_COMMON_OPTS,
        'quiet':   False,
        'verbose': False,
        'logger':  _SilentLogger(),
        'format':  'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': f'{save_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key':              'FFmpegExtractAudio',
            'preferredcodec':   'mp3',
            'preferredquality': '192',
        }],
        'live_from_start':  True,
        'retries':          15,
        'fragment_retries': 15,
        'continuedl':       True,
    }

    saved_file: list[str] = []

    def _capture_hook(d):
        if d['status'] == 'finished':
            saved_file.append(d.get('filename', ''))
        if progress_hook:
            progress_hook(d)

    opts['progress_hooks'] = [_capture_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return {'status': 'success', 'file': saved_file[0] if saved_file else ''}
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}

import yt_dlp
import os
import shutil

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
    """Fetch metadata for a single video or a playlist."""
    opts = {
        **_COMMON_OPTS,
        'extract_flat': 'in_playlist',
        'logger': _SilentLogger(),
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
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
            else:
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
    """Download a video (MP4)."""
    if not save_dir:
        save_dir = os.path.join(os.getcwd(), 'downloads')
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
        'format':              fmt,
        'merge_output_format':  'mp4',
        'outtmpl':              f'{save_dir}/%(title)s{resolution_tag}.%(ext)s',
        'live_from_start':      True,
        'retries':              15,
        'fragment_retries':     15,
        'continuedl':           True,
    }

    # ⭐ මෙතනදී අපි බාන හැම ෆයිල් කෑල්ලක්ම සහ ffmpeg එකෙන් හදන අලුත් ෆයිල් එකත් ලිස්ට් එකකට ගන්නවා
    saved_files: list[str] = []

    def _capture_hook(d):
        if d['status'] == 'finished':
            saved_files.append(d.get('filename', ''))
        if progress_hook:
            progress_hook(d)

    # ⭐ ffmpeg එක වැඩේ ඉවර කරපු ගමන් ලැබෙන සැබෑ ෆයිල් එක මෙතනින් ගන්නවා
    def _postprocessor_hook(d):
        if d['status'] == 'finished':
            f = d.get('info_dict', {}).get('_filename')
            if f:
                saved_files.append(f)

    opts['progress_hooks'] = [_capture_hook]
    opts['postprocessor_hooks'] = [_postprocessor_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        # ⭐ ලිස්ට් එකේ අන්තිමටම තියෙන (ffmpeg එකෙන් හදලා ඉතුරු කරපු) ඇත්තටම සර්වර් එකේ තියෙන ෆයිල් එක හොයනවා
        final_path = ""
        for f in reversed(saved_files):
            if f and os.path.exists(f):
                final_path = os.path.abspath(f)
                break

        if final_path:
            return {'status': 'success', 'file': final_path}
        else:
            return {'status': 'error', 'message': 'ෆයිල් එක සර්වර් එකේ සොයාගත නොහැක!'}
            
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}


def download_audio(
    url: str,
    save_dir: str | None = None,
    progress_hook=None,
) -> dict:
    """Download audio as MP3 (192 kbps)."""
    if not save_dir:
        save_dir = os.path.join(os.getcwd(), 'downloads')
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

    saved_files: list[str] = []

    def _capture_hook(d):
        if d['status'] == 'finished':
            saved_files.append(d.get('filename', ''))
        if progress_hook:
            progress_hook(d)

    def _postprocessor_hook(d):
        if d['status'] == 'finished':
            f = d.get('info_dict', {}).get('_filename')
            if f:
                saved_files.append(f)

    opts['progress_hooks'] = [_capture_hook]
    opts['postprocessor_hooks'] = [_postprocessor_hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        
        final_path = ""
        for f in reversed(saved_files):
            if f and os.path.exists(f):
                final_path = os.path.abspath(f)
                break

        if final_path:
            return {'status': 'success', 'file': final_path}
        else:
            return {'status': 'error', 'message': 'ඕඩියෝ ෆයිල් එක සොයාගත නොහැක!'}
            
    except Exception as exc:
        return {'status': 'error', 'message': str(exc)}

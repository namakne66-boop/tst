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
        'Cookie': 'LOGIN_INFO=AFmmF2swRQIgEXYzDP3a9w9YGx4A6vMF9KdNErTuTnT_ftM-NZWnNnoCIQC8XZAUxZqemQZzAVD5n2UUOX_xenTYdHSxSn1WNNA7_w:QUQ3MjNmeWpmdmVSVUYxTEVWLWt1ZXo0ZlBWazVZX2Jncjd1dF9SSmdxbkVUU05hRHJUMXl3Q1EtQjR4TzNsajdOS0VUeEkyZ0Fidk9ERnduZGdSaDJYWTU5LUJhV08xc2ktaE93UWxxdThjbXFxTGJvdUo3X0l2LTVYTzhBVUFhWG10MFdtdllYWndURnpSaTBGTGc0aGRtcFBKSDVYM1RB; HSID=Avwq1qkydt_H5poBs; SSID=Af_mZlWVHJARcDEYP; APISID=dGDiPpXG0w2M0AJr/AuKGkvegYCgXFnI_s; SAPISID=I7NA85D4KPZfnLZB/AYuM3OMaxiltjhMov; __Secure-1PAPISID=I7NA85D4KPZfnLZB/AYuM3OMaxiltjhMov; __Secure-3PAPISID=I7NA85D4KPZfnLZB/AYuM3OMaxiltjhMov; SID=g.a000-ggJBiCPKp1W-YdYr-zT0Jb-eFGY-QSFH865FK8KlAK1acg4wCT6klx43_fDXiHzOW1NJgACgYKATcSARISFQHGX2Mi0EytrEQnpUutgwxUecFBWBoVAUF8yKoahfMMXxm566qU7Fao0_NO0076; __Secure-1PSID=g.a000-ggJBiCPKp1W-YdYr-zT0Jb-eFGY-QSFH865FK8KlAK1acg4dMZNoDuKs38kJIR2gHTwHAACgYKARESARISFQHGX2MiRogXAdy09PQKryN75oDwLRoVAUF8yKriIBBGr4efe2rirQMIafhM0076; __Secure-3PSID=g.a000-ggJBiCPKp1W-YdYr-zT0Jb-eFGY-QSFH865FK8KlAK1acg4Y71iuA-f-ogn9VzhMxZiNwACgYKASISARISFQHGX2Miar3Wq2cRHOfRARnkCYOORBoVAUF8yKrfwB8TmFfk_L8dFEAyKe0p0076; PREF=f6=40000000&tz=Asia.Colombo&f7=100&f5=20000; CONSISTENCY=AHzIXryqA9wyYrXMRgkn5JUD4BowQxK4bEPtw9ZpbrXhr07lNjjrorEJeMd-WJG02N6Q4_KZyFLt9SJWwrz4_tqy48B0q05uFnhplgoyM9YTVByx2vrKzhkINpsgVe3s07Le0kF_gTiOMkXzBhVMrQC4; __Secure-1PSIDTS=sidts-CjQBhkeRd019Mmw1GIlQ60xhRdWC8yZ_oLfKtrvM2bev0XfOX8kyI-pGyiRPKDzCyypnhAFIEAA; __Secure-3PSIDTS=sidts-CjQBhkeRd019Mmw1GIlQ60xhRdWC8yZ_oLfKtrvM2bev0XfOX8kyI-pGyiRPKDzCyypnhAFIEAA; SIDCC=AKEyXzWD7yuMPtSF1JJulhZA4ZWzOdbg5hrueQ_CfXDcTSDP7MLe3vmG2QVsyUNEB-idgMxORsM; __Secure-1PSIDCC=AKEyXzVwV7eNUooE5YewUJZ1jsubfFutSCaNWm6PLU32GbP4tGLVX3ESdYFDrggRtpDnJV7_7Lk; __Secure-3PSIDCC=AKEyXzV-IA4JCvh9XrPam4gTTTOx-jryu3c-YZvzBJRwDdv7X_Ol38Vfh-VoLx8y6F3n78TnTfw; VISITOR_INFO1_LIVE=XiFOT0SyRV4; VISITOR_PRIVACY_METADATA=CgJMSxIEGgAgbQ%3D%3D; __Secure-YNID=18.YT=MGSFCTy6a0YoYzrYmiAyC8z2h5n-WodqCeSVMMDxBbYEqFYzfswpT9XvMnXfwVFubEGSnBWMewB7cMo7IT5ddIazJSunMDalk68QSw5DVYRVOCk8UNs3E9HbbgPL1pj-H7ZNRK24fvOiM2Ubf1U2c_J5plbnzvnjHTLJ3hwM0rr3zOeOW2_pvRqjLXVkOsraCZ-PRXDXXg67bXjFTxdvpg1J_-uIni5vK9QZ3ecKDWIAZHPSpXelx-0Lv-UT6Clzz2nKU5r-F0m-itqh6Q2pbmxD1YSeu6nY1N6rqwAbSb22no5eRwSUFu4q4EUV67aLJd0kVitXKkcZjn9xOJR2Zg; __Secure-ROLLOUT_TOKEN=CIfX5YGxx5KqIRCe2PaD3MqUAxiegMbI_umUAw%3D%3D; YSC=LXyHPyM3b4Q;'
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
            res = f"{height}p"
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
    """Fetch metadata for a single video, search query, or a playlist."""

    is_search = url.startswith('ytsearch')
    
    opts = {
        **_COMMON_OPTS,
        'logger': _SilentLogger(),
    }
    
    if not is_search:
        opts['extract_flat'] = 'in_playlist'

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                entries = list(info['entries'])
                
                if is_search and len(entries) > 0:
                    video_info = entries[0]
                    return {
                        'type':     'video',
                        'title':    video_info.get('title'),
                        'thumb':    video_info.get('thumbnail'),
                        'duration': video_info.get('duration'),
                        'uploader': video_info.get('uploader'),
                        'formats':  _extract_formats(video_info),
                    }
                else:
          
                    videos = [
                        {'title': e.get('title'), 'url': e.get('url')}
                        for e in entries if e.get('url')
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

import os
import subprocess
from typing import Optional


def _norm_output_path(input_path: str) -> str:
    abs_in = os.path.abspath(input_path)
    parent = os.path.dirname(abs_in)
    stem, _ = os.path.splitext(os.path.basename(abs_in))
    cache_dir = os.path.join(parent, "__jycache__")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{stem}.__jy_norm__.mp4")


def _is_cache_fresh(src: str, dst: str) -> bool:
    if not os.path.exists(dst):
        return False
    try:
        return os.path.getmtime(dst) >= os.path.getmtime(src)
    except OSError:
        return False


def normalize_webm_for_jianying(input_path: str) -> Optional[str]:
    """
    Convert WEBM to JianYing-friendly MP4 before timeline import.

    Output profile:
    - Video: H.264 (libx264), yuv420p
    - Audio: AAC (optional if source has audio)
    """
    src = os.path.abspath(input_path)
    if not os.path.exists(src):
        return None

    dst = _norm_output_path(src)
    if _is_cache_fresh(src, dst):
        return dst

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        src,
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        dst,
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError:
        print("❌ FFmpeg not found. Cannot normalize WEBM for JianYing import.")
        return None
    except Exception as e:
        print(f"❌ WEBM normalization failed: {e}")
        return None

    if proc.returncode != 0 or not os.path.exists(dst):
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"❌ WEBM normalization failed (ffmpeg={proc.returncode}): {err}")
        return None

    return dst

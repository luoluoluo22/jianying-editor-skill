import os
import json
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


def _probe_video(input_path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,pix_fmt",
        "-of",
        "json",
        input_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        return {}
    try:
        streams = json.loads(proc.stdout or "{}").get("streams", [])
    except json.JSONDecodeError:
        return {}
    return streams[0] if streams else {}


def should_normalize_video_for_jianying(input_path: str) -> bool:
    info = _probe_video(input_path)
    if not info:
        return False
    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    return (
        info.get("codec_name") != "h264"
        or info.get("pix_fmt") != "yuv420p"
        or width <= 0
        or height <= 0
        or width % 16 != 0
        or height % 2 != 0
    )


def normalize_video_for_jianying(input_path: str, force: bool = False) -> Optional[str]:
    """
    Convert video to JianYing-friendly MP4 before timeline import.

    Output profile:
    - Video: H.264 (libx264), yuv420p
    - Audio: AAC (optional if source has audio)
    - Geometry: 1920x1080 with padding when needed
    """
    src = os.path.abspath(input_path)
    if not os.path.exists(src):
        return None
    if not force and not should_normalize_video_for_jianying(src):
        return src

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
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-r",
        "30",
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
        print("❌ FFmpeg not found. Cannot normalize video for JianYing import.")
        return None
    except Exception as e:
        print(f"❌ Video normalization failed: {e}")
        return None

    if proc.returncode != 0 or not os.path.exists(dst):
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"❌ Video normalization failed (ffmpeg={proc.returncode}): {err}")
        return None

    return dst


def normalize_webm_for_jianying(input_path: str) -> Optional[str]:
    return normalize_video_for_jianying(input_path, force=True)

import argparse
import json
import os
import subprocess
import sys

from utils.logging_utils import setup_logger


logger = setup_logger("api_validator")


def _bootstrap_import():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    try:
        from jy_wrapper import JyProject
        return JyProject
    except ImportError as e:
        logger.error("Failed to load jy_wrapper: %s", e)
        return None


def check_ffprobe() -> bool:
    try:
        res = subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            logger.info("FFprobe is installed and available in PATH.")
            return True
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning("FFprobe check failed: %s", e)
    logger.warning("FFprobe not found in PATH. Duration fallback may fail for some files.")
    return False


def run_diagnostic(project_name: str, video_path: str, strict: bool = False) -> tuple[int, dict]:
    JyProject = _bootstrap_import()
    if JyProject is None:
        return 1, {"ok": False, "reason": "import_failed", "project": project_name, "video": video_path}

    logger.info("Starting JianYing skill diagnostic...")
    ffprobe_ok = check_ffprobe()
    if strict and not ffprobe_ok:
        return 2, {"ok": False, "reason": "ffprobe_missing", "project": project_name, "video": video_path}

    video_exists = os.path.exists(video_path)
    if not video_exists:
        logger.warning("Test asset missing at: %s", video_path)
        if strict:
            return 2, {"ok": False, "reason": "video_missing", "project": project_name, "video": video_path}

    try:
        project = JyProject(project_name, overwrite=True)
        seg1 = project.add_media_safe(video_path)
        project.add_text_simple("诊断测试: 检查溢出警告")

        if seg1 and hasattr(seg1, "material_instance") and hasattr(seg1.material_instance, "duration"):
            dur_us = seg1.material_instance.duration
            logger.info("Base video duration: %.2fs", dur_us / 1_000_000)
            project.add_media_safe(video_path, source_start=0, duration=f"{(dur_us / 1_000_000) + 10}s")

        logger.info("Testing Timeline Audit warning path...")
        for _ in range(6):
            project.add_media_safe(video_path, source_start="0s", duration="1s")

        save_result = project.save()
        logger.info("Diagnostic completed. Check above logs for warnings.")
        return 0, {
            "ok": True,
            "project": project_name,
            "video": video_path,
            "ffprobe_ok": ffprobe_ok,
            "video_exists": video_exists,
            "save_result": save_result,
        }
    except Exception as e:
        logger.exception("Diagnostic failed: %s", e)
        return 1, {
            "ok": False,
            "reason": "exception",
            "error": str(e),
            "project": project_name,
            "video": video_path,
            "ffprobe_ok": ffprobe_ok,
            "video_exists": video_exists,
        }


def main() -> int:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(current_dir)
    default_video = os.path.join(skill_root, "assets", "video.mp4")

    parser = argparse.ArgumentParser(description="JianYing Skill API diagnostic")
    parser.add_argument("--project", default="Diagnostic_Test", help="Diagnostic draft name")
    parser.add_argument("--video", default=default_video, help="Path to test video")
    parser.add_argument("--strict", action="store_true", help="Fail if ffprobe or test asset is missing")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary")
    args = parser.parse_args()
    code, summary = run_diagnostic(args.project, args.video, strict=args.strict)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

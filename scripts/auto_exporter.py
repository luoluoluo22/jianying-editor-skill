import argparse
import os

from utils.cli_protocol import emit_result, make_result
from utils.env_setup import setup_env
from utils.errors import UserInputError
from utils.logging_utils import setup_logger

setup_env()
logger = setup_logger("auto_exporter")

import pyJianYingDraft as draft  # noqa: E402


def auto_export(
    draft_name: str, output_path: str, resolution: str = None, framerate: str = None
) -> tuple[int, dict]:
    res_map = {
        "480": draft.ExportResolution.RES_480P,
        "720": draft.ExportResolution.RES_720P,
        "1080": draft.ExportResolution.RES_1080P,
        "2K": draft.ExportResolution.RES_2K,
        "4K": draft.ExportResolution.RES_4K,
        "8K": draft.ExportResolution.RES_8K,
    }
    fr_map = {
        "24": draft.ExportFramerate.FR_24,
        "25": draft.ExportFramerate.FR_25,
        "30": draft.ExportFramerate.FR_30,
        "50": draft.ExportFramerate.FR_50,
        "60": draft.ExportFramerate.FR_60,
    }

    target_res = res_map.get(str(resolution).upper() if resolution else "")
    target_fr = fr_map.get(str(framerate) if framerate else "")

    if resolution and target_res is None:
        raise UserInputError(
            f"Unsupported resolution: {resolution} (allowed: {', '.join(res_map.keys())})"
        )
    if framerate and target_fr is None:
        raise UserInputError(
            f"Unsupported framerate: {framerate} (allowed: {', '.join(fr_map.keys())})"
        )

    try:
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        logger.info("Preparing export: draft=%s", draft_name)
        ctrl = draft.JianyingController()
        ctrl.export_draft(draft_name, output_path, resolution=target_res, framerate=target_fr)
        logger.info("Export succeeded: %s", output_path)
        return 0, make_result(
            True,
            "ok",
            "",
            {
                "draft": draft_name,
                "output": output_path,
                "resolution": resolution,
                "fps": framerate,
            },
        )
    except Exception as e:
        logger.error("Export failed: %s", e)
        logger.error("Hint: restart JianYing and keep it on Home/Edit page before retry.")
        return 1, make_result(
            False,
            "export_failed",
            str(e),
            {"draft": draft_name, "output": output_path},
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless draft exporter")
    parser.add_argument("name", help="Draft name")
    parser.add_argument("output", help="Output mp4 path")
    parser.add_argument("--res", help="Resolution: 480/720/1080/2K/4K/8K")
    parser.add_argument("--fps", help="Framerate: 24/25/30/50/60")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args()
    try:
        code, summary = auto_export(args.name, args.output, args.res, args.fps)
    except UserInputError as e:
        logger.error(str(e))
        summary = make_result(
            False, "invalid_input", str(e), {"draft": args.name, "output": args.output}
        )
        code = 2
    emit_result(summary, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

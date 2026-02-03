import sys
import os
import argparse

# 确保能找到 pyJianYingDraft (位于同级或上级的 references 目录)
script_dir = os.path.dirname(os.path.abspath(__file__))
references_dir = os.path.join(os.path.dirname(script_dir), "references")
if references_dir not in sys.path:
    sys.path.append(references_dir)

import pyJianYingDraft as draft

def auto_export(draft_name, output_path, resolution=None, framerate=None):
    try:
        ctrl = draft.JianyingController()
        res_map = {
            "480": draft.ExportResolution.RES_480P,
            "720": draft.ExportResolution.RES_720P,
            "1080": draft.ExportResolution.RES_1080P,
            "2K": draft.ExportResolution.RES_2K,
            "4K": draft.ExportResolution.RES_4K
        }
        fr_map = {
            "24": draft.ExportFramerate.FR_24,
            "25": draft.ExportFramerate.FR_25,
            "30": draft.ExportFramerate.FR_30,
            "50": draft.ExportFramerate.FR_50,
            "60": draft.ExportFramerate.FR_60
        }
        
        target_res = res_map.get(resolution)
        target_fr = fr_map.get(framerate)
        
        print(f"准备导出草稿: {draft_name}")
        ctrl.export_draft(draft_name, output_path, resolution=target_res, framerate=target_fr)
        print(f"导出成功！文件位置: {output_path}")
    except Exception as e:
        print(f"导出失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("output")
    parser.add_argument("--res")
    parser.add_argument("--fps")
    args = parser.parse_args()
    auto_export(args.name, args.output, args.res, args.fps)

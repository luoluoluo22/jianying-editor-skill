import os
import sys
import json
import re
import argparse

"""
JianYing Movie Commentary Builder (Integrated Script)
功能：加载 AI 生成的故事版 JSON，自动完成视频切片、字幕遮罩、双轨原声增强。
"""

# 环境初始化 (由于在 scripts 目录下，直接 import jy_wrapper)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from jy_wrapper import JyProject, draft
except ImportError:
    print("❌ Critical Error: Could not load 'jy_wrapper'.")
    sys.exit(1)

def build_movie_commentary(video_path, storyboard_path, project_name="AI_Movie_Commentary", bgm_path=None, mask_path=None):
    if not os.path.exists(storyboard_path):
        print(f"❌ 错误: 找不到故事版文件 {storyboard_path}")
        return

    with open(storyboard_path, 'r', encoding='utf-8') as f:
        storyboard = json.load(f)

    project = JyProject(project_name, overwrite=True)
    timeline_cursor = 0 

    for i, scene in enumerate(storyboard):
        start_str = scene['start']
        duration = scene['duration']
        text = scene.get('text', '').strip()
        
        # 兼容处理时间格式 (HH:MM:SS 或 MM:SS)
        parts = list(map(int, start_str.split(':')))
        if len(parts) == 2: src_start_us = (parts[0] * 60 + parts[1]) * 1000000
        else: src_start_us = (parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000000
            
        duration_us = int(duration * 1000000)
        
        # A. 添加主视频片段
        project.add_media_safe(video_path, timeline_cursor, duration_us, "MainTrack", source_start=src_start_us)

        if text:
            # B. 字幕遮罩 (如果有)
            if mask_path and os.path.exists(mask_path):
                project.add_media_safe(mask_path, timeline_cursor, duration_us, "MaskTrack", transform_y=-0.85)

            # C. 智能字幕拆分
            split_pattern = r'([，。！？；：,.!?])'
            parts = re.split(split_pattern, text)
            sub_segments = [p for p in parts if p and p not in "，。！？；：,.!?"]
            
            if sub_segments:
                sub_dur_us = duration_us // len(sub_segments)
                local_cursor = timeline_cursor
                for sub_t in sub_segments:
                    display_text = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', sub_t).strip()
                    if display_text:
                        project.add_text_simple(display_text, local_cursor, sub_dur_us, transform_y=-0.8)
                    local_cursor += sub_dur_us
        else:
            # D. 原声高光片段逻辑 (双轨增强)
            project.add_media_safe(video_path, timeline_cursor, duration_us, "HighlightTrack", source_start=src_start_us)

        timeline_cursor += duration_us

    if bgm_path and os.path.exists(bgm_path):
        project.add_audio_safe(bgm_path, 0, timeline_cursor, "BGM_Track")

    project.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="解说视频自动构建工具")
    parser.add_argument("--video", required=True, help="原视频路径")
    parser.add_argument("--json", required=True, help="故事版 JSON 路径")
    parser.add_argument("--name", default="Movie_Commentary_Project", help="项目名称")
    parser.add_argument("--bgm", help="BGM 路径")
    parser.add_argument("--mask", help="遮罩图路径")

    args = parser.parse_args()
    build_movie_commentary(args.video, args.json, args.name, args.bgm, args.mask)

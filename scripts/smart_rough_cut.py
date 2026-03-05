
import sys
import os
import json
import re
from pathlib import Path

# --- 1. 环境配置 (路径注入) ---
from utils.env_setup import setup_env
setup_env()

try:
    from jy_wrapper import JyProject
    from api_client import AntigravityClient
except ImportError as e:
    import warnings
    warnings.warn(f"[smart_rough_cut] Optional dependency missing: {e}. "
                  f"Functions in this module will not be available.")
    JyProject = None
    AntigravityClient = None

# --- 2. 视频分析逻辑 ---
def analyze_video_content(video_path):
    print(f"[*] Analyzing video content using Gemini-3-Pro...")
    
    client = AntigravityClient()
    model = "gemini-3-pro"
    
    prompt = (
        "你是一个专业的视频剪辑师。请分析该视频，找出所有具有'画面冲击力'的精彩片段。\n"
        "重点关注以下内容：\n"
        "1. 喂鸡的动作 (Feeding chickens)\n"
        "2. 特别的肢体动作或交互 (Special actions)\n"
        "3. 画面发生显著变化或视觉突变的时刻 (Visual changes)\n"
        "\n"
        "请将这些时刻剪辑为 2-5 秒的短镜头 (Short clips)。\n"
        "请严格只输出一个 JSON 数组，格式如下：\n"
        "[\n"
        "  {\"start\": \"HH:MM:SS\", \"duration\": 4, \"description\": \"喂鸡特写\"},\n"
        "  {\"start\": \"00:00:12\", \"duration\": 3, \"description\": \"奔跑动作\"}\n"
        "]"
    )

    try:
        response = client.chat_completion(
             messages=[{"role": "user", "content": prompt}],
             model=model,
             file_paths=[video_path]
        )
        
        if not response or response.status_code != 200:
            print(f"[-] API Error: {response}")
            return []
            
        # Parse Streaming Response
        full_content = ""
        for line in response.iter_lines():
            if not line: continue
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]": break
                try:
                    data = json.loads(data_str)
                    content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content: full_content += content
                except: pass
        
        # Extract JSON
        clean_json = full_content.strip()
        # Remove Markdown wrappers
        match = re.search(r'\[.*\]', clean_json, re.DOTALL)
        if match:
            clean_json = match.group(0)
            
        return json.loads(clean_json)

    except Exception as e:
        print(f"[-] Analysis Failed: {e}")
        return []

# --- 3. 剪映工程生成逻辑 ---
def create_rough_cut_project(video_path, clips):
    if not clips:
        print("[-] No clips found to edit.")
        return

    project_name = f"RoughCut_{os.path.basename(video_path).split('.')[0]}_{len(clips)}clips"
    print(f"[*] Creating JianYing Draft: {project_name}")
    
    jy = JyProject(project_name, overwrite=True)
    
    total_dur = 0
    
    # Track 1: Main Video (Cut)
    # Track 2: Text Description (Subtitle/Marker)
    
    for i, clip in enumerate(clips):
        start_time_str = clip.get('start', "00:00:00")
        dur_sec = clip.get('duration', 3)
        desc = clip.get('description', f"Clip {i+1}")
        
        # Add Video Clip
        # add_clip(path, source_start, duration)
        # source_start needs to be parsed from HH:MM:SS or just passed as is if jy_wrapper supports str
        # pyJianYingDraft supports string "HH:MM:SS" for start times usually, but let's ensure.
        
        print(f"  > Adding Clip {i+1}: {desc} ({start_time_str}, {dur_sec}s)")
        
        # Add Clip to Video Track
        try:
            jy.add_clip(
                media_path=video_path,
                source_start=start_time_str,
                duration=f"{dur_sec}s",
                track_name="MainVideo"
            )
            
            # Add Text Marker (on top)
            # Calculated start time for text is the current total duration
            # But add_text_simple uses auto-append if start_time is None.
            # However, since video track and text track are separate, we need to sync them.
            # JyProject doesn't track global playhead across tracks automatically in simple API?
            # actually add_text_simple(start_time=None) gets track duration of TextTrack.
            # We want to align with VideoTrack. 
            
            # Get current end of video track
            current_end = jy.get_track_duration("MainVideo") - (dur_sec * 1000000)
            
            # Add text at the start of this clip
            jy.add_text_simple(
                text=desc,
                start_time=current_end, # Align with video clip start
                duration=f"{dur_sec}s",
                track_name="Subtitles",
                font_size=6,
                color_rgb=(1.0, 1.0, 1.0), # White
                transform_y=-0.85 # Bottom
            )
            
        except Exception as e:
            print(f"  [!] Failed to add clip: {e}")

    jy.save()
    print(f"[+] Project Saved: {project_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_rough_cut.py <video_path>")
        sys.exit(1)
        
    video_file = sys.argv[1].strip('"')
    
    if not os.path.exists(video_file):
        print(f"File not found: {video_file}")
        sys.exit(1)
        
    # Phase 1
    clips = analyze_video_content(video_file)
    print(f"[*] Found {len(clips)} highlights.")
    print(json.dumps(clips, indent=2, ensure_ascii=False))
    
    # Phase 2
    create_rough_cut_project(video_file, clips)

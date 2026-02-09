import os
import sys
import json
import subprocess
import time
import re

# ==========================================
# 1. 基础配置 (Paths & Config)
# ==========================================
# ==========================================
# 1. 基础配置 (Paths & Config)
# ==========================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 脚本路径探测：期望指向 .agent/skills
# 当前文件在 .agent/skills/jianying-editor/examples/ 下，向上 2 级即为 skills 根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(PROJECT_ROOT))

# 兜底校验：如果没找到 antigravity-api-skill，则尝试从当前工作目录查找
if not os.path.exists(os.path.join(SKILL_ROOT, "antigravity-api-skill")):
    alternative_path = os.path.abspath(".agent/skills")
    if os.path.exists(os.path.join(alternative_path, "antigravity-api-skill")):
        SKILL_ROOT = alternative_path

# 项目根目录 (即 .agent 的上级目录)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(SKILL_ROOT))

CHAT_SCRIPT = os.path.join(SKILL_ROOT, "antigravity-api-skill", "scripts", "chat.py")
MF_SCRIPT = os.path.join(SKILL_ROOT, "antigravity-api-skill", "scripts", "video_analyzer.py")
JY_SCRIPT_DIR = os.path.join(SKILL_ROOT, "jianying-editor", "scripts")


# ==========================================
# 2. 工具函数 (Utilities)
# ==========================================
def safe_decode(bytes_content):
    for enc in ['utf-8', 'gbk', 'utf-16']:
        try: return bytes_content.decode(enc)
        except: continue
    return bytes_content.decode('utf-8', errors='replace')

def parse_srt_time(time_str):
    try:
        parts = time_str.replace(',', '.').split(':')
        if len(parts) == 3:
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
    except: pass
    return 0.0

def parse_srt_content(content):
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    subs = []
    i = 0
    while i < len(lines):
        if lines[i].isdigit() and i+1 < len(lines) and '-->' in lines[i+1]:
            time_line = lines[i+1]
            text_lines, curr = [], i+2
            while curr < len(lines) and not lines[curr].isdigit():
                text_lines.append(lines[curr]); curr += 1
            
            times = time_line.split(' --> ')
            start_str = times[0].strip()
            end_str = times[1].strip() if len(times) > 1 else start_str
            
            start_sec = parse_srt_time(start_str)
            end_sec = parse_srt_time(end_str)
            
            subs.append({
                "index": int(lines[i]),
                "start": start_sec,
                "end": end_sec,
                "duration": end_sec - start_sec,
                "text": " ".join(text_lines).strip()
            })
            i = curr; continue
        i += 1
    return subs

# ==========================================
# 3. 核心流程类 (Workflow Engine)
# ==========================================
class VideoAutoEditor:
    def __init__(self, main_input, material_inputs, project_name, srt_input=None, bg_image=None):
        self.main_input = main_input
        self.material_inputs = material_inputs if isinstance(material_inputs, list) else [material_inputs]
        self.project_name = project_name
        self.srt_input = srt_input
        self.bg_image = bg_image
        
        # 内部临时/缓存路径 (现在指向 WORKSPACE_ROOT)
        self.temp_srt = srt_input if srt_input else os.path.join(WORKSPACE_ROOT, "auto_generated_subs.srt")
        self.analysis_json = os.path.join(WORKSPACE_ROOT, "auto_material_analysis.json")
        self.matches_json = os.path.join(WORKSPACE_ROOT, "auto_ai_matches.json")
        
        if JY_SCRIPT_DIR not in sys.path:
            sys.path.insert(0, JY_SCRIPT_DIR)

    def step1_recognize_subtitles(self):
        # 如果用户提供了 SRT 文件，直接使用
        if self.srt_input and os.path.exists(self.srt_input):
            print(f">>> [Step 1] 使用已有字幕文件: {self.srt_input}")
            self.temp_srt = self.srt_input
            return

        # 如果字幕已经生成在缓存中，跳过
        if os.path.exists(self.temp_srt):
            print(f">>> [Step 1] 跳过：字幕缓存已存在: {self.temp_srt}")
            return
            
        if not self.main_input:
            raise ValueError("未提供主视频/音频，无法生成字幕。请提供 --video 或 --srt 参数。")

        print(f"[Step 1] 正在识别音频中的字幕 (Gemini 3 Flash): {os.path.basename(self.main_input)}...")
        
        # 优化后的提示词：要求精确对齐并去除多余输出
        prompt = (
            "Please transcribe the audio from the file strictly into SRT format. \n"
            "CRITICAL: The timestamps must accurately match the speech in the audio. \n"
            "One sentence per block. Output ONLY the SRT content. No preamble, no markers."
        )
        
        cmd = [sys.executable, CHAT_SCRIPT, prompt, "gemini-3-flash", self.main_input]
        result = subprocess.run(cmd, capture_output=True)
        raw_content = safe_decode(result.stdout)
        
        # 提取真正的 SRT 部分 (寻找数字序号 -> 时间戳 -> 文本的结构)
        srt_match = re.findall(r'(\d+\s+\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}.*?)(?=\d+\s+\d{2}:\d{2}:\d{2},\d{3}|$)', raw_content, re.DOTALL)
        if srt_match:
            srt_content = "\n\n".join([m.strip() for m in srt_match])
        else:
            # 兜底方案：尝试寻找分隔符
            parts = raw_content.split('------------------------------')
            srt_content = parts[1].strip() if len(parts) >= 2 else raw_content.strip()
            
        with open(self.temp_srt, "w", encoding="utf-8") as f: f.write(srt_content)
        print(f"✅ 字幕已生成并清洗: {self.temp_srt}")

    def step2_analyze_materials(self, limit=None):
        print(f"[Step 2] 汇总与分析素材库 (输入源: {len(self.material_inputs)})...")
        
        # 1. 扫描所有输入源获取文件列表
        all_video_paths = []
        for inp in self.material_inputs:
            path = os.path.abspath(inp)
            if os.path.isfile(path):
                if path.lower().endswith(('.mp4', '.mov')):
                    all_video_paths.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if f.lower().endswith(('.mp4', '.mov')) and "数字人" not in f:
                            all_video_paths.append(os.path.join(root, f))
        
        if limit:
            all_video_paths = all_video_paths[:limit]
            
        print(f"    - 共发现 {len(all_video_paths)} 个视频文件。")

        # 2. 加载现有缓存
        existing_results = []
        if os.path.exists(self.analysis_json):
            try:
                with open(self.analysis_json, "r", encoding="utf-8") as f:
                    existing_results = json.load(f)
            except:
                existing_results = []
        
        # 建立索引：以绝对路径作为 Key，防止同名文件冲突
        cache_map = {item.get('path', item.get('filename')): item for item in existing_results}
        
        final_results = []
        from jy_wrapper import draft
        
        for path in all_video_paths:
            filename = os.path.basename(path)
            
            # 检查是否有缓存
            if path in cache_map:
                print(f"    - 跳过已分析素材: {filename}")
                final_results.append(cache_map[path])
                continue

            if not os.path.exists(path):
                print(f"    - 文件未找到: {path}")
                continue
                
            print(f"    - 正在分析新素材: {filename}...")
            # 获取时长
            try:
                dur = draft.VideoMaterial(path).duration / 1000000.0
            except:
                dur = 0
                
            # AI 识别内容
            prompt = "Analyze this cooking clip. Provide a JSON: {'tags': ['keyword1', 'keyword2'], 'desc': 'summary'}. No markdown."
            cmd = [sys.executable, MF_SCRIPT, path, prompt]
            ans = subprocess.run(cmd, capture_output=True)
            try:
                clean_ans = safe_decode(ans.stdout).strip()
                start_idx = clean_ans.find('{')
                end_idx = clean_ans.rfind('}')
                analysis = json.loads(clean_ans[start_idx:end_idx+1])
                
                new_entry = {"filename": filename, "path": path, "duration": dur, "analysis": analysis}
                final_results.append(new_entry)
                
                # 每分析完一个就追加保存
                cache_map[path] = new_entry
                with open(self.analysis_json, "w", encoding="utf-8") as out:
                    json.dump(list(cache_map.values()), out, indent=2, ensure_ascii=False)
                print(f"   ✅ {filename} 分析完成并已存入缓存。")
            except: 
                print(f"   ⚠️ {filename} 分析失败，跳过。")
        
        return final_results

    def step3_ai_match(self, materials_data):
        if os.path.exists(self.matches_json):
            print(f">>> [Step 3] 跳过：AI 语义匹配结果已存在: {self.matches_json}")
            with open(self.matches_json, "r", encoding="utf-8") as f:
                return json.load(f)

        print("[Step 3] 正在让 AI 处理素材与字幕的语义匹配...")
        
        with open(self.temp_srt, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # 准备缩减版的素材信息传给 AI
        materials_summary = []
        for i, m in enumerate(materials_data):
            materials_summary.append({
                "id": i,
                "file": m["filename"],
                "desc": m["analysis"].get("desc", ""),
                "tags": m["analysis"].get("tags", []),
                "dur": m["duration"]
            })
            
        prompt = (
            "You are a professional video editor. Match the best video clips to the provided subtitles.\n"
            "MATERIALS:\n" + json.dumps(materials_summary, ensure_ascii=False) + "\n\n"
            "SUBTITLES (SRT):\n" + srt_content + "\n\n"
            "TASK:\n"
            "1. Analyze the meaning of each subtitle line.\n"
            "2. Select the most appropriate video clip from the list for that specific segment.\n"
            "3. CRITICAL RULE: Each material ID can only be used ONCE throughout the whole video. If you run out of unique materials, leave the remaining subtitles unmatched.\n"
            "4. Return a JSON array of objects. Example: [{\"srt_idx\": 1, \"id\": 0}]\n"
            "5. Output ONLY the JSON array, no explanation."
        )
        
        cmd = [sys.executable, CHAT_SCRIPT, prompt, "gemini-3-flash"]
        ans = subprocess.run(cmd, capture_output=True)
        resp = safe_decode(ans.stdout).strip()
        
        try:
            # 强化 JSON 提取逻辑：获取分隔符之间的内容
            parts = resp.split('------------------------------')
            if len(parts) >= 2:
                # 优先取第 2 部分（通常是流式输出的正文）
                resp = parts[1]
            
            start_idx = resp.find('[')
            end_idx = resp.rfind(']')
            if start_idx == -1 or end_idx == -1:
                raise ValueError("未在 AI 响应中找到 JSON 数组")
            
            clean_resp = resp[start_idx:end_idx+1]
            matches = json.loads(clean_resp)
            
            # 保存匹配结果到缓存
            with open(self.matches_json, "w", encoding="utf-8") as f:
                json.dump(matches, f, indent=2, ensure_ascii=False)
                
            print(f"✅ AI 匹配完成并已保存至缓存，共选定 {len(matches)} 个匹配点。")
            return matches
        except Exception as e:
            print(f"AI 匹配解析失败: {e}\n响应内容摘要: {resp[:200]}...")
            return []

    def step4_assemble_project(self, materials_data, ai_matches):
        print(f"[Step 4] 组装剪辑工程: {self.project_name}...")
        from jy_wrapper import JyProject
        
        # 加载并解析字幕以获取精确时间
        with open(self.temp_srt, 'r', encoding='utf-8') as f:
            subs_list = parse_srt_content(f.read())

        project = JyProject(self.project_name, width=1080, height=1920)
        
        # 1. 判定主输入类型
        is_main_video = False
        if self.main_input and os.path.exists(self.main_input):
            ext = self.main_input.lower().split('.')[-1]
            if ext in ['mp4', 'mov', 'mkv', 'avi']:
                is_main_video = True

        # 2. 确定工程总时长
        total_dur = subs_list[-1]['end'] if subs_list else 10.0
        
        # 3. 处理背景与主轨道逻辑
        # 场景 A: 主输入是视频 -> 视频即是背景，也是主要内容
        if is_main_video:
            print(f"   🎥 添加主视频轨道: {os.path.basename(self.main_input)}")
            project.add_media_safe(self.main_input)
            
            # 如果用户强制指定了其他的 bg_image (非默认颜色)，比如一个叠加层图，可以额外处理
            if self.bg_image and self.bg_image not in ["white", "black"] and os.path.exists(self.bg_image):
                 print(f"   🖼️ 添加叠加层/背景图: {os.path.basename(self.bg_image)}")
                 project.add_media_safe(self.bg_image, duration=f"{total_dur}s", track_name="Background_Layer")
        
        # 场景 B: 主输入是音频 (或无输入) -> 需要填充背景
        else:
            bg_to_use = self.bg_image if self.bg_image else "white"
            bg_val = bg_to_use.lower()
            
            if bg_val == "white":
                print(f"   ⬜ 填充内置纯白背景 (时长: {total_dur}s)")
                project.add_color_strip("#FFFFFF", duration=f"{total_dur}s")
            elif bg_val == "black":
                print(f"   ⬛ 填充内置纯黑背景 (时长: {total_dur}s)")
                project.add_color_strip("#000000", duration=f"{total_dur}s")
            elif os.path.exists(bg_to_use):
                print(f"   🖼️ 填充主背景图: {os.path.basename(bg_to_use)} (时长: {total_dur}s)")
                project.add_media_safe(bg_to_use, duration=f"{total_dur}s")
            else:
                # 兜底：黑色
                project.add_color_strip("#000000", duration=f"{total_dur}s")

            # 添加主音频 (如果是音频文件)
            if self.main_input and os.path.exists(self.main_input):
                 print(f"   🎵 添加主配音轨道: {os.path.basename(self.main_input)}")
                 project.add_media_safe(self.main_input, track_name="Main_Vocal")
        
        project.import_subtitles(self.temp_srt)
        
        # --- 优化点：对匹配结果进行去重，确保每个 srt_idx 只有一个素材 ---
        unique_matches = {}
        for m in ai_matches:
            idx = m.get("srt_idx")
            if idx not in unique_matches:
                unique_matches[idx] = m
        
        added_count = 0
        target_track = "B-Roll_Main" # 统一使用一个主要空镜轨道
        used_materials = set() # 记录已使用的素材 ID
        
        for idx in sorted(unique_matches.keys()):
            match = unique_matches[idx]
            m_id = match.get("id")
            
            # 校验素材是否已被使用
            if m_id in used_materials:
                print(f"    - 跳过重复使用的素材: ID {m_id} (Subtitle {idx})")
                continue

            if 1 <= idx <= len(subs_list) and m_id is not None and 0 <= m_id < len(materials_data):
                sub = subs_list[idx-1]
                m_info = materials_data[m_id]
                path = m_info['path']
                fname = m_info['filename']
                
                start_time = f"{sub['start']}s"
                # 智能时长：取字幕时长和素材时长的最小值
                duration = f"{min(sub['duration'], m_info['duration'])}s"
                
                try:
                    # 优先放在同一个轨道
                    project.add_media_safe(path, start_time=start_time, duration=duration, track_name=target_track)
                    print(f"    [+] [{start_time}] (长 {duration}) 匹配字幕 {idx}: {sub['text'][:10]}... -> {fname}")
                    added_count += 1
                    used_materials.add(m_id) # 标记为已使用
                except Exception as e:
                    # 如果该位置确实有极细微的重叠导致失败，再尝试备用轨道
                    try:
                        project.add_media_safe(path, start_time=start_time, duration=duration, track_name=f"{target_track}_Alt")
                        added_count += 1
                    except:
                        print(f"    [!] 跳过冲突素材: {fname} at {start_time}")

        project.save()
        print(f"DONE: 组装完成! 已精简匹配，共添加 {added_count} 个空镜素材。")

# ==========================================
# 4. 执行入口 (Run)
# ==========================================
# ==========================================
# 4. 执行入口 (CLI)
# ==========================================
import argparse

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频全自动剪辑：自动语音转字幕 -> 智能素材分析 -> 语义画面匹配 -> 导出剪映草稿")
    
    # 核心输入参数 (支持多种组合)
    parser.add_argument("--video", type=str, help="主视频或主音频路径 (用于识别音频并生成字幕)")
    parser.add_argument("--srt", type=str, help="直接提供字幕文件 (跳过 AI 识别步骤)")
    
    # 素材输入：支持多个文件夹或文件
    parser.add_argument("--materials", type=str, nargs="+", required=True, 
                        help="素材来源，可以传入多个文件夹路径或具体视频文件路径")
    
    # 可选参数
    parser.add_argument("--project", type=str, default="AI_Auto_Edit_Project", help="剪映草稿工程名称")
    parser.add_argument("--clear_cache", type=str2bool, default=False, help="是否清除缓存重新分析 (True/False)")
    parser.add_argument("--limit", type=int, default=0, help="限制分析素材的数量 (0 为不限制)")
    parser.add_argument("--bg_image", type=str, default=None, help="音频模式下的背景(支持 white, black 或图片路径)")

    args = parser.parse_args()

    # 路径处理
    main_input = os.path.abspath(args.video) if args.video else None
    srt_input = os.path.abspath(args.srt) if args.srt else None
    material_sources = args.materials
    
    if not main_input and not srt_input:
        parser.error("❌ 必须提供 --video (主视频/音频) 或 --srt (直接提供字幕) 其中的至少一个。")

    if args.clear_cache:
        print("[Cleaning] 清除现有缓存文件...")
        for cache_file in ["auto_material_analysis.json", "auto_ai_matches.json", "auto_generated_subs.srt"]:
            p = os.path.join(WORKSPACE_ROOT, cache_file)
            if os.path.exists(p) and (not srt_input or cache_file != os.path.basename(srt_input)):
                os.remove(p)

    editor = VideoAutoEditor(main_input, material_sources, args.project, srt_input=srt_input, bg_image=args.bg_image)
    
    # 1. 识别字幕 (如果是通过 --srt 传入的会直接跳过)
    editor.step1_recognize_subtitles()
    
    # 2. 分析素材
    limit = args.limit if args.limit > 0 else None
    m_data = editor.step2_analyze_materials(limit=limit)
    
    # 3. AI 匹配
    matches = editor.step3_ai_match(m_data)
    
    # 4. 组装
    editor.step4_assemble_project(m_data, matches)

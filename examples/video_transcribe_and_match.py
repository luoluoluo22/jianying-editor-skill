import os
import sys
import json
import subprocess
import time
import re

# ==========================================
# 1. 基础配置 (Paths & Config)
# ==========================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.join(PROJECT_ROOT, ".agent", "skills")

# 脚本路径
CHAT_SCRIPT = os.path.join(SKILL_ROOT, "antigravity-api-skill", "scripts", "chat.py")
MF_SCRIPT = os.path.join(SKILL_ROOT, "antigravity-api-skill", "scripts", "video_analyzer.py")
JY_SCRIPT_DIR = os.path.join(SKILL_ROOT, "jianying-editor", "scripts")

# 默认关键词映射规则 (可根据需要扩展)
MAPPING_RULES = [
    ("洗干净", "Prep"), ("切碎", "Prep"), ("白菜切完", "Prep"),
    ("放盐", "Mixing"), ("酱油", "Mixing"), ("肉馅", "Mixing"), ("搅拌", "Mixing"),
    ("香油", "Seasoning"), ("调味", "Seasoning"),
    ("爆汁", "Juicy"), ("流油", "Juicy"), ("鲜嫩", "Juicy"),
    ("煮出来", "Cooking"), ("盛入碗中", "Serving"), ("装盘", "Plating"),
    ("家人们", "Showcase"), ("橱窗", "Showcase")
]

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
            start_str = time_line.split(' --> ')[0].strip()
            subs.append({"seconds": parse_srt_time(start_str), "text": " ".join(text_lines).strip()})
            i = curr; continue
        i += 1
    return subs

# ==========================================
# 3. 核心流程类 (Workflow Engine)
# ==========================================
class VideoAutoEditor:
    def __init__(self, main_input, material_inputs, project_name, srt_input=None):
        self.main_input = main_input
        self.material_inputs = material_inputs if isinstance(material_inputs, list) else [material_inputs]
        self.project_name = project_name
        self.srt_input = srt_input
        
        # 内部临时/缓存路径
        self.temp_srt = srt_input if srt_input else os.path.join(PROJECT_ROOT, "auto_generated_subs.srt")
        self.analysis_json = os.path.join(PROJECT_ROOT, "auto_material_analysis.json")
        self.matches_json = os.path.join(PROJECT_ROOT, "auto_ai_matches.json")
        
        if JY_SCRIPT_DIR not in sys.path:
            sys.path.insert(0, JY_SCRIPT_DIR)

    def step1_recognize_subtitles(self):
        # 如果用户提供了 SRT 文件，直接使用
        if self.srt_input and os.path.exists(self.srt_input):
            print(f"⏩ [Step 1] 使用已有字幕文件: {self.srt_input}")
            self.temp_srt = self.srt_input
            return

        # 如果字幕已经生成在缓存中，跳过
        if os.path.exists(self.temp_srt):
            print(f"⏩ [Step 1] 跳过：字幕缓存已存在: {self.temp_srt}")
            return
            
        if not self.main_input:
            raise ValueError("❌ 未提供主视频/音频，无法生成字幕。请提供 --video 或 --srt 参数。")

        print(f"🚀 [Step 1] 正在识别音频中的字幕 (Gemini 3 Flash): {os.path.basename(self.main_input)}...")
        prompt = "Please transcribe the audio from the file strictly into SRT format. One sentence per block. Output ONLY SRT."
        cmd = [sys.executable, CHAT_SCRIPT, prompt, "gemini-3-flash", self.main_input]
        result = subprocess.run(cmd, capture_output=True)
        srt_content = safe_decode(result.stdout)
        
        # 简单校验内容是否为 SRT
        if "-->" not in srt_content:
            print(f"⚠️ [Step 1] AI 响应似乎不是有效的 SRT 格式，请检查音频或 API。内容摘要: {srt_content[:200]}")
            
        with open(self.temp_srt, "w", encoding="utf-8") as f: f.write(srt_content)
        print(f"✅ 字幕已生成: {self.temp_srt}")

    def step2_analyze_materials(self, limit=None):
        print(f"🚀 [Step 2] 汇总与分析素材库 (输入源: {len(self.material_inputs)})...")
        
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
            
        print(f"   🔍 共发现 {len(all_video_paths)} 个视频文件。")

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
                print(f"   ⏩ 跳过已分析素材: {filename}")
                final_results.append(cache_map[path])
                continue

            if not os.path.exists(path):
                print(f"   ⚠️ 文件未找到: {path}")
                continue
                
            print(f"   🔍 正在分析新素材: {filename}...")
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
            print(f"⏩ [Step 3] 跳过：AI 语义匹配结果已存在: {self.matches_json}")
            with open(self.matches_json, "r", encoding="utf-8") as f:
                return json.load(f)

        print("🧠 [Step 3] 正在让 AI 处理素材与字幕的语义匹配...")
        
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
            "3. Try to provide a diverse set of matches (at least 10 matches) across the whole timeline to make the video engaging.\n"
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
            print(f"❌ AI 匹配解析失败: {e}\n响应内容摘要: {resp[:200]}...")
            return []

    def step4_assemble_project(self, materials_data, ai_matches):
        print(f"🚀 [Step 4] 组装剪辑工程: {self.project_name}...")
        from jy_wrapper import JyProject
        
        # 加载并解析字幕以获取精确时间
        with open(self.temp_srt, 'r', encoding='utf-8') as f:
            subs_list = parse_srt_content(f.read())

        project = JyProject(self.project_name, width=1080, height=1920)
        
        has_main_video = False
        # 处理主轨道输入 (视频或音频)
        if self.main_input and os.path.exists(self.main_input):
            ext = self.main_input.lower().split('.')[-1]
            if ext in ['mp4', 'mov', 'mkv', 'avi']:
                print(f"   🎥 检测到主视频，将作为底图轨道")
                project.add_media_safe(self.main_input)
                has_main_video = True
            elif ext in ['mp3', 'wav', 'm4a', 'flac', 'aac']:
                print(f"   🎵 检测到主音频，将作为配音轨道")
                project.add_media_safe(self.main_input, track_name="Main_Vocal")
        
        project.import_subtitles(self.temp_srt)
        
        # 轨道优先级逻辑：
        # 为了避免主轨道的“自动吸附”(Snapping)导致素材无法准确定位到时间点，
        # 我们【统一使用辅轨道】来放置 B-Roll 素材，即便是音频驱动模式也是如此。
        # 辅轨道支持自由定位，不会自动靠拢。
        tracks_to_try = [f"Video_Track_{i}" for i in range(1, 10)]

        added_count = 0
        for match in ai_matches:
            idx = match.get("srt_idx")
            m_id = match.get("id")
            
            if idx is not None and 1 <= idx <= len(subs_list) and m_id is not None and 0 <= m_id < len(materials_data):
                sub = subs_list[idx-1]
                m_info = materials_data[m_id]
                path = m_info['path']
                fname = m_info['filename']
                
                start_time = f"{sub['seconds']}s"
                duration = f"{m_info['duration']}s"
                
                # 寻找第一个不冲突的轨道
                success = False
                for t_name in tracks_to_try:
                    try:
                        project.add_media_safe(path, start_time=start_time, duration=duration, track_name=t_name)
                        track_display = t_name if t_name else "主轨道"
                        print(f"   ➕ [{start_time}] 匹配第 {idx} 条字幕 -> {fname} (填充至: {track_display})")
                        added_count += 1
                        success = True
                        break
                    except Exception:
                        continue
                if not success:
                    print(f"   ⚠️ [{start_time}] {fname} 轨道冲突，未能添加。")

        project.save()
        print(f"✅ 全流程完成! 共添加 {added_count} 个素材片段。")

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

    args = parser.parse_args()

    # 路径处理
    main_input = os.path.abspath(args.video) if args.video else None
    srt_input = os.path.abspath(args.srt) if args.srt else None
    material_sources = args.materials
    
    if not main_input and not srt_input:
        parser.error("❌ 必须提供 --video (主视频/音频) 或 --srt (直接提供字幕) 其中的至少一个。")

    if args.clear_cache:
        print("🗑️ 清除现有缓存文件...")
        for cache_file in ["auto_material_analysis.json", "auto_ai_matches.json", "auto_generated_subs.srt"]:
            p = os.path.join(PROJECT_ROOT, cache_file)
            if os.path.exists(p) and (not srt_input or cache_file != os.path.basename(srt_input)):
                os.remove(p)

    editor = VideoAutoEditor(main_input, material_sources, args.project, srt_input=srt_input)
    
    # 1. 识别字幕 (如果是通过 --srt 传入的会直接跳过)
    editor.step1_recognize_subtitles()
    
    # 2. 分析素材
    limit = args.limit if args.limit > 0 else None
    m_data = editor.step2_analyze_materials(limit=limit)
    
    # 3. AI 匹配
    matches = editor.step3_ai_match(m_data)
    
    # 4. 组装
    editor.step4_assemble_project(m_data, matches)

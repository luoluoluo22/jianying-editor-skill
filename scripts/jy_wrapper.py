
"""
JianYing Editor Skill - High Level Wrapper (Bootstrap)
旨在解决路径依赖、API 复杂度及严格校验问题。
代理应优先使用此 Wrapper 而非直接调用底层库。
"""

import os
import sys
import shutil
import warnings
import argparse
import difflib
import time
import uuid
from typing import Union

# Force UTF-8 output for Windows consoles to support Emojis
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# --- 1. 幽灵依赖解决: 自动注入 references 路径 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(current_dir)
references_path = os.path.join(skill_root, "references")

if os.path.exists(references_path):
    if references_path not in sys.path:
        sys.path.insert(0, references_path)

try:
    import pyJianYingDraft as draft
    from pyJianYingDraft import trange, tim
    from pyJianYingDraft import TextIntro, TextStyle, TextBorder, KeyframeProperty, ClipSettings
    from pyJianYingDraft import VideoSceneEffectType, TransitionType, IntroType, OutroType
except ImportError:
    fallback_path = os.path.join(os.getcwd(), "pyJianYingDraft")
    if os.path.exists(fallback_path):
        sys.path.insert(0, os.getcwd())
        import pyJianYingDraft as draft
        from pyJianYingDraft import trange, tim
        from pyJianYingDraft import TextIntro, TextStyle, TextBorder, KeyframeProperty, ClipSettings
        from pyJianYingDraft import VideoSceneEffectType, TransitionType, IntroType, OutroType
    else:
        print(f"⚠️ Warning: pyJianYingDraft module not found in standard locations.")

# --- 2. 注入录制器 (Internal) ---
try:
    from web_recorder import record_web_animation
    HAS_RECORDER = True
except ImportError:
    HAS_RECORDER = False

# --- 2. 路径自动探测 ---
def get_default_drafts_root() -> str:
    """自动探测剪映草稿目录 (Windows)"""
    local_app_data = os.environ.get('LOCALAPPDATA')
    user_profile = os.environ.get('USERPROFILE')
    
    candidates = []
    if local_app_data:
        candidates.extend([
            os.path.join(local_app_data, r"JianyingPro\User Data\Projects\com.lveditor.draft"),
            os.path.join(local_app_data, r"CapCut\User Data\Projects\com.lveditor.draft")
        ])
    
    if user_profile:
        candidates.append(os.path.join(user_profile, r"AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"))

    # 默认兜底路径 (仅作参考)
    fallback = r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    for path in candidates:
        if os.path.exists(path):
            return path
            
    # 如果都没找到，返回第一个候选路径但打印警告
    if candidates:
        return candidates[0]
    return fallback

def get_all_drafts(root_path: str = None):
    """获取所有草稿并按修改时间排序"""
    root = root_path or get_default_drafts_root()
    drafts = []
    if not os.path.exists(root):
        return []
        
    for item in os.listdir(root):
        path = os.path.join(root, item)
        if os.path.isdir(path):
            # 剪映草稿文件夹通常包含这两个文件之一
            if os.path.exists(os.path.join(path, "draft_content.json")) or \
               os.path.exists(os.path.join(path, "draft_meta_info.json")):
                drafts.append({
                    "name": item,
                    "mtime": os.path.getmtime(path),
                    "path": path
                })
    return sorted(drafts, key=lambda x: x['mtime'], reverse=True)

# --- 3. 辅助函数: 模糊匹配 ---
EFFECT_SYNONYMS = {
    "typewriter": ["打字机", "字幕", "typing", "复古打字机"],
    "fade": ["渐隐", "渐显", "黑场", "白场", "fade_in", "fade_out"],
    "glitch": ["故障", "干扰", "燥波", "雪花"],
    "zoom": ["拉近", "拉远", "缩放", "变焦"],
    "shake": ["振动", "摇晃", "抖动"],
    "blur": ["模糊", "虚化"],
    "glow": ["发光", "辉光", "霓虹"],
    "retro": ["复古", "胶片", "怀旧", "DV"],
    "dissolve": ["叠化", "溶解", "混合"],
}

def _resolve_enum(enum_cls, name: str):
    """
    尝试从 Enum 类中找到匹配的属性。
    1. 精确匹配
    2. 大小写不敏感匹配
    3. 中文同义词查表匹配 (New)
    4. 模糊匹配 (difflib)
    """
    if not name: return None
    
    # 1. Exact
    if hasattr(enum_cls, name):
        return getattr(enum_cls, name)
    
    # 2. Case insensitive map
    name_lower = name.lower()
    mapping = {k.lower(): k for k in enum_cls.__members__.keys()}
    
    if name_lower in mapping:
        real_key = mapping[name_lower]
        return getattr(enum_cls, real_key)

    # 3. Synonym Lookup (中文 -> English Enum Key)
    # 遍历字典，看 name 是否在 values 列表中，或者 values 列表中的词是否在 name 中
    for key, synonyms in EFFECT_SYNONYMS.items():
        key_lower = key.lower()
        if key_lower in mapping: # 确保 Enum 里真有这个 Key
            for syn in synonyms:
                if syn in name_lower or name_lower in syn:
                    real_key = mapping[key_lower]
                    print(f"ℹ️ Synonym Match: '{name}' -> '{real_key}'")
                    return getattr(enum_cls, real_key)
    
    # 4. Fuzzy
    matches = difflib.get_close_matches(name, enum_cls.__members__.keys(), n=1, cutoff=0.6)
    if matches:
        print(f"ℹ️ Fuzzy Match: '{name}' -> '{matches[0]}'")
        return getattr(enum_cls, matches[0])
        
    print(f"⚠️ Warning: Could not find enum memeber for '{name}'.")
    return None

def format_srt_time(us: int) -> str:
    """将微秒转换为 SRT 时间戳格式 (HH:MM:SS,mmm)"""
    ms = (us // 1000) % 1000
    s = (us // 1000000) % 60
    m = (us // 60000000) % 60
    h = (us // 3600000000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# --- 4. High-Level Facade ---

class JyProject:
    """
    高层封装类，提供容错、自动计算和简化的 API。
    """
    
    def __init__(self, project_name: str, width: int = 1920, height: int = 1080, 
                 drafts_root: str = None, overwrite: bool = True):
        self.root = drafts_root or get_default_drafts_root()
        if not os.path.exists(self.root):
            try:
                os.makedirs(self.root)
            except:
                pass
                
        print(f"📂 Project Root: {self.root}")
        
        self.df = draft.DraftFolder(self.root)
        self.name = project_name
        
        # 支持打开现有项目或创建新项目
        has_draft = self.df.has_draft(project_name)
        
        # 损坏检测与自愈 (Self-Healing)
        if has_draft:
            draft_path = os.path.join(self.root, project_name)
            content_path = os.path.join(draft_path, "draft_content.json")
            meta_path = os.path.join(draft_path, "draft_meta_info.json")
            
            # 如果缺少关键文件，视为损坏
            if not os.path.exists(content_path) or not os.path.exists(meta_path):
                print(f"⚠️ Corrupted draft detected (missing json): {project_name}")
                print(f"🧹 Auto-healing: Removing corrupted folder...")
                try:
                    shutil.rmtree(draft_path, ignore_errors=True)
                    has_draft = False
                except Exception as e:
                    print(f"❌ Failed to cleanup corrupted draft: {e}")
                    # 如果删不掉（权限/占用），只能尝试换个名字或者强制覆盖?
                    # 这里如果是 overwrite=True 模式，后面 create_draft 会再次尝试处理
                    pass

        if has_draft and not overwrite:
            print(f"📖 Loading existing project: {project_name}")
            try:
                self.script = self.df.load_template(project_name)
            except Exception as e:
                print(f"❌ Load failed ({e}), forcing recreate...")
                self.script = self.df.create_draft(project_name, width, height, allow_replace=True)
        else:
            print(f"🆕 Creating new project: {project_name}")
            self.script = self.df.create_draft(project_name, width, height, allow_replace=overwrite)

    def save(self):
        """
        保存草稿并执行交付前质检 (Pre-Delivery Checklist)。
        输出详细的 JSON 格式诊断报告，供 Agent 读取。
        """
        import json
        
        # --- 1. Pre-Delivery Checklist (质检) ---
        diagnostics = {
            "validations": [],
            "warnings": [],
            "stats": {}
        }
        
        # 1.1 检查所有媒体路径是否真实存在
        missing_files = []
        if hasattr(self.script, 'materials'):
            media_lists = [self.script.materials.videos, self.script.materials.audios]
            for m_list in media_lists:
                for m in m_list:
                    path = getattr(m, 'path', None)
                    if isinstance(m, dict):
                        path = m.get('path')
                    
                    if path and not os.path.exists(path):
                        missing_files.append(path)
        
        if missing_files:
            diagnostics['validations'].append({"status": "FAIL", "msg": f"Missing media files: {len(missing_files)}", "details": missing_files})
        else:
            diagnostics['validations'].append({"status": "PASS", "msg": "Media paths check"})

        # 1.2 统计轨道信息与音量检查
        total_duration = 0
        audio_tracks_high_vol = 0
        bgm_candidates = []
        
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        
        track_stats = {"video": 0, "audio": 0, "text": 0, "effect": 0}
        
        for t in iterator:
            t_type = getattr(t, 'track_type', None)
            
            # 统计时长
            for seg in t.segments:
                end_time = seg.target_timerange.start + seg.target_timerange.duration
                if end_time > total_duration:
                    total_duration = end_time
            
            # 统计轨道数
            type_map = {
                draft.TrackType.video: "video", draft.TrackType.audio: "audio",
                draft.TrackType.text: "text", draft.TrackType.effect: "effect"
            }
            if t_type in type_map:
                track_stats[type_map[t_type]] += 1
                
            # 检查音频音量 (假设 AudioSegment 有 volume 属性，pyJianYingDraft 目前可能存储在 material 或 extra_material_refs)
            # 由于库的封装复杂，这里做简化检查：如果 Audio Track 数量 > 1，警告需检查混音
            if t_type == draft.TrackType.audio:
                # 简单启发式：如果轨道名包含 BGM 但没显式设置音量 (通常需要手动确认)
                if "BGM" in getattr(t, 'name', '').upper():
                    bgm_candidates.append(getattr(t, 'name', 'Unknown'))

        if len(bgm_candidates) > 0 and track_stats['audio'] > 1:
             diagnostics['warnings'].append("Detected BGM track with other audio tracks. Please ensure BGM volume is lowered (e.g., -10dB).")

        diagnostics['stats']['duration_us'] = total_duration
        diagnostics['stats']['duration_formatted'] = format_srt_time(total_duration).split(',')[0]
        diagnostics['stats']['tracks'] = track_stats

        # --- 2. Save ---
        draft_path = os.path.join(self.root, self.name)
        try:
            self.script.save()
            save_status = "SUCCESS"
            
            # [Enhancement]: 强制更新文件夹修改时间
            if os.path.exists(draft_path):
                os.utime(draft_path, None)
            
            # [Ultimate Fix]: 强制更新剪映全局索引 root_meta_info.json
            duration_us = diagnostics['stats'].get('duration_us', 0)
            self._update_root_meta_info(draft_path, duration_us)
            
        except Exception as e:
            save_status = f"ERROR: {str(e)}"
        
        # --- 3. Output Report ---
        # draft_path 已经在上面定义过了
        
        report = {
            "status": save_status,
            "draft_path": draft_path,
            "draft_name": self.name,
            "diagnostics": diagnostics
        }
        
        print("\n=== JianYing Draft Build Report ===")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        print("===================================\n")

    def _update_root_meta_info(self, draft_path: str, duration_us: int = 0):
        """
        主动将当前项目注入到 root_meta_info.json 中，强制刷新剪映首页列表。
        """
        try:
            root_meta_path = os.path.join(self.root, "root_meta_info.json")
            if not os.path.exists(root_meta_path):
                print(f"⚠️ Root meta not found: {root_meta_path}")
                return

            import json
            import time

            # 读取现有的 root_meta
            with open(root_meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "all_draft_store" not in data:
                data["all_draft_store"] = []

            # 准备当前项目的 meta
            # 我们需要获取项目的 ID (从 draft_meta_info.json 中读取)
            project_meta_path = os.path.join(draft_path, "draft_meta_info.json")
            if not os.path.exists(project_meta_path):
                print(f"⚠️ Project meta not found: {project_meta_path}")
                return
                
            with open(project_meta_path, 'r', encoding='utf-8') as f:
                p_meta = json.load(f)
                
            draft_id = p_meta.get("id", uuid.uuid4().hex.upper())
            current_timestamp = int(time.time() * 1000000) # 微秒
            
            # 路径处理: 剪映似乎喜欢 目录用 / 分隔，但文件名用 \ 分隔 (例如 .../folder\file.json)
            # 为了最大程度兼容，我们先统一转为 / (标准 Unix)，剪映通常也能识别。
            # 如果之前的 Feature_Showcase_V1 能写进去，说明混合写法或者純 / 都可以。
            # 这里统一使用 / (Forward Slash) 是一种安全策略。
            
            d_path_fwd = draft_path.replace("\\", "/")
            d_root_fwd = self.root.replace("\\", "/")
            
            # 构造新的 Entry
            new_entry = {
                "draft_cloud_last_action_download": False,
                "draft_cloud_purchase_info": "",
                "draft_cloud_template_id": "",
                "draft_cloud_tutorial_info": "",
                "draft_cloud_videocut_purchase_info": "",
                "draft_cover": f"{d_path_fwd}/draft_cover.jpg", # 统一用 /
                "draft_fold_path": d_path_fwd,
                "draft_id": draft_id,
                "draft_is_ai_shorts": False,
                "draft_is_invisible": False,
                "draft_json_file": f"{d_path_fwd}/draft_content.json",
                "draft_name": self.name,
                "draft_new_version": "",
                "draft_root_path": d_root_fwd,
                "draft_timeline_materials_size": 0,
                "draft_type": "",
                "tm_draft_cloud_completed": "",
                "tm_draft_cloud_modified": 0,
                "tm_draft_create": current_timestamp,
                "tm_draft_modified": current_timestamp,
                "tm_draft_removed": 0,
                "tm_duration": duration_us
            }

            # 查找并替换（或添加）
            found = False
            for i, entry in enumerate(data["all_draft_store"]):
                if entry.get("draft_fold_path") == new_entry["draft_fold_path"]:
                    # 更新已存在的
                    new_entry["tm_draft_create"] = entry.get("tm_draft_create", current_timestamp)
                    data["all_draft_store"][i].update(new_entry)
                    found = True
                    break
            
            if not found:
                data["all_draft_store"].insert(0, new_entry) # 插入到最前面
            
            # 写入并确保原子操作
            with open(root_meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            
            print(f"🔄 Root Meta Updated: Injected '{self.name}' (Duration: {duration_us/1000000}s) into project list.")

        except Exception as e:
            print(f"⚠️ Failed to update root_meta_info: {e}")

    def add_web_asset_safe(self, html_path: str, start_time: Union[str, int], duration: Union[str, int] = "5s", 
                           track_name: str = "WebVfxTrack", **kwargs):
        """
        [封装核心]: 将一个 HTML 动效文件录制并导入剪映。
        
        Args:
            html_path: HTML 文件的绝对路径。
            start_time: 在时间轴上的起始位置。
            duration: 持续时长。
            track_name: 目标轨道名称。
        """
        if not HAS_RECORDER:
            print("❌ Cannot add web asset: 'web_recorder' module or its dependencies (playwright) are missing.")
            return None

        if not os.path.exists(html_path):
            print(f"❌ HTML file not found: {html_path}")
            return None

        # 1. 生成临时录制路径 (在草稿目录下的 temp 文件夹)
        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        video_output = os.path.join(temp_dir, f"web_vfx_{int(time.time())}.webm")

        # 2. 调用录制流程
        print(f"🎬 Recording web asset: {os.path.basename(html_path)} ...")
        success = record_web_animation(html_path, video_output, max_duration=tim(duration)/1000000 + 5)
        
        if not success:
            print("⚠️ Web recording failed.")
            return None

        # 3. 导入素材 (关键：WebM 必须显式传递 duration)
        print(f"📥 Importing recorded video to jianying...")
        return self.add_media_safe(video_output, start_time, duration, track_name=track_name)

    def add_web_code_vfx(self, html_code: str, start_time: Union[str, int], duration: Union[str, int] = "5s", 
                        track_name: str = "WebVfxTrack", **kwargs):
        """
        [顶级封装]: 直接传入 HTML 代码，自动保存并录制导入。
        Agent 只需生成网页代码，剩下的交给此方法。
        """
        # 自动创建临时 HTML 文件
        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        temp_html_path = os.path.join(temp_dir, f"vfx_{uuid.uuid4().hex[:8]}.html")
        
        # 确保代码中包含基础样式以适配 1080P
        if "margin: 0" not in html_code:
            html_code = html_code.replace("<style>", "<style>body{margin:0;overflow:hidden;background:transparent;}")
            
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_code)
            
        print(f"📝 Generated VFX HTML: {temp_html_path}")
        return self.add_web_asset_safe(temp_html_path, start_time, duration, track_name=track_name)

    def add_media_safe(self, media_path: str, start_time: Union[str, int], duration: Union[str, int] = None, 
                       track_name: str = None, source_start: Union[str, int] = 0, **kwargs):
        """
        自动容错的媒体添加方法 (Auto-Clamp)
        支持视频/图片/音频自动分流。
        """
        if kwargs:
            print(f"⚠️ Warning: Ignored extra args in add_media_safe: {list(kwargs.keys())}")

        if not os.path.exists(media_path):
            print(f"❌ Media Missing: {media_path}")
            return None

        # 简单的后缀判断
        ext = os.path.splitext(media_path)[1].lower()
        if ext in ['.mp3', '.wav', '.aac', '.flac', '.m4a']:
            return self.add_audio_safe(media_path, start_time, duration, track_name or "AudioTrack")
        
        return self._add_video_safe(media_path, start_time, duration, track_name or "VideoTrack", source_start=source_start)

    def add_clip(self, media_path: str, source_start: Union[str, int], duration: Union[str, int], 
                 target_start: Union[str, int] = None, track_name: str = "VideoTrack", **kwargs):
        """
        高层剪辑接口：从媒体指定位置裁剪指定长度，并放入轨道。
        """
        if target_start is None:
            # 自动计算轨道当前末尾时间
            target_start = self.get_track_duration(track_name)
            
        return self.add_media_safe(media_path, target_start, duration, track_name, source_start=source_start, **kwargs)

    def get_track_duration(self, track_name: str) -> int:
        """获取指定轨道当前的总时长（微秒）"""
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        for t in iterator:
            if hasattr(t, 'name') and getattr(t, 'name') == track_name:
                max_end = 0
                for seg in t.segments:
                    end = seg.target_timerange.start + seg.target_timerange.duration
                    if end > max_end: max_end = end
                return max_end
        return 0

    def add_audio_safe(self, media_path: str, start_time: Union[str, int], duration: Union[str, int] = None, 
                       track_name: str = "AudioTrack", **kwargs):
        self._ensure_track(draft.TrackType.audio, track_name)
        
        if kwargs:
            print(f"⚠️ Warning: Ignored extra args in add_audio_safe: {list(kwargs.keys())}")

        try:
            mat = draft.AudioMaterial(media_path)
            phys_duration = mat.duration
        except Exception as e:
            print(f"⚠️ Audio Read Error: {e}")
            return None
            
        start_us = tim(start_time)
        actual_duration = self._calculate_duration(duration, phys_duration)
        
        seg = draft.AudioSegment(
            mat,
            target_timerange=trange(start_us, actual_duration),
            source_timerange=trange(0, actual_duration)
        )
        self.script.add_segment(seg, track_name)
        return seg

    def _add_video_safe(self, media_path: str, start_time: Union[str, int], duration: Union[str, int] = None, 
                        track_name: str = "VideoTrack", source_start: Union[str, int] = 0, **kwargs):
        self._ensure_track(draft.TrackType.video, track_name)
        
        try:
            # 现在这一步是安全的，如果解析失败，会因为我们传了 duration 而 fallback
            # 注意：底层接收的是微秒 (int)，所以需要先转换
            fallback_duration_us = tim(duration) * 10 if duration else None # 10倍冗余
            
            # 这里的 duration 参数是我们刚刚给底层库加上的
            mat = draft.VideoMaterial(media_path, duration=fallback_duration_us)
            
            phys_duration = mat.duration
        except Exception as e:
            print(f"❌ Video Material Init Failed: {e}")
            return None

        start_us = tim(start_time)
        src_start_us = tim(source_start)
        actual_duration = self._calculate_duration(duration, phys_duration - src_start_us)

        seg = draft.VideoSegment(
            mat,
            target_timerange=trange(start_us, actual_duration),
            source_timerange=trange(src_start_us, actual_duration) 
        )
        self.script.add_segment(seg, track_name)
        return seg

    def _calculate_duration(self, req_duration, phys_duration):
        if req_duration is not None:
            req = tim(req_duration)
            if req > phys_duration:
                print(f"⚠️ Auto-Clamp: {req_duration} > physical. Using full length.")
                return phys_duration
            return req
        return phys_duration

    def add_text_simple(self, text: str, start_time, duration, 
                        track_name: str = "TextTrack",
                        font_size: float = 5.0,
                        color_rgb: tuple = (1.0, 1.0, 1.0),
                        bold: bool = False,
                        align: int = 1,
                        auto_wrapping: bool = True,
                        transform_y: float = -0.8,
                        anim_in: str = None,
                        **kwargs):
        """
        极简文本接口 (增强版 V2)
        特点:
        1. 容错: 自动忽略不支持的参数 (如 position) 并打印警告。
        2. 自动分层: 如果轨道上有重叠，自动创建新轨道 (TextTrack_L2, _L3...)。
        """
        # --- 1. 参数清洗与兼容 (Arguments Sanitization) ---
        if kwargs:
            print(f"⚠️ Warning: Ignored unsupported args in add_text_simple: {list(kwargs.keys())}")
            
            # 尝试兼容 position 参数 (假设用户传入的是 (x, y) 归一化坐标, 中心为0)
            if 'position' in kwargs:
                pos = kwargs['position']
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    # 如果这只是别名，我们可以尝试应用它 (这里仅做简单的 Y 轴覆盖)
                    # 假设用户想用 position 控制位置，优先权高于 transform_y
                    # 注意: 剪映坐标系通常 Y向上为正? 还是向下? 
                    # 默认 transform_y=-0.8 是在下方。
                    pass

        self._ensure_track(draft.TrackType.text, track_name)
        
        style = TextStyle(size=font_size, color=color_rgb, bold=bold, align=align, auto_wrapping=auto_wrapping)
        clip = ClipSettings(transform_y=transform_y)
        
        start_us = tim(start_time)
        dur_us = tim(duration)
        
        seg = draft.TextSegment(text, trange(start_us, dur_us), style=style, clip_settings=clip)
        
        if anim_in:
            anim = _resolve_enum(TextIntro, anim_in)
            if anim: seg.add_animation(anim)
        
        # --- 2. 自动分层 (Auto-Layering) ---
        # 尝试添加到指定轨道，如果失败则尝试寻找/创建空闲轨道
        max_retries = 5
        current_track_name = track_name
        
        for i in range(max_retries):
            try:
                self._ensure_track(draft.TrackType.text, current_track_name)
                self.script.add_segment(seg, current_track_name)
                if i > 0:
                    print(f"🛡️ Auto-Layering: Segment overlapping on '{track_name}', moved to '{current_track_name}'")
                return seg
            except Exception as e:
                # 检查是否是重叠错误 (通过错误信息字符串匹配，因为 pyJianYingDraft 可能没有导出特定的 Exception 类)
                err_msg = str(e).lower()
                if "overlap" in err_msg:
                    # 尝试下一层
                    current_track_name = f"{track_name}_L{i+2}"
                    continue
                else:
                    # 其他错误直接抛出
                    print(f"❌ Error adding text: {e}")
                    raise e
                    
        print(f"❌ Failed to add text after {max_retries} layering attempts.")
        return None


    def add_effect_simple(self, effect_name: str, start_time: str, duration: str, track_name: str = "EffectTrack"):
        """添加全局特效 (支持模糊匹配名称)"""
        self._ensure_track(draft.TrackType.effect, track_name)
        
        eff = _resolve_enum(VideoSceneEffectType, effect_name)
        if not eff:
            return None
            
        start_us = tim(start_time)
        dur_us = tim(duration)
        
        try:
            self.script.add_effect(eff, trange(start_us, dur_us), track_name=track_name)
            print(f"✨ Added Effect: {effect_name}")
        except Exception as e:
            print(f"❌ Failed to add effect: {e}")

    def add_transition_simple(self, transition_name: str, duration: str = "0.5s", track_name: str = "VideoTrack"):
        """
        向指定轨道的最后两个片段之间添加转场。
        """
        # 找到对应轨道 (兼容 List/Dict)
        track = None
        tracks = self.script.tracks
        if isinstance(tracks, dict):
            iterator = tracks.values()
        else:
            iterator = tracks if isinstance(tracks, list) else []

        for t in iterator:
            # 兼容性: 检查 type (旧逻辑) 或 track_type (pyJianYingDraft 可能的属性名)
            t_type = getattr(t, 'type', None) or getattr(t, 'track_type', None)
            
            if hasattr(t, 'name') and getattr(t, 'name') == track_name and \
               t_type == draft.TrackType.video:
                track = t
                break
        
        if not track or len(track.segments) < 1:
            print(f"⚠️ Cannot add transition: Track '{track_name}' not found or empty.")
            return

        trans_enum = _resolve_enum(TransitionType, transition_name)
        if not trans_enum: return

        # 这里的逻辑假设最后添加的片段需要转场
        # pyJianYingDraft 的 add_transition 是加在 VideoSegment 对象上的
        # 通常是加在“后面”那个片段上，或者“前面”？ docs says: "注意转场应当添加在**前面的**片段上"??
        # Let's check docs from prev step: "为视频片段添加转场, 注意转场应当添加在**前面的**片段上" -> So add to segment[i] to transition to segment[i+1]??
        # Or add to segment[i] to transition FROM it? 
        # Usually it's attached to the incoming or outgoing. Let's assume we add to the last segment added.
        
        last_seg = track.segments[-1]
        try:
            last_seg.add_transition(trans_enum, duration=duration)
            print(f"🔗 Added Transition: {transition_name}")
        except Exception as e:
            print(f"❌ Failed add transition: {e}")

    def apply_smart_zoom(self, video_segment, events_json_path, zoom_scale=150):
        """
        根据录制轨迹自动应用缩放关键帧
        """
        if video_segment is None:
            print("⚠️ Cannot apply smart zoom: video_segment is None.")
            return

        try:
            import smart_zoomer
            smart_zoomer.apply_smart_zoom(self, video_segment, events_json_path, zoom_scale=zoom_scale)
        except ImportError:
            import json
            if not os.path.exists(events_json_path):
                print(f"❌ Events file not found: {events_json_path}")
                return
            
            with open(events_json_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
            
            # 权重事件：点击和按键都视为有效触发点
            trigger_events = []
            last_x, last_y = 0.5, 0.5 # 默认中心
            for e in events:
                # 持续跟踪最后已知的鼠标位置
                if 'x' in e and 'y' in e:
                    last_x, last_y = e['x'], e['y']
                
                if e['type'] in ['click', 'keypress']:
                    # 为按键事件补充当时已知的坐标，使其也能作为缩放中心
                    if 'x' not in e:
                        e['x'], e['y'] = last_x, last_y
                    trigger_events.append(e)
            
            print(f"🎯 Applying {len(trigger_events)} zoom interest points (Fallback Mode)...")
            from pyJianYingDraft.keyframe import KeyframeProperty as KP

            grouped_events = []
            if trigger_events:
                current_group = [trigger_events[0]]
                for i in range(1, len(trigger_events)):
                    # 判断间隔是否在 3秒内，实现“每输入一次重新更新计时”
                    if (trigger_events[i]['time'] - trigger_events[i-1]['time']) <= 3.0:
                        current_group.append(trigger_events[i])
                    else:
                        grouped_events.append(current_group)
                        current_group = [trigger_events[i]]
                grouped_events.append(current_group)

            scale_val = float(zoom_scale) / 100.0
            ZOOM_IN_US = 300000
            HOLD_US = 3000000
            ZOOM_OUT_US = 600000

            for group in grouped_events:
                # 1. Start
                first = group[0]
                t0 = int(first['time'] * 1000000)
                t_start = max(0, t0 - ZOOM_IN_US)
                
                video_segment.add_keyframe(KP.uniform_scale, t_start, 1.0)
                video_segment.add_keyframe(KP.position_x, t_start, 0.0)
                video_segment.add_keyframe(KP.position_y, t_start, 0.0)

                # 2. Action
                for i, evt in enumerate(group):
                    t_curr = int(evt['time'] * 1000000)
                    tx = (evt['x'] - 0.5) * 2
                    ty = (0.5 - evt['y']) * 2
                    px = -tx * scale_val
                    py = -ty * scale_val

                    if i == 0:
                        video_segment.add_keyframe(KP.uniform_scale, t_curr, scale_val)
                        video_segment.add_keyframe(KP.position_x, t_curr, px)
                        video_segment.add_keyframe(KP.position_y, t_curr, py)
                    else:
                        prev = group[i-1]
                        t_prev = int(prev['time'] * 1000000)
                        prev_tx = (prev['x'] - 0.5) * 2
                        prev_ty = (0.5 - prev['y']) * 2
                        prev_px = -prev_tx * scale_val
                        prev_py = -prev_ty * scale_val

                        if (t_curr - t_prev) > ZOOM_IN_US:
                            t_hold = t_curr - ZOOM_IN_US
                            video_segment.add_keyframe(KP.uniform_scale, t_hold, scale_val)
                            video_segment.add_keyframe(KP.position_x, t_hold, prev_px)
                            video_segment.add_keyframe(KP.position_y, t_hold, prev_py)

                        video_segment.add_keyframe(KP.uniform_scale, t_curr, scale_val)
                        video_segment.add_keyframe(KP.position_x, t_curr, px)
                        video_segment.add_keyframe(KP.position_y, t_curr, py)

                # 2.5 在最后一个动作后立即锁定保持状态
                last_evt = group[-1]
                t_last_action = int(last_evt['time'] * 1000000)
                last_tx = (last_evt['x'] - 0.5) * 2
                last_ty = (0.5 - last_evt['y']) * 2
                lpx_lock = -last_tx * scale_val
                lpy_lock = -last_ty * scale_val
                
                # 在最后动作后 100ms 添加锁定关键帧，确保缩放值被明确固定
                t_lock = t_last_action + 100000  # 100ms
                video_segment.add_keyframe(KP.uniform_scale, t_lock, scale_val)
                video_segment.add_keyframe(KP.position_x, t_lock, lpx_lock)
                video_segment.add_keyframe(KP.position_y, t_lock, lpy_lock)

                # 3. End Phase - 固定保持 3 秒后恢复
                # 简化逻辑：不再受 move 事件影响，直接在最后点击后 3 秒开始恢复
                t_hold_end = t_last_action + HOLD_US  # 3秒 = 3000000微秒

                video_segment.add_keyframe(KP.uniform_scale, t_hold_end, scale_val)
                video_segment.add_keyframe(KP.position_x, t_hold_end, lpx_lock)
                video_segment.add_keyframe(KP.position_y, t_hold_end, lpy_lock)

                t_restore = t_hold_end + ZOOM_OUT_US
                video_segment.add_keyframe(KP.uniform_scale, t_restore, 1.0)
                video_segment.add_keyframe(KP.position_x, t_restore, 0.0)
                video_segment.add_keyframe(KP.position_y, t_restore, 0.0)

    def export_subtitles(self, output_path: str, track_name: str = None):
        """
        导出项目中的字幕为 SRT 格式。
        支持新创建的 TextSegment 和从草稿导入的文本片段。
        """
        import json
        all_segments = []
        
        # 1. 收集所有文本轨道
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        
        # 也要考虑导入的轨道
        imported_tracks = getattr(self.script, 'imported_tracks', [])
        
        all_text_tracks = []
        for t in list(iterator) + list(imported_tracks):
            t_type = getattr(t, 'type', None) or getattr(t, 'track_type', None)
            if t_type == draft.TrackType.text:
                if track_name and getattr(t, 'name', '') != track_name:
                    continue
                all_text_tracks.append(t)
        
        if not all_text_tracks:
            print("⚠️ No text tracks found to export.")
            return False

        # 2. 遍历片段并提取文本
        # 需要查找素材库以获取导入片段的内容
        material_texts = {}
        # 检查新素材
        for mat in self.script.materials.texts:
            material_texts[mat['id']] = mat
        # 检查导入素材
        if hasattr(self.script, 'imported_materials'):
            for mat in self.script.imported_materials.get('texts', []):
                material_texts[mat['id']] = mat

        for track in all_text_tracks:
            for seg in track.segments:
                text_val = ""
                # 情况 A: 新创建的 TextSegment
                if hasattr(seg, 'text'):
                    text_val = seg.text
                # 情况 B: 导入的片段 (ImportedSegment)
                elif hasattr(seg, 'material_id'):
                    mat_id = seg.material_id
                    if mat_id in material_texts:
                        try:
                            content = json.loads(material_texts[mat_id]['content'])
                            text_val = content.get('text', '')
                        except:
                            text_val = "[Complex Text/Bubble]"
                
                if text_val:
                    # 获取时间范围
                    tr = seg.target_timerange
                    all_segments.append({
                        'start': tr.start,
                        'end': tr.start + tr.duration,
                        'text': text_val
                    })

        if not all_segments:
            print("⚠️ No valid subtitles found.")
            return False

        # 3. 按开始时间排序
        all_segments.sort(key=lambda x: x['start'])

        # 4. 写入 SRT
        try:
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                for idx, s in enumerate(all_segments, 1):
                    f.write(f"{idx}\n")
                    f.write(f"{format_srt_time(s['start'])} --> {format_srt_time(s['end'])}\n")
                    f.write(f"{s['text']}\n\n")
            print(f"📝 Subtitles exported to: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to export SRT: {e}")
            return False

    def _ensure_track(self, type, name):
        # 兼容性修复: self.script.tracks 可能是 List[Track] 或 Dict[str, Track]
        tracks = self.script.tracks
        
        # 获取迭代器
        if isinstance(tracks, dict):
            iterator = tracks.values()
        elif isinstance(tracks, list):
            iterator = tracks
        else:
            # Fallback
            iterator = []

        # 遍历查找是否存在同名同类型轨道
        for t in iterator:
            # 防御性检查
            if hasattr(t, 'name') and getattr(t, 'name') == name and \
               hasattr(t, 'track_type') and getattr(t, 'track_type') == type:
                return
        
        # 不存在则创建 (捕获 NameError 以防并发或状态不一致)
        try:
            self.script.add_track(type, name)
        except NameError:
            # 如果底层库抛出 "NameError: 名为 'xxx' 的轨道已存在"，说明轨道其实存在
            # 我们可以安全地忽略这个错误，视为 ensure 成功
            pass

    def add_sticker_at(self, media_path: str, start_time_us: int, duration_us: int):
        """
        在 Overlay 轨道上添加贴纸（图片/视频），位置默认居中 (0,0)。
        这个轨道主要用于放置红点标记等。
        """
        # 1. 确保有一个专门的 Overlay 轨道
        track_name = "OverlayTrack"
        self._ensure_track(draft.TrackType.video, track_name) 
        # 注意: 贴纸本质上也是 video/image 素材，所以放在 video track 上
        # 为了保证它在最上层，应该确保这个 track 在列表的最后面? 
        # pyJianYingDraft 的轨道顺序通常是按添加顺序。
        
        # 2. 读取素材
        try:
            mat = draft.VideoMaterial(media_path)
        except Exception as e:
            print(f"⚠️ Sticker Load Error: {e}")
            return

        # 3. 创建片段
        from pyJianYingDraft import trange
        seg = draft.VideoSegment(
            mat,
            target_timerange=trange(start_time_us, duration_us),
            source_timerange=trange(0, duration_us)
        )
        
        # 4. 显式设置位置为 0,0 (虽然默认为0, 但为了保险)
        from pyJianYingDraft.keyframe import KeyframeProperty as KP
        # 由于我们只希望它是静态的显示在中心，不需要 Keyframe，直接设属性即可?
        # pyJianYingDraft 的 segment 可能没有直接 set pos 的方法，得加关键帧或者.. 
        # 暂时加一个关键帧锁住位置
        seg.add_keyframe(KP.position_x, start_time_us, 0.0)
        seg.add_keyframe(KP.position_y, start_time_us, 0.0)
        seg.add_keyframe(KP.uniform_scale, start_time_us, 1.0) # 原始大小

        self.script.add_segment(seg, track_name)

    def import_subtitles(self, srt_path: str, track_name: str = "TextTrack"):
        """
        从 SRT 文件导入字幕到项目中。
        """
        if not os.path.exists(srt_path):
            print(f"❌ SRT file not found: {srt_path}")
            return False

        try:
            import re
            with open(srt_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # 简单的 SRT 解析正则 (匹配序号、时间轴、文本内容)
            pattern = re.compile(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n?)+?)(?=\n\d+\n|\n?$)', re.MULTILINE)
            matches = pattern.findall(content)

            if not matches:
                # 尝试另一种常见的换行符兼容正则
                pattern = re.compile(r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+((?:.+[\r\n]?)+?)(?=[\r\n]+\d+[\r\n]+|[\r\n]?$)', re.MULTILINE)
                matches = pattern.findall(content)

            def srt_to_us(srt_time: str) -> int:
                h, m, s_ms = srt_time.split(':')
                s, ms = s_ms.split(',')
                return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000000 + int(ms) * 1000

            count = 0
            for _, start_str, end_str, text in matches:
                start_us = srt_to_us(start_str.strip())
                end_us = srt_to_us(end_str.strip())
                duration_us = end_us - start_us
                
                clean_text = text.strip()
                if clean_text:
                    self.add_text_simple(clean_text, start_us, duration_us, track_name=track_name)
                    count += 1
            
            print(f"✅ Imported {count} subtitle segments from {srt_path} to track '{track_name}'")
            return True
        except Exception as e:
            print(f"❌ Failed to import SRT: {e}")
            import traceback
            traceback.print_exc()
            return False

    def clear_text_tracks(self, track_name: str = None):
        """
        清除项目中的文本轨道。
        """
        if hasattr(self.script, 'tracks'):
            original_tracks = self.script.tracks
            if isinstance(original_tracks, list):
                self.script.tracks = [t for t in original_tracks if not (getattr(t, 'track_type', None) == draft.TrackType.text and (not track_name or getattr(t, 'name', '') == track_name))]
            elif isinstance(original_tracks, dict):
                keys_to_del = [k for k, t in original_tracks.items() if getattr(t, 'track_type', None) == draft.TrackType.text and (not track_name or getattr(t, 'name', '') == track_name)]
                for k in keys_to_del: del original_tracks[k]


# --- 5. CLI Controller ---

def cli():
    parser = argparse.ArgumentParser(description="Antigravity JianYing (CapCut) Skill CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Command: check
    subparsers.add_parser("check", help="Run diagnostics on environment")
    
    # Command: list-assets (原 list)
    list_assets_parser = subparsers.add_parser("list-assets", help="List available assets (effects, transitions, etc.)")
    list_assets_parser.add_argument("--type", choices=["anim", "effect", "trans"], default="anim")
    
    # Command: list-drafts (新)
    subparsers.add_parser("list-drafts", help="List user video drafts from JianYing")

    # Command: export-srt (新)
    export_parser = subparsers.add_parser("export-srt", help="Export subtitles from a draft to SRT file")
    export_parser.add_argument("--name", required=True, help="Draft Project Name")
    export_parser.add_argument("--output", help="Output SRT path (default: project_name.srt)")

    # Command: import-srt (新)
    import_parser = subparsers.add_parser("import-srt", help="Import subtitles from SRT file to a draft")
    import_parser.add_argument("--name", required=True, help="Draft Project Name")
    import_parser.add_argument("--srt", required=True, help="Input SRT path")
    import_parser.add_argument("--track", default="TextTrack", help="Target text track name")
    import_parser.add_argument("--clear", action="store_true", help="Clear existing text tracks before importing")

    # Command: create (Simple)
    create_parser = subparsers.add_parser("create", help="Quickly create a simple video draft")
    create_parser.add_argument("--name", required=True, help="Project Name")
    create_parser.add_argument("--media", required=True, help="Path to video/image")
    create_parser.add_argument("--text", help="Overlay text")
    
    # Command: apply-zoom (新)
    zoom_parser = subparsers.add_parser("apply-zoom", help="Apply smart zoom to a video based on events.json")
    zoom_parser.add_argument("--name", required=True, help="Draft Project Name")
    zoom_parser.add_argument("--video", required=True, help="Video file path used in project")
    zoom_parser.add_argument("--json", required=True, help="Events JSON path")
    zoom_parser.add_argument("--scale", type=int, default=150, help="Zoom scale percentage")
    
    args = parser.parse_args()
    
    if args.command == "check":
        root = get_default_drafts_root()
        if os.path.exists(root):
            print(f"✅ Environment Ready. Drafts Path: {root}")
            try:
                import uiautomation
                print("✅ Dependencies: uiautomation found.")
            except:
                print("⚠️ Warning: uiautomation not installed (Auto-export will fail).")
        else:
            print(f"❌ Drafts folder not found at: {root}")
            
    elif args.command == "list-assets":
        # Simple listing, refer to md for details
        print("Please check '.agent/skills/jianying-editor/references/AVAILABLE_ASSETS.md' for full list.")
        
    elif args.command == "list-drafts":
        root = get_default_drafts_root()
        drafts = get_all_drafts(root)
        if not drafts:
            print(f"📭 No drafts found in: {root}")
        else:
            print(f"📂 Found {len(drafts)} drafts in: {root}")
            import time
            for d in drafts:
                t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d['mtime']))
                print(f" - {d['name']} (Last Modified: {t_str})")

    elif args.command == "export-srt":
        p = JyProject(args.name)
        # 默认输出到当前运行目录 (项目根目录)
        if args.output:
            output = args.output
        else:
            output = os.path.join(os.getcwd(), f"{args.name}.srt")
        p.export_subtitles(output)

    elif args.command == "import-srt":
        p = JyProject(args.name)
        if args.clear:
            p.clear_text_tracks(args.track)
        p.import_subtitles(args.srt, track_name=args.track)
        p.save()

    elif args.command == "create":
        p = JyProject(args.name)
        p.add_media_safe(args.media, "0s")
        if args.text:
            p.add_text_simple(args.text, "0s", "3s")
        p.save()

    elif args.command == "apply-zoom":
        p = JyProject(args.name)
        # 查找或添加视频
        seg = p.add_media_safe(args.video, "0s")
        if seg:
            p.apply_smart_zoom(seg, args.json, zoom_scale=args.scale)
        else:
            print(f"❌ Failed to load video: {args.video}")
        p.save()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        print("JyWrapper Library Loaded. Import `JyProject` to use.")

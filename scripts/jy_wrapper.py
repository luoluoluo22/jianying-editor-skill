
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
import subprocess
from typing import Union, Optional

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

    # 3. Synonym Lookup (双向映射: 中文<->英文)
    # 情况A: 输入的是中文同义词 (如 "打字机") -> 找英文 Key (如果有) 或者其他中文标准名
    # 情况B: 输入的是英文 Key (如 "typewriter") -> 找 Enum 里实际存在的中文属性名 (如 "复古打字机")
    
    for key, synonyms in EFFECT_SYNONYMS.items():
        # 检查是否命中字典的 Key (英文)
        if name_lower == key.lower():
            # 尝试在 synonyms 列表里找到一个在 Enum 里存在的词
            for candidate in synonyms:
                if candidate in mapping: # Enum 里有 "复古打字机"
                    real_key = mapping[candidate]
                    print(f"ℹ️ Map EN->CN: '{name}' -> '{real_key}'")
                    return getattr(enum_cls, real_key)
        
        # 检查是否命中字典的 Value (中文同义词)
        # 如果 Enum 里真的有英文 Key (design by normal people)，那走这里
        if key.lower() in mapping:
            for syn in synonyms:
                if syn in name_lower or name_lower in syn:
                    real_key = mapping[key.lower()]
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

# --- 4. 复合片段辅助类 (Internal) ---
class MockVideoMaterial(draft.VideoMaterial):
    """绕过底层库物理文件检测的伪视频素材类"""
    def __init__(self, material_id, duration, name, width=1920, height=1080):
        # 绕过父类 __init__ 的物理文件检测，直接手动赋值
        self.material_id = material_id
        self.duration = duration
        self.material_name = name
        self.width = width
        self.height = height
        self.path = ""
        self.material_type = "video"
        self.local_material_id = ""
        self.crop_settings = draft.CropSettings()

    def export_json(self):
        return {
            "id": self.material_id,
            "type": "video",
            "material_name": self.material_name,
            "path": "",
            "extra_type_option": 2, # 复合片段核心标识
            "duration": self.duration,
            "height": self.height,
            "width": self.width,
            "category_id": "",
            "category_name": "local",
            "check_flag": 63487,
            "local_material_id": ""
        }

class MockAudioMaterial(draft.AudioMaterial):
    """绕过底层库物理文件检测的伪音频素材类"""
    def __init__(self, material_id, duration, name, path):
        self.material_id = material_id
        self.duration = duration
        self.name = name
        self.path = path
        self.material_type = "audio"
        self.local_material_id = ""

    def export_json(self):
        return {
            "app_id": 1775,
            "category_id": "6678556627852856076",
            "category_name": "推荐音乐",
            "check_flag": 1,
            "copyright_limit_type": "none",
            "duration": self.duration,
            "effect_id": "",
            "formula_id": "",
            "id": self.material_id,
            "intensifies_path": "",
            "is_ugc": False,
            "local_material_id": "",
            "music_id": self.material_id,
            "name": self.name,
            "path": self.path,
            "source_platform": 0,
            "type": "music",
            "wave_points": []
        }

class CompoundSegment(draft.VideoSegment):
    """自定义复合片段 Segment，完全解耦 MediaInfo 检测"""
    def __init__(self, mock_material, draft_id, duration, start_us=0):
        # 绕过父类初始化以规避路径检测逻辑
        self.material_instance = mock_material
        self.target_timerange = draft.Timerange(start_us, duration)
        self.source_timerange = draft.Timerange(0, duration)
        self.draft_id = draft_id
        self.duration_val = duration
        
        # 兼容基类必要属性
        self.segment_id = uuid.uuid4().hex.upper()
        self.material_id = mock_material.material_id
        self.common_keyframes = []
        self.render_index = 0
        self.visible = True
        self.volume = 1.0
        self.speed = None # 复合片段不直接由底层库处理变速
        self.clip_settings = draft.ClipSettings()
        self.animations_instance = None
        self.fade = None
        self.effects = []
        self.filters = []
        self.mask = None
        self.background_filling = None
        self.transition = None
        self.extra_material_refs = []

    def export_json(self):
        # 纯手工构建符合嵌套协议的 JSON
        return {
            "id": self.segment_id,
            "material_id": self.material_id,
            "extra_material_refs": [self.draft_id],
            "target_timerange": self.target_timerange.export_json(),
            "source_timerange": {"start": 0, "duration": self.duration_val},
            "render_index": 0,
            "visible": True,
            "volume": 1.0,
            "speed": 1.0,
            "track_attribute": 0,
            "extra_type_option": 0,
            "clip": self.clip_settings.export_json(),
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_correct_adjust": False,
            "enable_color_curves": True,
            "enable_color_match_adjust": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0},
            "uniform_scale": {"on": True, "value": 1.0},
            "keyframe_refs": []
        }
    
    def overlaps(self, other):
        # 如果不是标准 Segment 类型，简单返回 False 或执行基础判断
        if not hasattr(other, 'target_timerange'): return False
        return self.target_timerange.overlaps(other.target_timerange)

def safe_tim(inp: Union[str, int, float]) -> int:
    """
    增强版时间解析器，支持:
    1. 1h2m3s (底层库自带)
    2. 00:00:10 (冒号分隔格式)
    3. 10 (纯数字)
    """
    if isinstance(inp, (int, float)):
        return int(inp * 1000000) if inp < 1000000 else int(inp)

    if isinstance(inp, str) and ":" in inp:
        try:
            parts = inp.split(":")
            if len(parts) == 3: # HH:MM:SS
                h, m, s = map(float, parts)
                return int((h * 3600 + m * 60 + s) * 1000000)
            elif len(parts) == 2: # MM:SS
                m, s = map(float, parts)
                return int((m * 60 + s) * 1000000)
        except:
            pass

    # 回退到原始 tim 函数
    return tim(inp)

# --- 5. High-Level Facade ---

class JyProject:
    """
    高层封装类，提供容错、自动计算和简化的 API。
    """
    
    def __init__(self, project_name: str, width: int = 1920, height: int = 1080, 
                 drafts_root: str = None, overwrite: bool = True, script_instance: any = None):
        self.root = drafts_root or get_default_drafts_root()
        if not os.path.exists(self.root):
            try:
                os.makedirs(self.root)
            except:
                pass
                
        print(f"📂 Project Root: {self.root}")
        
        self.df = draft.DraftFolder(self.root)
        self.name = project_name
        self.draft_dir = os.path.join(self.root, self.name)
        self._internal_colors = [] # 新增：用于追踪内部生成的色块
        self._cloud_audio_patches = {} # 新增：用于追踪云端音频映射 {dummy_path: {"id": id, "type": "music"|"sfx"}}
        self._cloud_text_patches = {}   # 新增：用于追踪花字样式映射 {material_id: style_id}
        
        # 是否显式指定了分辨率 (如果用户传入的不是默认值，则视为显式指定)
        self._explicit_res = (width != 1920 or height != 1080)
        self._first_video_resolved = False

        # 如果提供了脚本实例（克隆模式），直接绑定
        if script_instance:
            self.script = script_instance
            self._explicit_res = True # 克隆通常不改变比例
            return

        # 支持打开现有项目或创建新项目
        has_draft = self.df.has_draft(project_name)
        
        # 损坏检测与自愈 (Self-Healing)
        if has_draft:
            draft_path = os.path.join(self.root, project_name)
            content_path = os.path.join(draft_path, "draft_content.json")
            meta_path = os.path.join(draft_path, "draft_meta_info.json")
            
            # 如果缺少关键文件，视为损坏 (仅在 overwrite 模式下自动修复)
            if not os.path.exists(content_path) or not os.path.exists(meta_path):
                if overwrite:
                    print(f"Corrupted draft detected (missing json): {project_name}")
                    print(f"Auto-healing: Removing corrupted folder...")
                    try:
                        shutil.rmtree(draft_path, ignore_errors=True)
                        has_draft = False
                    except Exception as e:
                        print(f"Failed to cleanup corrupted draft: {e}")
                        pass
                else:
                    print(f"Corrupted draft detected: {project_name} (missing json). Use overwrite=True to auto-fix.")

        if has_draft and not overwrite:
            print(f"Loading existing project: {project_name}")
            try:
                self.script = self.df.load_template(project_name)
            except Exception as e:
                print(f"Load failed ({e}), forcing recreate...")
                self.script = self.df.create_draft(project_name, width, height, allow_replace=True)
        else:
            print(f"Creating new project: {project_name}")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.script = self.df.create_draft(project_name, width, height, allow_replace=overwrite)
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"\n{'='*50}")
                        print(f"  [!] 剪映正在占用项目 '{project_name}' 的文件。")
                        print(f"  请在剪映中关闭该草稿的编辑界面,")
                        print(f"  然后返回剪映首页。(将在 5 秒后重试...)")
                        print(f"{'='*50}\n")
                        time.sleep(5)
                    else:
                        print(f"\n  剪映仍在占用文件，请先手动关闭剪映中的草稿后再重新运行脚本。")
                        raise

    @staticmethod
    def from_template(template_name: str, new_project_name: str, drafts_root: str = None):
        """
        [克隆模式]: 基于现有模板创建一个全新的项目副本。
        防止直接在模板上修改导致的“模板损坏”问题。
        """
        root = drafts_root or get_default_drafts_root()
        df = draft.DraftFolder(root)
        
        if not df.has_draft(template_name):
            raise FileNotFoundError(f"Template '{template_name}' not found.")
            
        print(f"🚀 Cloning template '{template_name}' -> '{new_project_name}'")
        # 使用底层库的 duplicate_as_template 功能实现物理拷贝
        script = df.duplicate_as_template(template_name, new_project_name, allow_replace=True)
        
        # 返回映射后的 JyProject 实例
        return JyProject(new_project_name, drafts_root=root, script_instance=script)

    @staticmethod
    def import_external_draft(external_path: str, new_name: str = None, drafts_root: str = None, overwrite: bool = True):
        """
        [智能物理导入]: 将外部工程文件夹导入剪映工作区。
        支持智能探测：如果 external_path 下没有 draft_content.json，会自动向下搜索子目录。
        """
        if not os.path.exists(external_path):
            raise FileNotFoundError(f"External path not found: {external_path}")

        # --- 智能探测真正的草稿根目录 ---
        real_source = None
        if os.path.exists(os.path.join(external_path, "draft_content.json")):
            real_source = external_path
        else:
            print(f"🔍 '{external_path}' is not a direct draft folder. Searching sub-directories...")
            for root, dirs, files in os.walk(external_path):
                if "draft_content.json" in files:
                    real_source = root
                    print(f"✨ Found real draft at: {real_source}")
                    break
        
        if not real_source:
            raise FileNotFoundError(f"No valid JianYing draft (draft_content.json) found under: {external_path}")
            
        target_root = drafts_root or get_default_drafts_root()
        original_name = os.path.basename(real_source.rstrip(os.path.sep))
        project_name = new_name or original_name
        
        target_path = os.path.join(target_root, project_name)
        
        if os.path.abspath(real_source) == os.path.abspath(target_path):
            print(f"ℹ️ Project already in workdir: {project_name}")
            return JyProject(project_name, drafts_root=target_root)

        print(f"🚚 Importing real draft: '{real_source}' -> '{target_path}'")
        
        if os.path.exists(target_path):
            if overwrite:
                try:
                    shutil.rmtree(target_path)
                except PermissionError:
                    print(f"\n  [!] 剪映正在占用项目 '{project_name}'，请先关闭剪映中的草稿。")
                    raise
            else:
                raise FileExistsError(f"Project '{project_name}' already exists.")
        
        # 执行物理拷贝 (仅拷贝真实的草稿根目录)
        shutil.copytree(real_source, target_path)
        
        # 显式指定 overwrite=False 以加载刚刚导入的内容，防止被清空
        return JyProject(project_name, drafts_root=target_root, overwrite=False)

    def get_missing_assets(self):
        """
        [深度诊断]: 返回工程中所有丢失素材的详细清单（含原始路径）。
        """
        missing_map = {} # path -> name
        
        # 探测所有可能的素材来源
        materials = []
        if hasattr(self.script, 'materials'):
            materials.extend(getattr(self.script.materials, 'videos', []))
            materials.extend(getattr(self.script.materials, 'audios', []))
        
        if hasattr(self.script, 'imported_materials'):
            materials.extend(self.script.imported_materials.get('videos', []))
            materials.extend(self.script.imported_materials.get('audios', []))
            materials.extend(self.script.imported_materials.get('images', []))

        for m in materials:
            path = getattr(m, 'path', '') if not isinstance(m, dict) else m.get('path', '')
            if path and not os.path.exists(path):
                missing_map[path] = os.path.basename(path)
        
        # 转换为结构化列表输出
        result = []
        for path, name in missing_map.items():
            result.append({
                "name": name,
                "orig_path": path
            })
        
        return sorted(result, key=lambda x: x['name'])

    def save(self):
        """
        保存草稿并执行深度质检 (Deep Quality Check)。
        输出完整的 JSON 报告，包含轨道详情、素材映射和时序分析。
        """
        import json
        
        # --- 1. 获取基础统计与片段明细 ---
        total_duration = 0
        track_details = []
        missing_count = 0
        
        # 建立素材快速查找表
        mat_lookup = {}
        if hasattr(self.script, 'materials'):
            for m in (self.script.materials.videos + self.script.materials.audios):
                mat_lookup[m.material_id] = getattr(m, 'path', '')
        
        # 深度扫描轨道
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        # 兼容 imported_tracks
        imported_tracks = getattr(self.script, 'imported_tracks', [])
        
        all_tracks_to_scan = list(iterator) + list(imported_tracks)
        track_stats = {"video": 0, "audio": 0, "text": 0, "effect": 0}
        
        for i, t in enumerate(all_tracks_to_scan):
            t_type = getattr(t, 'track_type', None)
            t_name = getattr(t, 'name', f"Track_{i}")
            
            # 统计类型
            type_map = {
                draft.TrackType.video: "video", draft.TrackType.audio: "audio",
                draft.TrackType.text: "text", draft.TrackType.effect: "effect"
            }
            if t_type in type_map: track_stats[type_map[t_type]] += 1
            
            segments_info = []
            for seg in t.segments:
                d_start = seg.target_timerange.start
                d_dur = seg.target_timerange.duration
                d_end = d_start + d_dur
                if d_end > total_duration: total_duration = d_end
                
                # 获取素材路径
                final_path = ""
                if hasattr(seg, 'material_instance'):
                    final_path = getattr(seg.material_instance, 'path', '')
                elif hasattr(seg, 'material_id'):
                    mid = seg.material_id
                    # 查表或从 imported_materials 查找
                    final_path = mat_lookup.get(mid, "")
                    if not final_path and hasattr(self.script, 'imported_materials'):
                        for im in self.script.imported_materials.get('videos', []) + self.script.imported_materials.get('audios', []):
                            if im['id'] == mid:
                                final_path = im.get('path', '')
                                break

                # 检查缺失
                is_missing = False
                if final_path and not os.path.exists(final_path):
                    missing_count += 1
                    is_missing = True

                # 深度解析：片段绑定的视觉特效 (VFX)
                vfx_list = []
                # 1. 片段内绑定的滤镜/特效
                if hasattr(seg, 'filters') and seg.filters:
                    for f in seg.filters: vfx_list.append({"type": "filter", "name": getattr(f, 'name', 'Filter')})
                if hasattr(seg, 'effects') and seg.effects:
                    for e in seg.effects: vfx_list.append({"type": "effect", "name": getattr(e, 'name', 'Effect')})
                
                # 2. 转场 (Transition) - 通常附在片段尾部
                if getattr(seg, 'transition', None):
                    vfx_list.append({
                        "type": "transition", 
                        "name": getattr(seg.transition, 'name', 'Transition'),
                        "duration": f"{getattr(seg.transition, 'duration', 0)/1000000:.2f}s"
                    })

                # 3. 如果片段本身就是特效/滤镜轨道上的“独立片段”
                if not vfx_list:
                    # 尝试从 material_instance 里的名字恢复
                    if hasattr(seg, 'effect_inst'): # EffectSegment
                         vfx_list.append({"type": "scene_effect", "name": getattr(seg.effect_inst, 'name', 'Scene Effect')})
                    elif hasattr(seg, 'material') and hasattr(seg, 'meta'): # FilterSegment
                         vfx_list.append({"type": "global_filter", "name": getattr(seg.material, 'name', 'Global Filter')})

                segments_info.append({
                    "name": getattr(seg, 'name', os.path.basename(final_path) if final_path else (vfx_list[0]['name'] if vfx_list else "Untitled")),
                    "start": f"{d_start/1000000:.2f}s",
                    "duration": f"{d_dur/1000000:.2f}s",
                    "src_start_us": seg.source_timerange.start if getattr(seg, 'source_timerange', None) else 0,
                    "path": final_path,
                    "status": "MISSING" if is_missing else "OK",
                    "vfx": vfx_list # 新增 VFX 字段
                })
            
            track_details.append({
                "track_index": i,
                "type": str(t_type).split('.')[-1] if t_type else "unknown",
                "name": t_name,
                "segments_count": len(segments_info),
                "segments": segments_info
            })

        # --- 2. 构造诊断报告 ---
        diagnostics = {
            "validations": [],
            "warnings": [],
            "stats": {
                "duration_us": total_duration,
                "duration_formatted": format_srt_time(total_duration).split(',')[0],
                "tracks_summary": track_stats,
                "total_missing_files": missing_count
            },
            "timeline_overview": track_details
        }
        
        if missing_count > 0:
            diagnostics['validations'].append({"status": "FAIL", "msg": f"Missing {missing_count} media files"})
        else:
            diagnostics['validations'].append({"status": "PASS", "msg": "All media files verified"})

        # --- 3. 执行保存逻辑 ---
        draft_path = os.path.join(self.root, self.name)
        try:
            self.script.save()
            # 自动针对云端库进行协议补丁 (含 Music, SFX, 花字)
            self._patch_cloud_material_ids()
            # 自动注入激活补丁，解决亮度/曝光等参数不即时生效的问题
            self._force_activate_adjustments()
            save_status = "SUCCESS"
            if os.path.exists(draft_path):
                os.utime(draft_path, None)
            self._update_root_meta_info(draft_path, total_duration)
        except Exception as e:
            save_status = f"ERROR: {str(e)}"
        
        report = {
            "status": save_status,
            "draft_name": self.name,
            "draft_path": draft_path,
            "report_summary": {
                "total_duration": diagnostics['stats']['duration_formatted'],
                "tracks_count": sum(track_stats.values()),
                "missing_files": missing_count
            },
            "full_timeline": track_details  # AI 重点关注的字段
        }
        # 之前这里会打印完整的 JSON，在 Windows 控制台下容易导致编码冲突崩溃
        # 现在改为静默生成，只在看板前端展示
        print(f"✅ Report generated successfully: {report['report_summary']['missing_files']} files missing.")
        
        self.audit_timeline(track_details)
        
        return report

    def audit_timeline(self, track_details):
        """
        [健康检查]: 审计时间轴并打印可能的高频重复片段异常警告。
        """
        issues_found = False
        # 记录特定起始时间截取的频次
        mat_start_counts = {}
        for td in track_details:
            if td['type'] == 'video' or td['type'] == 'audio':
                for seg in td['segments']:
                    path = seg.get('path', '')
                    src_start = seg.get('src_start_us', 0)
                    if path:
                        key = f"{path}@{src_start}"
                        mat_start_counts[key] = mat_start_counts.get(key, 0) + 1

        for key, count in mat_start_counts.items():
            if count > 5:  # 假设超过5次相同源起点复用可能有问题
                issues_found = True
                path, start_us = key.rsplit('@', 1)
                start_sec = int(start_us) / 1000000
                print(f"⚠️ [AUDIT WARNING] 检测到高频率重复片段！文件: '{os.path.basename(path)}' 被从起点 {start_sec}s 截取了 {count} 次。")
                print(f"  -> 请检查素材时长解析是否正确，是否存在静默归零或异常缩放到起点。")

        if issues_found:
            print("❗️ Timeline Audit highlighted potential duplication issues. Review the logs above.")

    def _force_activate_adjustments(self):
        """
        [协议级补丁]: 强行注入影子材质和引用链。
        解决代码注入亮度、对比度等关键帧后，剪映渲染引擎不激活的问题。
        """
        import json
        import uuid

        content_path = os.path.join(self.root, self.name, "draft_content.json")
        if not os.path.exists(content_path): return

        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            has_modified = False
            materials = data.setdefault("materials", {})
            all_effects = materials.setdefault("effects", [])
            video_effects = materials.setdefault("video_effects", [])

            PROP_MAP = {
                "KFTypeBrightness": "brightness",
                "KFTypeContrast": "contrast",
                "KFTypeSaturation": "saturation"
            }
            # 适配当前版本的路径
            jy_res_path = "C:/Program Files/JianyingPro/5.9.0.11632/Resources/DefaultAdjustBundle/combine_adjust"

            for track in data.get("tracks", []):
                for seg in track.get("segments", []):
                    kfs = seg.get("common_keyframes", [])
                    active_props = [kf.get("property_type") for kf in kfs if kf.get("property_type") in PROP_MAP]

                    if active_props:
                        seg["enable_adjust"] = True
                        seg["enable_color_correct_adjust"] = True
                        refs = seg.setdefault("extra_material_refs", [])

                        for prop in active_props:
                            mat_type = PROP_MAP[prop]
                            if not any(m.get("type") == mat_type and m["id"] in refs for m in all_effects):
                                new_id = str(uuid.uuid4()).upper()
                                shadow_mat = {
                                    "type": mat_type, "value": 0.0, "path": jy_res_path, "id": new_id,
                                    "apply_target_type": 0, "platform": "all", "source_platform": 0, "version": "v2"
                                }
                                all_effects.append(shadow_mat)
                                refs.append(new_id)
                                has_modified = True

                        if not any(m.get("type") == "video_effect" and m["id"] in refs for m in video_effects):
                            adj_id = str(uuid.uuid4()).upper()
                            adjust_material = {
                                "id": adj_id, "name": "调节", "type": "video_effect",
                                "effect_id": "7051252119932014606", "resource_id": "7051252119932014606",
                                "apply_target_type": 0, "source_platform": 0, "platform": "all"
                            }
                            video_effects.append(adjust_material)
                            refs.append(adj_id)
                            has_modified = True

            if has_modified:
                with open(content_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"🪄  Auto-Activated color adjustments for project '{self.name}'.")

        except Exception as e:
            print(f"⚠️  Force activation failed: {e}")

    def _patch_cloud_material_ids(self):
        """
        [协议级补丁]: 扫描 JSON 并强行注入 music_id, effect_id 或 text_style_id。
        """
        import json
        if not self._cloud_audio_patches and not self._cloud_text_patches:
            return

        content_path = os.path.join(self.root, self.name, "draft_content.json")
        if not os.path.exists(content_path): return

        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            has_modified = False
            materials = data.get("materials", {})

            # 1. 音频补丁 (BGM/SFX)
            audios = materials.get("audios", [])
            for mat in audios:
                path = mat.get("path", "")
                for dummy_path, patch_info in self._cloud_audio_patches.items():
                    if dummy_path in path:
                        if patch_info["type"] == "music":
                            mat["music_id"] = patch_info["id"]
                            mat["type"] = "music"
                        else: # sfx
                            mat["effect_id"] = patch_info["id"]
                            mat["type"] = "sound"
                        mat.setdefault("category_name", "推荐素材")
                        mat.setdefault("category_id", "6678556627852856076")
                        has_modified = True

            # 2. 花字补丁 (Styled Text)
            texts = materials.get("texts", [])
            # 路径查找优先级: 1) Skill 本地资源 -> 2) 剪映缓存
            skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            skill_artist = os.path.join(skill_root, "assets", "artistEffect")
            jy_artist = os.path.join(os.getenv('LOCALAPPDATA', ''), "JianyingPro", "User Data", "Cache", "artistEffect")
            for mat in texts:
                m_id = mat.get("id")
                if m_id in self._cloud_text_patches:
                    style_id = self._cloud_text_patches[m_id]
                    try:
                        # 解析 artistEffect 路径 (优先 Skill 本地资源)
                        effect_path = ""
                        for search_root in [skill_artist, jy_artist]:
                            effect_dir = os.path.join(search_root, style_id)
                            if os.path.isdir(effect_dir):
                                subs = [d for d in os.listdir(effect_dir) if os.path.isdir(os.path.join(effect_dir, d))]
                                if subs:
                                    effect_path = os.path.join(effect_dir, subs[0]).replace("\\", "/")
                                    break

                        c_json = json.loads(mat.get("content", "{}"))
                        text_content = c_json.get("text", "")
                        text_len = len(text_content)
                        # 为每个 style 注入 effectStyle，并修正字体/尺寸
                        for sty in c_json.get("styles", []):
                            sty["effectStyle"] = {
                                "id": style_id,
                                "path": effect_path
                            }
                            sty["size"] = 15.0
                            sty["range"] = [0, text_len]
                            sty.setdefault("font", {})
                            if not sty["font"].get("path"):
                                sty["font"]["path"] = "C:/Program Files/JianyingPro/5.9.0.11632/Resources/Font/SystemFont/zh-hans.ttf"
                                sty["font"]["id"] = ""
                        mat["content"] = json.dumps(c_json, ensure_ascii=False)
                        # 修正材质级别的字段
                        mat["type"] = "text"
                        mat["font_size"] = 15.0
                        mat["use_effect_default_color"] = True
                        has_modified = True
                        print(f"  [+] Styled text patched: {m_id} -> style {style_id} (path: {'OK' if effect_path else 'MISSING'})")
                    except Exception as e:
                        print(f"⚠️ Failed to patch text style for {m_id}: {e}")

            if has_modified:
                with open(content_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"📡 Cloud Materials Patched for project '{self.name}'.")
        except Exception as e:
            print(f"⚠️ Cloud patching failed: {e}")

    def _patch_cloud_audio_ids(self):
        # 兼容旧代码调用
        self._patch_cloud_material_ids()

    def _patch_cloud_music_ids(self):
        # 兼容旧代码调用
        self._patch_cloud_material_ids()

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

    def add_web_asset_safe(self, html_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = "5s", 
                           track_name: str = "WebVfxTrack", output_dir: Optional[str] = None, **kwargs):
        """
        [封装核心]: 将一个 HTML 动效文件录制并导入剪映。
        
        Args:
            html_path: HTML 文件的绝对路径。
            start_time: 在时间轴上的起始位置。如果为 None，自动追加到轨道末尾。
            duration: 持续时长。
            track_name: 目标轨道名称。
            output_dir: 录制资产的存放目录。若为 None，则存放在草稿的 temp_assets 目录下。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        if not HAS_RECORDER:
            print("❌ Cannot add web asset: 'web_recorder' module or its dependencies (playwright) are missing.")
            return None

        if not os.path.exists(html_path):
            print(f"❌ HTML file not found: {html_path}")
            return None

        # 1. 确定录制路径
        if output_dir is None:
            output_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(output_dir, exist_ok=True)
        video_output = os.path.join(output_dir, f"web_vfx_{int(time.time())}.webm")

        # 2. 调用录制流程
        print(f"🎬 Recording web asset: {os.path.basename(html_path)} ...")
        success = record_web_animation(html_path, video_output, max_duration=tim(duration)/1000000 + 5)
        
        if not success:
            print("⚠️ Web recording failed.")
            return None

        # 3. 导入素材 (关键：WebM 必须显式传递 duration)
        print(f"📥 Importing recorded video to jianying...")
        return self.add_media_safe(video_output, start_time, duration, track_name=track_name)

    def add_web_code_vfx(self, html_code: str, start_time: Union[str, int] = None, duration: Union[str, int] = "5s",
                        track_name: str = "WebVfxTrack", output_dir: Optional[str] = None, **kwargs):
        """
        [顶级封装]: 直接传入 HTML 代码，自动保存并录制导入。
        Agent 只需生成网页代码，剩下的交给此方法。
        Args:
            output_dir: 网页与视频资产存放目录。若为 None，则存放在草稿的 temp_assets 目录下。
        """
        # 自动创建临时 HTML 文件
        if output_dir is None:
            output_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(output_dir, exist_ok=True)
        temp_html_path = os.path.join(output_dir, f"vfx_{uuid.uuid4().hex[:8]}.html")

        # 确保代码中包含基础样式以适配 1080P
        if "<style>" not in html_code:
            html_code = html_code.replace("<style>", "<style>body{margin:0;overflow:hidden;background:transparent;}")

        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_code)

        print(f"📝 Generated VFX HTML: {temp_html_path}")
        return self.add_web_asset_safe(temp_html_path, start_time, duration, track_name=track_name, output_dir=output_dir)

    def add_color_strip(self, color_hex: str, duration: Union[str, int], track_name: str = "VideoTrack"):
        """
        [稳健版]: 通过生成物理单色图片来模拟剪映背景块。
        """
        import base64
        # 极小的 1x1 PNG 图片数据 (黑/白)
        PNG_DATA = {
            "#000000": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            "#FFFFFF": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hPwAIAgL/AOfn2v8AAAAASUVORK5CYII="
        }

        color_key = color_hex.upper()
        if color_key not in PNG_DATA:
            # 默认黑色
            color_key = "#000000"

        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        bg_path = os.path.join(temp_dir, f"bg_{color_key.replace('#','')}.png")

        # 写入物理文件
        with open(bg_path, "wb") as f:
            f.write(base64.b64decode(PNG_DATA[color_key]))

        print(f"🖼️ Generated Physical Background: {bg_path}")
        # 使用最稳健的方式添加素材
        return self.add_media_safe(bg_path, duration=duration, track_name=track_name)

    def add_media_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                       track_name: str = None, source_start: Union[str, int] = 0, **kwargs):
        """
        自动容错的媒体添加方法 (Auto-Clamp)
        支持视频/图片/音频自动分流。
        
        Args:
            media_path: 素材绝对路径
            start_time: 起始位置。如果为 None (默认)，则自动追加到该轨道末尾 (Smart Append)。
            duration: 持续时长 (建议使用 '5s' 格式字符串)。
        """
        if kwargs:
            print(f"⚠️ Warning: Ignored extra args in add_media_safe: {list(kwargs.keys())}")

        if not os.path.exists(media_path):
            print(f"❌ Media Missing: {media_path}")
            return None

        # 简单的后缀判断
        ext = os.path.splitext(media_path)[1].lower()
        if ext in ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg']:
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


    def add_tts_intelligent(self, text: str, speaker: str = "zh_male_huoli", start_time: Union[str, int] = None, track_name: str = "AudioTrack"):
        """
        [集成核心]: 智能通用 TTS 接口。
        1. 自动生成语音: 优先调用剪映 SAMI 直连 (高品质)，失败则回退微软 Edge-TTS (稳定)。
        2. 自动配置探测: 通过集成脚本嗅探本地剪映 device_id 与 iid，实现零配置即用。
        3. 自动同步导入: 生成音频后自动添加到指定轨道。
        
        Args:
            text: 语音文案。
            speaker: 剪映音色 ID (如 zh_male_huoli, zh_female_xiaopengyou)。
            start_time: 插入时间轴位置。
            track_name: 目标轨道名称。
        """
        import asyncio
        import uuid
        try:
            from universal_tts import generate_voice
        except ImportError:
            # 兼容性处理：如果 universal_tts 不在 path 中，尝试从同级目录加载
            sys.path.append(os.path.dirname(__file__))
            from universal_tts import generate_voice

        if start_time is None:
            start_time = self.get_track_duration(track_name)
            
        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        # 生成唯一文件名 (优先 ogg，兼容通用性)
        output_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex[:8]}.ogg")
        
        print(f"🎙️ Running Intelligent TTS (Auto-Fallback enabled): '{text[:30]}...'")
        
        # 兼容当前脚本的异步调用环境 (检测当前是否有 running loop)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在异步环境运行，建议用户直接使用异步 generate_voice
                print("⚠️ Warning: Detected running event loop. Synchronous wrapper might block.")
                # 这里我们依然开启一个临时线程执行或尝试嵌套 (视具体 IDE 环境而定)
                # 简单起见，技能脚本通常是顺序执行的，我们创建一个新 loop 即可
                actual_path = asyncio.run(generate_voice(text, output_file, speaker))
            else:
                actual_path = loop.run_until_complete(generate_voice(text, output_file, speaker))
        except RuntimeError:
            # 没有 Loop 时
            actual_path = asyncio.run(generate_voice(text, output_file, speaker))
        except Exception as e:
            print(f"❌ Critical TTS Error: {e}")
            return None
        
        if not actual_path or not os.path.exists(actual_path):
            print("❌ TTS Generation failed (All providers).")
            return None
            
        print(f"✅ TTS Success: {os.path.basename(actual_path)}")
        return self.add_media_safe(actual_path, start_time, track_name=track_name)

    def add_audio_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                       track_name: str = "AudioTrack", **kwargs):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
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

    def add_cloud_music(self, music_id: str, name: str, duration_s: float = None, start_time: Union[str, int] = None, track_name: str = "BGM"):
        """
        [封装核心]: 添加一个未下载的云端音乐引用。
        生成后用户需在剪映内点击该占位素材进行同步/下载。
        Args:
            duration_s: 音乐时长(秒)。如果不传，自动从 cloud_music_library.csv 按 music_id 查找。
        """
        # --- 自动获取时长 (Auto Duration Lookup) ---
        if duration_s is None:
            duration_s = self._lookup_cloud_music_duration(music_id)
            if duration_s is None:
                print(f"[CRITICAL] Cannot determine duration for music_id={music_id}. "
                      f"Please provide duration_s explicitly or ensure the ID exists in cloud_music_library.csv.")
                return None

        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.audio, track_name)
        
        start_us = tim(start_time)
        duration_us = int(float(duration_s) * 1000000)
        
        # 记录补丁信息。
        dummy_path = f"CLOUD_MUSIC_{music_id}.mp3"
        self._cloud_audio_patches[dummy_path] = {"id": music_id, "type": "music"}

        # 使用 MockAudioMaterial 绕过文件系统检测
        mat = MockAudioMaterial(
            material_id=str(uuid.uuid4()).upper(),
            duration=duration_us,
            name=name,
            path=os.path.join(self.draft_dir, dummy_path).replace("\\", "/")
        )
        
        seg = draft.AudioSegment(
            mat,
            target_timerange=trange(start_us, duration_us),
            source_timerange=trange(0, duration_us)
        )
        self.script.add_segment(seg, track_name)
        return seg

    @staticmethod
    def _lookup_cloud_music_duration(music_id: str):
        """从 cloud_music_library.csv 按 music_id 查找时长(秒)，未找到返回 None。"""
        import csv
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cloud_music_library.csv")
        csv_path = os.path.normpath(csv_path)
        if not os.path.exists(csv_path):
            print(f"Cloud music library not found: {csv_path}")
            return None
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # 跳过注释行
                lines = [line for line in f if not line.startswith('#')]
            import io
            reader = csv.DictReader(io.StringIO(''.join(lines)))
            for row in reader:
                if str(row.get('music_id', '')).strip() == str(music_id).strip():
                    dur = float(row['duration_s'])
                    print(f"Auto-resolved duration for '{row.get('title', music_id)}': {dur}s")
                    return dur
        except Exception as e:
            print(f"Failed to lookup cloud music duration: {e}")
        return None

    def add_cloud_sfx(self, effect_id: str, name: str, duration_s: float, start_time: Union[str, int] = None, track_name: str = "SFX"):
        """
        [封装核心]: 添加一个未下载的云端音效引用 (SFX)。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.audio, track_name)
        
        start_us = tim(start_time)
        duration_us = int(float(duration_s) * 1000000)
        
        dummy_path = f"CLOUD_SFX_{effect_id}.mp3"
        self._cloud_audio_patches[dummy_path] = {"id": effect_id, "type": "sfx"}

        mat = MockAudioMaterial(
            material_id=str(uuid.uuid4()).upper(),
            duration=duration_us,
            name=name,
            path=os.path.join(self.draft_dir, dummy_path).replace("\\", "/")
        )
        
        seg = draft.AudioSegment(
            mat,
            target_timerange=trange(start_us, duration_us),
            source_timerange=trange(0, duration_us)
        )
        self.script.add_segment(seg, track_name)
        return seg

    def _add_video_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                        track_name: str = "VideoTrack", source_start: Union[str, int] = 0, **kwargs):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
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

        # --- 强力时长解析与 FFprobe 兜底 ---
        if not phys_duration or phys_duration <= 0:
            print(f"⚠️ Metadata parser failed to detect duration for: {os.path.basename(media_path)}. Triggering ffprobe fallback...")
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", media_path],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5
                )
                ff_dur = float(result.stdout.strip())
                phys_duration = int(ff_dur * 1000000)
                mat.duration = phys_duration
                print(f"✅ ffprobe restored duration: {ff_dur:.2f}s")
            except Exception as ef:
                print(f"❌ ffprobe failed or not installed: {ef}")
                if fallback_duration_us:
                    print(f"⚠️ Overriding with explicit duration parameter: {fallback_duration_us/1000000:.2f}s")
                    phys_duration = fallback_duration_us
                    mat.duration = phys_duration
                else:
                    print(f"🚨 [CRITICAL ALERT] Could not resolve duration for {os.path.basename(media_path)}. Source clip might fail or silently collapse to 0s!")

        # --- 自适应分辨率逻辑 (Adaptive Resolution) ---
        # 如果用户未显式指定分辨率，且这是第一个视频素材，则自动调整项目分辨率以匹配视频
        if not self._explicit_res and not self._first_video_resolved:
            try:
                # 尝试获取素材分辨率 (pyJianYingDraft 的 VideoMaterial 通常有 width/height 属性)
                if hasattr(mat, 'width') and hasattr(mat, 'height') and mat.width > 0:
                    v_w, v_h = mat.width, mat.height
                    # 如果检测到的比例与当前项目比例不一致，执行调整
                    if v_w != self.script.width or v_h != self.script.height:
                        print(f"✨ Auto-Adjusting project resolution to match first video: {v_w}x{v_h}")
                        self.script.width = v_w
                        self.script.height = v_h
                self._first_video_resolved = True
            except Exception as res_err:
                print(f"⚠️ Resolution adaptive failed: {res_err}")
                self._first_video_resolved = True # 即使失败也标记为已尝试，防止后续重复尝试
        start_us = tim(start_time)
        src_start_us = tim(source_start)
        actual_duration = self._calculate_duration(duration, phys_duration - src_start_us)

        # 溢出警告 (Overflow Check)
        if phys_duration > 0 and (src_start_us + actual_duration > phys_duration):
            print(f"\n🚨 [CRITICAL WARNING] Clip overflow detected for: {os.path.basename(media_path)}")
            print(f"   -> Required: Start={src_start_us/1000000:.2f}s, Duration={actual_duration/1000000:.2f}s, End={(src_start_us + actual_duration)/1000000:.2f}s")
            print(f"   -> Available media length limit: {phys_duration/1000000:.2f}s")
            print(f"   -> This may result in silent truncation or a broken timeline!\n")

        seg = draft.VideoSegment(
            mat,
            target_timerange=trange(start_us, actual_duration),
            source_timerange=trange(src_start_us, actual_duration) 
        )
        self.script.add_segment(seg, track_name)
        return seg

    def add_compound_project(self, sub_project, clip_name: str = None, start_time: Union[str, int] = None, track_name: str = "VideoTrack"):
        """
        [顶级进阶接口]: 将另一个 JyProject 对象整体打包为复合片段注入当前工程。
        原理: 协议级嵌套，实现真正的模组化剪辑。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        
        main_script = self.script
        sub_script = sub_project.script
        
        # 1. 生成协议所需的 ID
        combination_id = str(uuid.uuid4()).upper()
        draft_material_id = str(uuid.uuid4()).upper()
        video_material_id = str(uuid.uuid4()).upper()
        
        import json
        sub_data = json.loads(sub_script.dumps())
        duration = sub_data.get("duration", 0)
        clip_name = clip_name or sub_project.name
        
        # 2. 注入伪视频素材
        mock_mat = MockVideoMaterial(video_material_id, duration, clip_name, width=main_script.width, height=main_script.height)
        main_script.materials.videos.append(mock_mat)
        
        # 3. 注入嵌套工程素材 (Hook ScriptMaterial 以支持输出 drafts 数组)
        draft_meta = {
            "id": draft_material_id,
            "combination_id": combination_id,
            "type": "combination",
            "name": clip_name,
            "draft": sub_data
        }
        
        if not hasattr(main_script.materials, "custom_drafts"):
            main_script.materials.custom_drafts = []
            orig_export = main_script.materials.export_json
            def new_export():
                d = orig_export()
                # 注入嵌套工程协议列表
                d["drafts"] = main_script.materials.custom_drafts
                return d
            main_script.materials.export_json = new_export
            
        main_script.materials.custom_drafts.append(draft_meta)
        
        # 4. 创建轨道并添加自定义 Segment
        self._ensure_track(draft.TrackType.video, track_name)
        track = self.script.tracks[track_name]
        
        start_us = tim(start_time)
        seg = CompoundSegment(mock_mat, draft_material_id, duration, start_us=start_us)
        track.add_segment(seg)
        
        main_script.duration = max(main_script.duration, start_us + duration)
        print(f"📦 Compound Injection: '{clip_name}' -> '{self.name}' (Start: {start_us/1e6}s, Dur: {duration/1e6}s)")
        return seg

    # --- 模板替换与路径重连 API ---

    def replace_material_by_name(self, placeholder_name: str, new_material_path: str, start_s: float = 0):
        """
        通过片段名称或素材名称语义化替换素材。
        支持新创建轨道 (tracks) 和 加载的模板轨道 (imported_tracks)。
        """
        if not os.path.exists(new_material_path):
            print(f"❌ Replacement Failed: File not found -> {new_material_path}")
            return False

        new_mat = draft.VideoMaterial(new_material_path)
        count = 0

        # 获取所有待扫描片段的函数 (闭包)
        def process_segments(segments, is_imported=False):
            nonlocal count
            for seg in segments:
                # 匹配逻辑
                mat_name = ""
                # A. 轨道直接持有的素材 (新创建)
                if hasattr(seg, 'material_instance'):
                    mat_name = getattr(seg.material_instance, 'material_name', getattr(seg.material_instance, 'name', ''))
                # B. 模板加载的素材 (ImportedSegment 需要查表)
                elif hasattr(seg, 'material_id'):
                    mid = seg.material_id
                    for m in self.script.imported_materials.get('videos', []):
                        if m['id'] == mid:
                            mat_name = m.get('material_name', m.get('name', ''))
                            break
                
                if mat_name:
                    # print(f"🔍 [Debug] Scanning segment mat: '{mat_name}'") # 只有非常深入排查才开启
                    pass

                # 执行替换
                if mat_name and placeholder_name.lower() in mat_name.lower():
                    print(f"🔄 [TemplateMatch] Target: '{mat_name}' -> '{os.path.basename(new_material_path)}'")
                    if hasattr(seg, 'material_instance'):
                        seg.material_instance = new_mat
                    else:
                        seg.material_id = new_mat.material_id
                        self.script.add_material(new_mat)
                    
                    # 同步时长/起点
                    old_dur = seg.target_timerange.duration
                    seg.source_timerange = draft.Timerange(int(start_s * 1000000), old_dur)
                    count += 1

        # 1. 扫描新创建的轨道
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        for t in iterator: process_segments(t.segments)

        # 2. 扫描加载的模板轨道
        if hasattr(self.script, 'imported_tracks'):
            for t in self.script.imported_tracks:
                if hasattr(t, 'segments'): process_segments(t.segments, is_imported=True)

        if count > 0:
            print(f"✅ Successfully replaced {count} instances.")
            return True
        return False

    def replace_material_by_path(self, old_path_keyword: str, new_material_path: str, start_s: float = 0):
        """
        通过原始路径关键字替换素材。
        """
        if not os.path.exists(new_material_path):
            print(f"❌ Replacement Failed: File not found -> {new_material_path}")
            return False

        new_mat = draft.VideoMaterial(new_material_path)
        count = 0

        def process_segments(segments):
            nonlocal count
            for seg in segments:
                orig_path = ""
                if hasattr(seg, 'material_instance'):
                    orig_path = getattr(seg.material_instance, 'path', '')
                elif hasattr(seg, 'material_id'):
                    mid = seg.material_id
                    for m in self.script.imported_materials.get('videos', []):
                        if m['id'] == mid:
                            orig_path = m.get('path', '')
                            break
                
                if old_path_keyword.lower() in orig_path.lower():
                    print(f"🔗 [PathMatch] Found '{orig_path}', redirecting...")
                    if hasattr(seg, 'material_instance'):
                        seg.material_instance = new_mat
                    else:
                        seg.material_id = new_mat.material_id
                        self.script.add_material(new_mat)
                    
                    old_dur = seg.target_timerange.duration
                    seg.source_timerange = draft.Timerange(int(start_s * 1000000), old_dur)
                    count += 1

        # 扫描两类轨道
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        for t in iterator: process_segments(t.segments)
        if hasattr(self.script, 'imported_tracks'):
            for t in self.script.imported_tracks:
                if hasattr(t, 'segments'): process_segments(t.segments)

        return count > 0

    def reconnect_all_assets(self, local_asset_root: str):
        """
        全局路径重连：自动找回失效的素材。
        """
        print(f"🛠️  Starting Global Reconnection in: {local_asset_root}")
        file_index = {}
        for root, _, files in os.walk(local_asset_root):
            for f in files: file_index[f.lower()] = os.path.join(root, f)

        reconnected_count = 0
        
        # 1. 处理新创建的素材 (ScriptMaterial)
        if hasattr(self.script, 'materials'):
            all_mats = self.script.materials.videos + self.script.materials.audios
            for mat in all_mats:
                orig_path = getattr(mat, 'path', '')
                if not orig_path or not os.path.exists(orig_path):
                    filename = os.path.basename(orig_path).lower()
                    if filename in file_index:
                        mat.path = file_index[filename]
                        if hasattr(mat, 'local_material_id'): mat.local_material_id = ""
                        reconnected_count += 1
        
        # 2. 处理导入的素材库 (Imported Materials JSON dicts)
        if hasattr(self.script, 'imported_materials'):
            for mat_list in self.script.imported_materials.values():
                for mat_dict in mat_list:
                    p = mat_dict.get('path', '')
                    if p and not os.path.exists(p):
                        fname = os.path.basename(p).lower()
                        if fname in file_index:
                            new_local_path = file_index[fname]
                            mat_dict['path'] = new_local_path
                            # 只清除物理指纹，保留主逻辑关联 ID (id)
                            # 这样轨道上的片段就能瞬间恢复显示
                            if 'local_material_id' in mat_dict:
                                mat_dict['local_material_id'] = ""
                            reconnected_count += 1
                            print(f"🔗 [Auto-Link] Found local asset for '{fname}', path updated.")
        
        print(f"🏁 Reconnection finished. Fixed {reconnected_count} assets.")
        return reconnected_count

    def _calculate_duration(self, req_duration, phys_duration):
        if req_duration is not None:
            req = tim(req_duration)
            # 保护：如果请求时长非零但被解析为 0 (如 0.05)，强制设为 1微秒，防止底层库 ZeroDivisionError
            if req == 0 and (isinstance(req_duration, (int, float)) and req_duration > 0):
                req = 1
            
            if req > phys_duration:
                print(f"⚠️ Auto-Clamp: {req_duration} > physical. Using full length.")
                return phys_duration
            return req
        return phys_duration

    def add_styled_text(self, text: str, style_id: str, start_time: Union[str, int] = None, duration: Union[str, int] = "3s", 
                        track_name: str = "FlowerText", **kwargs):
        """
        [封装核心]: 添加花字 (Styled Text)。
        使用此方法后，系统会在保存时注入 effect_id。
        """
        seg = self.add_text_simple(text, start_time=start_time, duration=duration, track_name=track_name, **kwargs)
        if seg:
            # 记录此素材需要补丁
            self._cloud_text_patches[seg.material_id] = style_id
        return seg

    def add_text_simple(self, text: str, start_time: Union[str, int] = None, duration: Union[str, int] = "3s", 
                        track_name: str = "TextTrack",
                        font_size: float = 5.0, # 锁定默认字号为 5.0
                        color_rgb: tuple = (1.0, 1.0, 1.0),
                        bold: bool = False,
                        align: int = 1,
                        auto_wrapping: bool = True,
                        transform_y: float = -0.8,
                        anim_in: str = None, **kwargs):
        """
        极简文本接口 (增强版 V2)
        特点:
        1. 容错: 自动忽略不支持的参数 (如 position) 并打印警告。
        2. 自动分层: 如果轨道上有重叠，自动创建新轨道 (TextTrack_L2, _L3...)。
        3. 智能追加: 如果不传 start_time，自动衔接上一个片段。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)
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
        
        # 默认样式：白字 + 黑色描边 (提高对比度，适配白底和各种背景)
        # width 30 对应映射后的 0.06
        border = TextBorder(color=(0.0, 0.0, 0.0), width=30.0)
        style = TextStyle(size=font_size, color=color_rgb, bold=bold, align=align, 
                          auto_wrapping=auto_wrapping)
        clip = ClipSettings(transform_y=transform_y)
        
        start_us = safe_tim(start_time)
        dur_us = safe_tim(duration)
        
        seg = draft.TextSegment(text, trange(start_us, dur_us), style=style, clip_settings=clip, border=border)
        
        if anim_in:
            anim = _resolve_enum(TextIntro, anim_in)
            if anim: 
                seg.add_animation(anim)
            else:
                # Fallback: 支持直接传入效果 ID (Raw ID Support)
                # 当 Agent 从 asset_search 拿到一个未知 ID 时，允许透传
                print(f"ℹ️ Enum lookup failed. Using raw animation ID: {anim_in}")
                try:
                    # 构造一个符合底层接口的伪对象 (Duck Typing)
                    from types import SimpleNamespace
                    raw_anim = SimpleNamespace(value=anim_in)
                    seg.add_animation(raw_anim)
                except Exception as e:
                    print(f"⚠️ Failed to apply raw animation ID: {e}")
        
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

    def _get_visual_width(self, text: str):
        """计算字幕的视觉宽度：中文=1.0, 英文/符号=0.5"""
        return sum(1.0 if ord(c) > 127 else 0.5 for c in text)

    def add_subtitles_auto_split(self, text: str, start_time: Union[str, int], duration: Union[str, int], 
                               track_name: str = "Subtitles", **kwargs):
        """
        [封装核心]: 遵循规范的高级字幕接口 (V2.1)。
        1. 按中文 '，' '。' '！' '？' 等切分。
        2. 单条上限 27 个视觉字符。
        3. 自动根据视觉长度分配显示时长。
        """
        import re
        input_text = text.strip()
        if not input_text: return []

        # 1. 分句：按标点符号切分，保留分隔符
        raw_parts = re.split(r'([，。！？、\n\r]+)', input_text)
        
        # 重新组合：将文本与其后的标点合并
        sentences = []
        i = 0
        while i < len(raw_parts):
            part = raw_parts[i]
            if i + 1 < len(raw_parts):
                # 检查下一项是否是标点
                if re.match(r'[，。！？、\n\r]+', raw_parts[i+1]):
                    part += raw_parts[i+1]
                    i += 1
            if part.strip():
                sentences.append(part.strip())
            i += 1

        # 2. 对过长的句子进行强制切分
        final_parts = []
        for s in sentences:
            temp_s = s
            while self._get_visual_width(temp_s) > 27.0:
                cut_idx = 0
                current_width = 0.0
                for idx, char in enumerate(temp_s):
                    char_w = 1.0 if ord(char) > 127 else 0.5
                    if current_width + char_w > 27.0:
                        break
                    current_width += char_w
                    cut_idx = idx + 1
                
                if cut_idx == 0: cut_idx = 1
                final_parts.append(temp_s[:cut_idx].strip())
                temp_s = temp_s[cut_idx:].strip()
            
            if temp_s:
                final_parts.append(temp_s)
            
        if not final_parts: return []
        
        # 3. 时间分配
        total_weight = sum(self._get_visual_width(p) for p in final_parts)
        if total_weight == 0: return []
        
        total_dur_us = safe_tim(duration)
        start_us = safe_tim(start_time)
        
        added_segs = []
        acc_dur_us = 0
        for i, p in enumerate(final_parts):
            # 权重计算包含标点，以反映语音中的自然停顿
            p_weight = self._get_visual_width(p)
            p_dur_us = int((p_weight / total_weight) * total_dur_us)
            
            # 最后一个片段填满剩余时间
            if i == len(final_parts) - 1:
                p_dur_us = total_dur_us - acc_dur_us
                
            if p_dur_us <= 0: continue
            
            # 实际显示时剔除末尾标点符号，保持短视频字幕一贯的“无标点”风格
            clean_text = p.rstrip('，。！？、\n\r ')
            
            seg = self.add_text_simple(
                clean_text, 
                start_time=start_us + acc_dur_us, 
                duration=p_dur_us, 
                track_name=track_name, 
                **kwargs
            )
            added_segs.append(seg)
            acc_dur_us += p_dur_us
            
        return added_segs
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

    def add_transition_simple(self, transition_name: str, duration: str = "0.5s", track_name: str = "VideoTrack", effect_id: str = None):
        """
        向指定轨道的最后两个片段之间添加转场。
        支持 transition_name (Enum 模糊匹配) 或 effect_id (原始 ID)。
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

        if effect_id:
            from types import SimpleNamespace
            # 兼容 pyJianYingDraft 的 TransitionMeta 接口，需要同时有 name 和 value
            trans_enum = SimpleNamespace(value=effect_id, name=transition_name or "CustomTransition")
        else:
            trans_enum = _resolve_enum(TransitionType, transition_name)
        
        if not trans_enum: 
            print(f"⚠️ Could not resolve transition: {transition_name}")
            return

        # 这里的逻辑假设最后添加的片段需要转场
        last_seg = track.segments[-1]
        try:
            # 关键修复: 转换 duration 为微秒
            dur_us = tim(duration)
            print(f"DEBUG: trans_enum={trans_enum} (type={type(trans_enum)})")
            print(f"DEBUG: last_seg={last_seg} (type={type(last_seg)})")
            last_seg.add_transition(trans_enum, duration=dur_us)
            print(f"🔗 Added Transition: {transition_name or effect_id} (Duration: {dur_us}us)")
        except Exception as e:
            import traceback
            print(f"❌ Failed add transition: {e}")
            traceback.print_exc()

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
    
    # Command: clone (新)
    clone_parser = subparsers.add_parser("clone", help="Clone an existing draft as a template")
    clone_parser.add_argument("--template", required=True, help="Source template name")
    clone_parser.add_argument("--name", required=True, help="New project name")
    
    # Command: import (新)
    import_ext_parser = subparsers.add_parser("import", help="Import an external project folder into JianYing drafts")
    import_ext_parser.add_argument("--path", required=True, help="Full path to the external project folder")
    import_ext_parser.add_argument("--name", help="New project name (optional)")
    
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

    elif args.command == "clone":
        try:
            p = JyProject.from_template(args.template, args.name)
            p.save() # 确保克隆后的项目立即生效保存一次
            print(f"✅ Success! New project created: {args.name}")
        except Exception as e:
            print(f"❌ Clone failed: {e}")

    elif args.command == "import":
        try:
            p = JyProject.import_external_draft(args.path, args.name)
            p.save()
            print(f"✅ Success! Project imported to JianYing drafts: {p.name}")
        except Exception as e:
            print(f"❌ Import failed: {e}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        print("JyWrapper Library Loaded. Import `JyProject` to use.")

import os
import subprocess
import difflib
from typing import Union, List, Dict
import functools

# ----------------- 路径自动探测 -----------------
def get_default_drafts_root() -> str:
    """自动探测剪映草稿目录 (Windows)"""
    local_app_data = os.environ.get('LOCALAPPDATA')
    user_profile = os.environ.get('USERPROFILE')
    
    candidates = []
    if local_app_data:
        candidates.extend([
            os.path.join(local_app_data, "JianyingPro/User Data/Projects/com.lveditor.draft"),
            os.path.join(local_app_data, "CapCut/User Data/Projects/com.lveditor.draft"),
        ])
    
    if user_profile:
        candidates.append(os.path.join(user_profile, "AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft"))

    fallback = "C:/Users/Administrator/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft"
    for path in candidates:
        if os.path.exists(path): return path
    return candidates[0] if candidates else fallback

def get_all_drafts(root_path: str = None) -> List[Dict]:
    """获取所有草稿并按修改时间排序"""
    root = root_path or get_default_drafts_root()
    drafts = []
    if not os.path.exists(root): return []
        
    for item in os.listdir(root):
        path = os.path.join(root, item)
        if os.path.isdir(path):
            if os.path.exists(os.path.join(path, "draft_content.json")) or \
               os.path.exists(os.path.join(path, "draft_meta_info.json")):
                drafts.append({
                    "name": item,
                    "mtime": os.path.getmtime(path),
                    "path": path
                })
    return sorted(drafts, key=lambda x: x['mtime'], reverse=True)

try:
    from pyJianYingDraft import tim
except ImportError:
    def tim(v):
        if isinstance(v, (int, float)): return int(v * 1000000)
        return 0

# ----------------- 时间与格式转换 -----------------
def safe_tim(inp: Union[str, int, float]) -> int:
    """
    增强版时间解析器，支持:
    1. 1h2m3s (底层库自带)
    2. 00:00:10 (冒号分隔格式)
    3. 10 (纯数字秒)
    """
    # 约定：
    # - int 统一视为“微秒”，避免 200000us 被误判为 200000s
    # - float 视为“秒”
    if isinstance(inp, int):
        return int(inp)
    if isinstance(inp, float):
        return int(inp * 1000000)

    if isinstance(inp, str) and ":" in inp:
        try:
            parts = inp.split(":")
            if len(parts) == 3: # HH:MM:SS
                h, m, s = map(float, parts)
                return int((h * 3600 + m * 60 + s) * 1000000)
            elif len(parts) == 2: # MM:SS
                m, s = map(float, parts)
                return int((m * 60 + s) * 1000000)
        except Exception:
            pass
    if isinstance(inp, str):
        s = inp.strip()
        # 纯数字字符串按秒处理
        if s.replace(".", "", 1).isdigit():
            return int(float(s) * 1000000)
    return tim(inp)

def format_srt_time(us: int) -> str:
    """将微秒转换为 SRT 时间戳格式 (HH:MM:SS,mmm)"""
    ms = (us // 1000) % 1000
    s = (us // 1000000) % 60
    m = (us // 60000000) % 60
    h = (us // 3600000000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ----------------- FFprobe 工具 -----------------

@functools.lru_cache(maxsize=128)
def get_duration_ffprobe_cached(file_path: str) -> float:
    """
    带缓存的 ffprobe 时长检测，防止重复开销。
    """
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        return 0.0
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ ffprobe failed for {os.path.basename(file_path)}: {e}")
        return 0.0

# ----------------- Enum 模糊匹配 -----------------
def resolve_enum_with_synonyms(enum_cls, name: str, synonyms_dict: dict):
    """
    尝试从 Enum 类中找到匹配的属性。
    """
    if not name: return None
    
    if hasattr(enum_cls, name):
        return getattr(enum_cls, name)
    
    name_lower = name.lower()
    mapping = {k.lower(): k for k in enum_cls.__members__.keys()}
    
    if name_lower in mapping:
        real_key = mapping[name_lower]
        return getattr(enum_cls, real_key)

    for key, synonyms in synonyms_dict.items():
        if name_lower == key.lower():
            for candidate in synonyms:
                if candidate in mapping:
                    real_key = mapping[candidate]
                    print(f"ℹ️ Map EN->CN: '{name}' -> '{real_key}'")
                    return getattr(enum_cls, real_key)
        
        if key.lower() in mapping:
            for syn in synonyms:
                if syn in name_lower or name_lower in syn:
                    real_key = mapping[key.lower()]
                    print(f"ℹ️ Synonym Match: '{name}' -> '{real_key}'")
                    return getattr(enum_cls, real_key)
    
    matches = difflib.get_close_matches(name, enum_cls.__members__.keys(), n=1, cutoff=0.6)
    if matches:
        print(f"ℹ️ Fuzzy Match: '{name}' -> '{matches[0]}'")
        return getattr(enum_cls, matches[0])
    return None

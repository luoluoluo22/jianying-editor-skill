import os
import sys
import shutil
import time
import json
import uuid
import re
import pyJianYingDraft as draft
from utils.formatters import format_srt_time, get_default_drafts_root

class JyProjectBase:
    """
    JyProject 的核心基类，负责工程生命周期、草稿定位与质检。
    """
    def __init__(self, project_name: str, width: int = 1920, height: int = 1080, 
                 drafts_root: str = None, overwrite: bool = True, script_instance: any = None):
        self.root = os.path.abspath(drafts_root or get_default_drafts_root())
        if not os.path.exists(self.root):
            try:
                os.makedirs(self.root)
            except Exception:
                pass
                
        print(f"📂 Project Root: {self.root}")
        
        self.df = draft.DraftFolder(self.root)
        self.name = self._sanitize_project_name(project_name)
        self.draft_dir = self._safe_join_root(self.name)
        self._internal_colors = [] 
        self._cloud_audio_patches = {} 
        self._cloud_text_patches = {}   
        
        self._explicit_res = (width != 1920 or height != 1080)
        self._first_video_resolved = False
        self._cloud_manager = None

        if script_instance:
            self.script = script_instance
            self._explicit_res = True 
            return

        has_draft = self.df.has_draft(self.name)
        
        if has_draft:
            draft_path = self._safe_join_root(self.name)
            content_path = os.path.join(draft_path, "draft_content.json")
            meta_path = os.path.join(draft_path, "draft_meta_info.json")
            
            if not os.path.exists(content_path) or not os.path.exists(meta_path):
                if overwrite:
                    print(f"Corrupted draft detected (missing json): {self.name}")
                    print(f"Auto-healing: Removing corrupted folder...")
                    try:
                        self._safe_remove_dir(draft_path)
                        has_draft = False
                    except Exception as e:
                        print(f"Failed to cleanup corrupted draft: {e}")
                else:
                    print(f"Corrupted draft detected: {self.name} (missing json). Use overwrite=True to auto-fix.")

        if has_draft and not overwrite:
            print(f"Loading existing project: {self.name}")
            try:
                self.script = self.df.load_template(self.name)
            except Exception as e:
                print(f"Load failed ({e}), forcing recreate...")
                self.script = self.df.create_draft(self.name, width, height, allow_replace=True)
        else:
            print(f"Creating new project: {self.name}")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.script = self.df.create_draft(self.name, width, height, allow_replace=overwrite)
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        print(f"\n{'='*50}\n  [!] 剪映正在占用该项目。请关闭后再试...\n{'='*50}\n")
                        time.sleep(5)
                    else:
                        raise

    def get_track_duration(self, track_name: str) -> int:
        """获取指定轨道当前的总时长（微秒）"""
        tracks = self.script.tracks
        iterator = tracks.values() if isinstance(tracks, dict) else (tracks if isinstance(tracks, list) else [])
        for t in iterator:
            if hasattr(t, "name") and getattr(t, "name") == track_name:
                max_end = 0
                for seg in t.segments:
                    end = seg.target_timerange.start + seg.target_timerange.duration
                    if end > max_end: max_end = end
                return max_end
        return 0

    @property
    def cloud_manager(self):
        """延迟加载 CloudManager 以避免在不需要时初始化数据库。"""
        if self._cloud_manager is None:
            from cloud_manager import CloudManager
            self._cloud_manager = CloudManager()
        return self._cloud_manager

    def audit_timeline(self, track_details):
        """审计时间轴并打印可能的高频重复片段异常警告。"""
        issues_found = False
        mat_start_counts = {}
        for td in track_details:
            if td["type"] in ["video", "audio"]:
                for seg in td["segments"]:
                    path = seg.get("path", "")
                    src_start = seg.get("src_start_us", 0)
                    if path:
                        key = f"{path}@{src_start}"
                        mat_start_counts[key] = mat_start_counts.get(key, 0) + 1

        for key, count in mat_start_counts.items():
            if count > 5:
                issues_found = True
                path, start_us = key.rsplit("@", 1)
                start_sec = int(start_us) / 1000000
                print(f"⚠️ [AUDIT WARNING] 检测到高频率重复片段！文件: '{os.path.basename(path)}' 被从起点 {start_sec}s 截取了 {count} 次。")

        if issues_found:
            print("❗️ Timeline Audit highlighted potential duplication issues.")
    def _sanitize_project_name(self, name: str) -> str:
        """仅允许安全字符，防止路径穿越和非法文件名。"""
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(name)).strip().strip(".")
        cleaned = re.sub(r"\s+", " ", cleaned)
        while ".." in cleaned:
            cleaned = cleaned.replace("..", "_")
        if not cleaned:
            raise ValueError("Invalid project_name: empty after sanitization.")
        if cleaned != name:
            print(f"⚠️ project_name sanitized: '{name}' -> '{cleaned}'")
        return cleaned

    def _safe_join_root(self, *parts: str) -> str:
        target = os.path.abspath(os.path.normpath(os.path.join(self.root, *parts)))
        if os.path.commonpath([self.root, target]) != self.root:
            raise ValueError(f"Unsafe path detected: {target}")
        return target

    def _safe_remove_dir(self, path: str) -> None:
        abs_path = os.path.abspath(path)
        if abs_path == self.root:
            raise ValueError("Refuse to remove drafts root directly.")
        if os.path.commonpath([self.root, abs_path]) != self.root:
            raise ValueError(f"Refuse to remove path outside root: {abs_path}")
        shutil.rmtree(abs_path, ignore_errors=True)

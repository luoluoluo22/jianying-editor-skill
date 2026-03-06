import os
import re
import shutil
import time

import pyJianYingDraft as draft
from utils.formatters import get_default_drafts_root


class JyProjectBase:
    """
    Core project lifecycle wrapper:
    - draft creation/loading
    - safe path handling
    - timeline audit helpers
    """

    def __init__(
        self,
        project_name: str,
        width: int = 1920,
        height: int = 1080,
        drafts_root: str = None,
        overwrite: bool = True,
        script_instance=None,
    ):
        self.root = os.path.abspath(drafts_root or get_default_drafts_root())
        if not os.path.exists(self.root):
            try:
                os.makedirs(self.root)
            except Exception:
                pass

        print(f"Project Root: {self.root}")

        self.df = draft.DraftFolder(self.root)
        self.name = self._sanitize_project_name(project_name)
        self.draft_dir = self._safe_join_root(self.name)
        self._internal_colors = []
        self._cloud_audio_patches = {}
        self._cloud_text_patches = {}

        self._explicit_res = width != 1920 or height != 1080
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
                    print("Auto-healing: Removing corrupted folder...")
                    try:
                        self._safe_remove_dir(draft_path)
                        has_draft = False
                    except Exception as e:
                        print(f"Failed to cleanup corrupted draft: {e}")
                else:
                    print(
                        f"Corrupted draft detected: {self.name} (missing json). "
                        "Use overwrite=True to auto-fix."
                    )

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
                    self.script = self.df.create_draft(
                        self.name, width, height, allow_replace=overwrite
                    )
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        released = self._try_release_project_lock()
                        if released:
                            print(
                                "[i] Detected project lock. Switched JianYing to home page, retrying..."
                            )
                        else:
                            print(
                                "\n"
                                + "=" * 50
                                + "\n  [!] 剪映正在占用该项目，自动释放失败。请手动切回主界面后重试。\n"
                                + "=" * 50
                                + "\n"
                            )
                        time.sleep(2)
                    else:
                        raise

    def _try_release_project_lock(self) -> bool:
        """
        Best-effort lock release:
        activate JianYing and switch from edit page to home page.
        """
        try:
            from pyJianYingDraft.jianying_controller import JianyingController
        except Exception as e:
            print(f"[warn] lock-release controller unavailable: {e}")
            return False

        try:
            ctl = JianyingController(keep_topmost=False)
            status = getattr(ctl, "app_status", "")

            if status == "home":
                ctl.release_topmost()
                return True

            if status == "pre_export":
                try:
                    ctl.app.SendKeys("{Esc}")
                    time.sleep(1)
                    ctl.get_window(topmost=False)
                except Exception:
                    pass
                status = getattr(ctl, "app_status", "")

            if status == "edit":
                ctl.switch_to_home()
                ctl.get_window(topmost=False)
                ctl.release_topmost()
                return getattr(ctl, "app_status", "") == "home"

            return False
        except Exception as e:
            print(f"[warn] auto lock-release failed: {e}")
            return False

    def get_track_duration(self, track_name: str) -> int:
        tracks = self.script.tracks
        iterator = (
            tracks.values()
            if isinstance(tracks, dict)
            else (tracks if isinstance(tracks, list) else [])
        )
        for track in iterator:
            if hasattr(track, "name") and getattr(track, "name") == track_name:
                max_end = 0
                for seg in track.segments:
                    end = seg.target_timerange.start + seg.target_timerange.duration
                    if end > max_end:
                        max_end = end
                return max_end
        return 0

    @property
    def cloud_manager(self):
        if self._cloud_manager is None:
            from cloud_manager import CloudManager

            self._cloud_manager = CloudManager()
        return self._cloud_manager

    def audit_timeline(self, track_details):
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
                start_sec = int(start_us) / 1_000_000
                print(
                    f"[AUDIT WARNING] High repetition detected: "
                    f"'{os.path.basename(path)}' from {start_sec}s repeated {count} times."
                )

        if issues_found:
            print("Timeline Audit highlighted potential duplication issues.")

    def _sanitize_project_name(self, name: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(name)).strip().strip(".")
        cleaned = re.sub(r"\s+", " ", cleaned)
        while ".." in cleaned:
            cleaned = cleaned.replace("..", "_")
        if not cleaned:
            raise ValueError("Invalid project_name: empty after sanitization.")
        if cleaned != name:
            print(f"[warn] project_name sanitized: '{name}' -> '{cleaned}'")
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

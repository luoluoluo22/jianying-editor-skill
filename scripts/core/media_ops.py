import hashlib
import os
import shutil
import sys
from typing import Union

import pyJianYingDraft as draft
from pyJianYingDraft import trange
from pyJianYingDraft.exceptions import SegmentOverlap
from utils.formatters import get_duration_ffprobe_cached, safe_tim
from utils.media_normalizer import normalize_video_for_jianying, normalize_webm_for_jianying


class MediaOpsMixin:
    """
    JyProject 的媒体处理 Mixin。
    """

    def add_media_safe(
        self,
        media_path: str,
        start_time: Union[str, int] = None,
        duration: Union[str, int] = None,
        track_name: str = None,
        source_start: Union[str, int] = 0,
        **kwargs,
    ):
        if not os.path.exists(media_path):
            print(f"❌ Media Missing: {media_path}")
            return None

        ext = os.path.splitext(media_path)[1].lower()
        # Normalize WEBM to a stable MP4 profile before import to avoid parser incompatibilities.
        if ext == ".webm":
            normalized_path = normalize_webm_for_jianying(media_path)
            if not normalized_path:
                print(f"❌ WEBM normalization failed: {media_path}")
                return None
            media_path = normalized_path
            ext = ".mp4"
        elif ext in [".mp4", ".mov", ".m4v"]:
            normalized_path = normalize_video_for_jianying(media_path)
            if normalized_path:
                media_path = normalized_path
                ext = os.path.splitext(media_path)[1].lower()

        # 复制进草稿目录，使草稿自包含，规避 macOS 沙盒拦截及 Windows 5.9+ 外部素材丢失问题
        media_path = self._stage_local_asset(media_path)

        if ext in [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"]:
            return self.add_audio_safe(media_path, start_time, duration, track_name or "AudioTrack")

        return self._add_video_safe(
            media_path, start_time, duration, track_name or "VideoTrack", source_start=source_start
        )

    def _stage_local_asset(self, media_path: str, subdir: str = "materials") -> str:
        """把外部本地素材复制进草稿目录内部（默认 materials/ 子目录），返回副本绝对路径。

        1. macOS (Darwin)：剪映为沙盒应用，草稿引用外部路径常因系统权限提示格式不支持或无法访问；
        2. 全平台 (Windows/macOS/Linux)：若素材在临时目录，源文件被清理会导致剪映 5.9+ 报“检测到媒体丢失”；
        复制进草稿目录可让工程自包含、路径永久稳定。
        若素材已在草稿目录内，则跳过复制。
        """
        try:
            draft_dir = getattr(self, "draft_dir", "")
            if not draft_dir or not os.path.isfile(media_path):
                return media_path

            abs_media = os.path.abspath(media_path)
            abs_draft = os.path.abspath(draft_dir)

            try:
                if os.path.commonpath([abs_draft, abs_media]) == abs_draft:
                    return abs_media
            except ValueError:
                pass

            target_dir = os.path.join(abs_draft, subdir)
            os.makedirs(target_dir, exist_ok=True)

            ext = os.path.splitext(abs_media)[1].lower()
            digest = hashlib.md5(abs_media.encode("utf-8")).hexdigest()
            staged = os.path.join(target_dir, f"{digest}{ext}")

            if os.path.exists(staged) and os.path.getsize(staged) == os.path.getsize(abs_media):
                return staged

            shutil.copy2(abs_media, staged)
            return staged
        except Exception as e:
            print(f"⚠️ 素材复制进草稿目录失败，回退使用源路径: {e}")
            return media_path

    def _stage_media_for_jianying(self, media_path: str) -> str:
        """兼容 macOS 剪映沙盒的暂存接口（向后兼容/单测兼容）"""
        return self._stage_local_asset(media_path, subdir="media")

    def add_audio_safe(
        self,
        media_path: str,
        start_time: Union[str, int] = None,
        duration: Union[str, int] = None,
        track_name: str = "AudioTrack",
        **kwargs,
    ):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.audio, track_name)

        # 音频同样复制进草稿目录：云音乐缓存在 ~/cloud_cache，macOS 沙盒下会丢失
        media_path = self._stage_local_asset(media_path)

        try:
            mat = draft.AudioMaterial(media_path)
            phys_duration = mat.duration
        except Exception:
            return None

        start_us = safe_tim(start_time)
        actual_duration = self._calculate_duration(duration, phys_duration)

        seg = draft.AudioSegment(
            mat, trange(start_us, actual_duration), source_timerange=trange(0, actual_duration)
        )
        target_track = self._find_available_audio_track_name(track_name, seg)
        self.script.add_segment(seg, target_track)
        return seg

    def _add_video_safe(
        self,
        media_path: str,
        start_time: Union[str, int] = None,
        duration: Union[str, int] = None,
        track_name: str = "VideoTrack",
        source_start: Union[str, int] = 0,
        **kwargs,
    ):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.video, track_name)

        try:
            fallback_duration_us = safe_tim(duration) * 10 if duration else None
            mat = draft.VideoMaterial(media_path, duration=fallback_duration_us)
            phys_duration = mat.duration
        except Exception:
            return None

        if not phys_duration or phys_duration <= 0:
            ff_dur = get_duration_ffprobe_cached(media_path)
            if ff_dur > 0:
                phys_duration = int(ff_dur * 1000000)
                mat.duration = phys_duration

        if not self._explicit_res and not self._first_video_resolved:
            if hasattr(mat, "width") and mat.width > 0:
                self.script.width, self.script.height = mat.width, mat.height
            self._first_video_resolved = True

        start_us = safe_tim(start_time)
        src_start_us = safe_tim(source_start)
        actual_duration = self._calculate_duration(duration, phys_duration - src_start_us)

        seg = draft.VideoSegment(
            mat,
            trange(start_us, actual_duration),
            source_timerange=trange(src_start_us, actual_duration),
        )
        self.script.add_segment(seg, track_name)
        return seg

    def add_cloud_media(
        self,
        query: str,
        start_time: Union[str, int] = None,
        duration: Union[str, int] = None,
        track_name: str = None,
    ):
        cm = self.cloud_manager
        local_path = cm.download_asset(query)
        if not local_path:
            return None

        asset_info = cm.find_asset(query)
        db_type = str(asset_info.get("type", "")).lower() if asset_info else ""
        source_db = str(asset_info.get("source_db", "")).lower() if asset_info else ""
        is_audio_db = source_db in {"cloud_music_library.csv", "cloud_sound_effects.csv"}
        is_audio_type = any(
            k in db_type for k in ["music", "audio", "sound", "bgm", "音效", "歌曲", "歌"]
        )
        is_audio = is_audio_db or is_audio_type

        if is_audio:
            default_track = (
                "BGM"
                if source_db == "cloud_music_library.csv"
                or any(k in db_type for k in ["music", "bgm", "歌曲", "歌"])
                else "AudioTrack"
            )
            return self.add_audio_safe(
                local_path, start_time, duration, track_name or default_track
            )
        return self.add_media_safe(local_path, start_time, duration, track_name or "VideoTrack")

    def add_cloud_music(
        self,
        query: str,
        start_time: Union[str, int] = None,
        duration: Union[str, int] = None,
        name: str = None,
        duration_s: float = None,
        track_name: str = "BGM",
    ):
        """
        通过 Cloud ID 添加云端音乐。直接注入 Material ID 补丁。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)

        # 仅使用真实下载的本地缓存文件。虚拟路径（如 cloud_music_xxx.mp3）在磁盘上
        # 并不存在，会直接触发剪映“检测到媒体丢失”。下载失败时直接报错返回。
        local_path = self.cloud_manager.download_asset(query)
        if not local_path or not os.path.exists(local_path):
            print(f"❌ Cloud music download failed: '{query}'. Aborted to avoid media-missing error.")
            return None

        return self.add_audio_safe(
            local_path, start_time=start_time, duration=duration, track_name=track_name
        )

    def _find_available_audio_track_name(self, base_track_name: str, segment) -> str:
        preferred = base_track_name or "AudioTrack"
        if self._track_accepts_segment(preferred, segment):
            return preferred

        index = 1
        while True:
            candidate = f"{preferred}_{index}"
            self._ensure_track(draft.TrackType.audio, candidate)
            if self._track_accepts_segment(candidate, segment):
                return candidate
            index += 1

    def _track_accepts_segment(self, track_name: str, segment) -> bool:
        track = self.script.tracks.get(track_name)
        if track is None:
            return False
        try:
            for existing in track.segments:
                if existing.overlaps(segment):
                    return False
            return True
        except SegmentOverlap:
            return False

    def _ensure_track(self, track_type, track_name, relative_index=None):
        """确保轨道存在，不存在则创建。

        同类型轨道若共用同一个 relative_index，render_index 会完全相同，
        剪映里的图层遮挡顺序就变得不确定；故默认按已有同类型轨道数递增分层。
        """
        if not track_name:
            return
        if track_name in self.script.tracks:
            return
        if relative_index is None:
            relative_index = sum(
                1 for t in self.script.tracks.values() if t.track_type == track_type
            )
        self.script.add_track(track_type, track_name, relative_index=relative_index)

    def _calculate_duration(self, req_dur, phys_dur_available):
        """计算实际应用时长，带容错。"""
        if req_dur:
            req_us = safe_tim(req_dur)
            return min(req_us, phys_dur_available) if phys_dur_available > 0 else req_us
        return phys_dur_available

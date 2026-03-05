import os
import uuid
from typing import Union
import pyJianYingDraft as draft
from pyJianYingDraft import trange
from utils.formatters import safe_tim, get_duration_ffprobe_cached, tim
from utils.media_normalizer import normalize_webm_for_jianying

class MediaOpsMixin:
    """
    JyProject 的媒体处理 Mixin。
    """
    def add_media_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                       track_name: str = None, source_start: Union[str, int] = 0, **kwargs):
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

        if ext in [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"]:
            return self.add_audio_safe(media_path, start_time, duration, track_name or "AudioTrack")
        
        return self._add_video_safe(media_path, start_time, duration, track_name or "VideoTrack", source_start=source_start)

    def add_audio_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                       track_name: str = "AudioTrack", **kwargs):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.audio, track_name)
        
        try:
            mat = draft.AudioMaterial(media_path)
            phys_duration = mat.duration
        except Exception:
            return None
            
        start_us = safe_tim(start_time)
        actual_duration = self._calculate_duration(duration, phys_duration)
        
        seg = draft.AudioSegment(mat, trange(start_us, actual_duration), source_timerange=trange(0, actual_duration))
        self.script.add_segment(seg, track_name)
        return seg

    def _add_video_safe(self, media_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = None, 
                        track_name: str = "VideoTrack", source_start: Union[str, int] = 0, **kwargs):
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

        seg = draft.VideoSegment(mat, trange(start_us, actual_duration), source_timerange=trange(src_start_us, actual_duration))
        self.script.add_segment(seg, track_name)
        return seg

    def add_cloud_media(self, query: str, start_time: Union[str, int] = None, 
                       duration: Union[str, int] = None, track_name: str = None):
        cm = self.cloud_manager
        local_path = cm.download_asset(query)
        if not local_path: return None
        
        asset_info = cm.find_asset(query)
        db_type = str(asset_info.get("type", "")).lower() if asset_info else ""
        source_db = str(asset_info.get("source_db", "")).lower() if asset_info else ""
        is_audio_db = source_db in {"cloud_music_library.csv", "cloud_sound_effects.csv"}
        is_audio_type = any(k in db_type for k in ["music", "audio", "sound", "bgm", "音效", "歌曲", "歌"])
        is_audio = is_audio_db or is_audio_type
        
        if is_audio:
            return self.add_audio_safe(local_path, start_time, duration, track_name or "AudioTrack")
        return self.add_media_safe(local_path, start_time, duration, track_name or "VideoTrack")

    def add_cloud_music(self, query: str, start_time: Union[str, int] = None, 
                        duration: Union[str, int] = None, name: str = None, duration_s: float = None, 
                        track_name: str = "AudioTrack"):
        """
        通过 Cloud ID 添加云端音乐。直接注入 Material ID 补丁。
        """
        if start_time is None:
            start_time = self.get_track_duration(track_name)

        # 优先使用真实本地缓存文件，避免生成虚拟路径导致“媒体丢失”提示。
        # 若下载失败，再回退到旧的 mock 注入模式。
        local_path = self.cloud_manager.download_asset(query)
        if local_path and os.path.exists(local_path):
            seg = self.add_audio_safe(local_path, start_time=start_time, duration=duration, track_name=track_name)
            if seg is not None:
                return seg
             
        # 1. 如果没给 duration_s，尝试查表
        actual_duration_s = duration_s
        if not actual_duration_s:
            actual_duration_s = self.cloud_manager.get_asset_duration(query)
            
        if not actual_duration_s:
            print(f"⚠️ Warning: Duration for cloud music '{query}' not found. Using fallback 3.0s")
            actual_duration_s = 3.0
            
        final_dur_us = safe_tim(duration) if duration else int(actual_duration_s * 1000000)
        
        # 2. 注入 Patch
        dummy_path = local_path if (local_path and os.path.exists(local_path)) else f"cloud_music_{query}.mp3"
        self._cloud_audio_patches[dummy_path] = {"id": query, "type": "music"}
        
        # 3. 使用 Mock 素材
        from core.mocking_ops import MockAudioMaterial
        mat = MockAudioMaterial(query, final_dur_us, name or f"CloudMusic_{query}", dummy_path)
        seg = draft.AudioSegment(mat, draft.Timerange(safe_tim(start_time), final_dur_us), source_timerange=draft.Timerange(0, final_dur_us))
        
        self._ensure_track(draft.TrackType.audio, track_name)
        self.script.add_segment(seg, track_name)
        return seg

    def _ensure_track(self, track_type, track_name):
        """确保轨道存在，不存在则创建。"""
        if not track_name: return
        if track_name not in self.script.tracks:
            self.script.add_track(track_type, track_name)

    def _calculate_duration(self, req_dur, phys_dur_available):
        """计算实际应用时长，带容错。"""
        if req_dur:
            req_us = safe_tim(req_dur)
            return min(req_us, phys_dur_available) if phys_dur_available > 0 else req_us
        return phys_dur_available

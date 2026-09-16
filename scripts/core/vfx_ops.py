import os
import time
from typing import Union, Optional
import pyJianYingDraft as draft
from utils.formatters import safe_tim, tim

class VfxOpsMixin:
    """
    JyProject 的特效与转场 Mixin。
    """
    def add_effect_simple(self, effect_name: str, start_time: Union[str, int] = None, duration: Union[str, int] = "3s", track_name: str = "EffectTrack"):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.effect, track_name)
        
        eff_type = self._resolve_enum(draft.VideoSceneEffectType, effect_name)
        if not eff_type: return None
        
        seg = draft.EffectSegment(eff_type, draft.Timerange(safe_tim(start_time), safe_tim(duration)))
        self.script.add_segment(seg, track_name)
        return seg

    def add_picture_fade(
        self,
        video_segment: draft.VideoSegment,
        in_duration: Union[str, int] = 0,
        out_duration: Union[str, int] = 0,
    ) -> Optional[draft.VideoSegment]:
        """为视频片段添加**画面**淡入淡出。

        底层 `VideoSegment.add_fade()` 只写音频淡化（落入 `materials.audio_fades`），
        画面不受影响；画面淡化须由 alpha 关键帧完成，故单独提供本方法。
        两条视频轨重叠时，对上层片段调用本方法即可得到交叉溶解。
        """
        if video_segment is None:
            return None

        fade_in = safe_tim(in_duration)
        fade_out = safe_tim(out_duration)
        duration = video_segment.duration
        if fade_in + fade_out > duration:
            print(f"⚠️ 淡化时长 {(fade_in + fade_out) / 1e6:.2f}s 超过片段长度，已跳过")
            return video_segment

        alpha = draft.KeyframeProperty.alpha
        if fade_in > 0:
            video_segment.add_keyframe(alpha, 0, 0.0)
            video_segment.add_keyframe(alpha, fade_in, 1.0)
        if fade_out > 0:
            video_segment.add_keyframe(alpha, duration - fade_out, 1.0)
            video_segment.add_keyframe(alpha, duration, 0.0)
        return video_segment

    def add_transition_simple(
        self,
        transition_name: str,
        video_segment: Optional[draft.VideoSegment] = None,
        duration: Union[str, int] = "1s",
        track_name: Optional[str] = None,
    ):
        # 兼容调用：如果未直接给 segment，则尝试从指定轨道获取最后一个视频片段
        if video_segment is None and track_name:
            track = self.script.tracks.get(track_name)
            if not track or not getattr(track, "segments", None):
                return None
            video_segment = track.segments[-1]

        if video_segment is None:
            return None

        trans_type = self._resolve_enum(draft.TransitionType, transition_name)
        if not trans_type: return None
        
        video_segment.add_transition(trans_type, duration=duration)
        return video_segment.transition

    def add_web_asset_safe(self, html_path: str, start_time: Union[str, int] = None, duration: Union[str, int] = "5s", 
                           track_name: str = "WebVfxTrack", output_dir: Optional[str] = None):
        from web_recorder import record_web_animation
        
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        if output_dir is None:
            output_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(output_dir, exist_ok=True)
        
        video_output = os.path.join(output_dir, f"web_vfx_{int(time.time())}.webm")
        if record_web_animation(html_path, video_output, max_duration=safe_tim(duration)/1e6 + 5):
            return self.add_media_safe(video_output, start_time, duration, track_name=track_name)
        return None

import os
import re
import asyncio
import threading
from typing import Union
import pyJianYingDraft as draft
from utils.formatters import safe_tim, tim

class TextOpsMixin:
    """
    JyProject 的文本与字幕 Mixin。
    """
    def add_text_simple(self, text: str, start_time: Union[str, int] = None, duration: Union[str, int] = "3s", 
                        track_name: str = "Subtitles", **kwargs):
        if start_time is None:
            start_time = self.get_track_duration(track_name)
        self._ensure_track(draft.TrackType.text, track_name)
        
        start_us = safe_tim(start_time)
        dur_us = safe_tim(duration)

        # 兼容高层参数：动画参数不透传给 TextSegment，避免底层 __init__ 报 unexpected kw。
        anim_in = kwargs.pop("anim_in", None)
        anim_out = kwargs.pop("anim_out", None)
        anim_loop = kwargs.pop("anim_loop", None)
        anim_in_duration = kwargs.pop("anim_in_duration", None)
        anim_out_duration = kwargs.pop("anim_out_duration", None)
        anim_loop_duration = kwargs.pop("anim_loop_duration", None)

        # 仅透传 TextSegment 支持的字段
        allowed_keys = {"font", "style", "clip_settings", "border", "background", "shadow"}
        text_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}

        seg = draft.TextSegment(text, draft.Timerange(start_us, dur_us), **text_kwargs)

        # 为动画名称做同义词+模糊解析，支持如 "Typewriter" -> "复古打字机"
        if anim_in:
            intro_enum = self._resolve_enum(draft.TextIntro, str(anim_in))
            if intro_enum:
                seg.add_animation(intro_enum, duration=anim_in_duration)
        if anim_out:
            outro_enum = self._resolve_enum(draft.TextOutro, str(anim_out))
            if outro_enum:
                seg.add_animation(outro_enum, duration=anim_out_duration)
        if anim_loop:
            loop_enum = self._resolve_enum(draft.TextLoopAnim, str(anim_loop))
            if loop_enum:
                seg.add_animation(loop_enum, duration=anim_loop_duration)

        self.script.add_segment(seg, track_name)
        return seg

    def add_narrated_subtitles(self, text: str, speaker: str = "zh_female_xiaopengyou", 
                              start_time: Union[str, int] = None, track_name: str = "Subtitles"):
        if start_time is None: start_time = self.get_track_duration(track_name)
        curr_us = safe_tim(start_time)
        
        parts = [p for p in re.split(r'([，。！？、\n\r]+)', text) if p.strip()]
        sentences = []
        for i in range(0, len(parts), 2):
            s = parts[i]
            if i + 1 < len(parts): s += parts[i+1]
            sentences.append(s.strip())

        for s in sentences:
            clean_text = s.rstrip('，。！？、\n\r ')
            if not clean_text: continue
            
            audio_seg = self.add_tts_intelligent(clean_text, speaker=speaker, start_time=curr_us)
            if audio_seg:
                actual_dur_us = audio_seg.target_timerange.duration
                # 默认设置为屏幕底部 (transform_y=-0.8)
                clip_settings = draft.ClipSettings(transform_y=-0.8)
                self.add_text_simple(clean_text, start_time=curr_us, duration=actual_dur_us, 
                                    track_name=track_name, clip_settings=clip_settings)
                curr_us += actual_dur_us + 100000 
        return curr_us

    def add_tts_intelligent(self, text: str, speaker: str = "zh_male_huoli", start_time: Union[str, int] = None, track_name: str = "AudioTrack"):
        from universal_tts import generate_voice
        import uuid
        
        if start_time is None:
            start_time = self.get_track_duration(track_name)
            
        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        output_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex[:8]}.ogg")

        async def _generate():
            return await generate_voice(text, output_file, speaker)

        try:
            asyncio.get_running_loop()
            loop_running = True
        except Exception:
            loop_running = False

        if loop_running:
            box = {"path": None, "err": None}

            def _worker():
                try:
                    box["path"] = asyncio.run(_generate())
                except Exception as e:
                    box["err"] = e

            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            t.join()
            if box["err"] is not None:
                raise box["err"]
            actual_path = box["path"]
        else:
            actual_path = asyncio.run(_generate())

        if not actual_path: return None
        return self.add_media_safe(actual_path, start_time, track_name=track_name)

    async def add_tts_intelligent_async(
        self,
        text: str,
        speaker: str = "zh_male_huoli",
        start_time: Union[str, int] = None,
        track_name: str = "AudioTrack",
    ):
        from universal_tts import generate_voice
        import uuid

        if start_time is None:
            start_time = self.get_track_duration(track_name)

        temp_dir = os.path.join(self.root, self.name, "temp_assets")
        os.makedirs(temp_dir, exist_ok=True)
        output_file = os.path.join(temp_dir, f"tts_{uuid.uuid4().hex[:8]}.ogg")
        actual_path = await generate_voice(text, output_file, speaker)
        if not actual_path:
            return None
        return self.add_media_safe(actual_path, start_time, track_name=track_name)

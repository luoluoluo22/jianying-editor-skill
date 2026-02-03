---
name: audio-voice-generative
description: Rules for generating TTS voiceover and sourcing/downloading background music.
metadata:
  tags: tts, voiceover, bgm, audio, download, edge-tts
---

# Audio & Voice Generative Rules

Use these rules to provide a rich auditory experience, including AI narration and appropriate background music.

## 1. Text-to-Speech (TTS)
Always use `edge-tts` for high-quality, natural-sounding voiceovers.

### Workflow:
1.  **Generate Audio**: Create a temporary Python script or use the `edge-tts` CLI.
    *   Synthesizer: `edge-tts`
    *   Voice: `zh-CN-XiaoxiaoNeural` (standard) or `zh-CN-YunxiNeural` (energetic).
2.  **Import to Project**: Use `project.add_audio_safe()`.
3.  **Syncing**: Use `ffprobe` to get the exact duration of the generated `.mp3` to ensure perfect timing with visual clips.

```python
# Implementation Example
import asyncio
import edge_tts
async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(output_path)
```

## 2. JianYing Internal BGM (Native Integration)
This is the **preferred** way to use BGM.
- **Workflow**: 
    1. AI tells User: "Please search and play [Music Name] in JianYing once."
    2. AI/User runs: `python scripts/sync_jy_assets.py` to index the cache.
    3. AI uses `asset_search.py` (checks `jy_cached_audio.csv`) to get local path.

## 3. Web Sourcing (Fallback)
If native assets are missing after sync, source royalty-free music from the web.

### Sourcing Strategy:
1.  **Search**: Use `search_web` to find direct MP3 links from royalty-free sites.
2.  **Download**: Use `curl.exe -L -o bgm.mp3 "{URL}"`.
3.  **Looping**: Specified in `add_audio_safe(duration=...)`.

## 3. Subtitle Syncing (TTS to Text)
When adding TTS, you MUST add corresponding subtitles.
- **Track**: Place subtitles on a track named "Subtitles".
- **Position**: Set `transform_y=-0.8`.
- **Timing**: The start time and duration of the text clip MUST match the TTS audio segment exactly.

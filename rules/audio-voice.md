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
This is the **preferred** way to use BGM to ensure copyright compliance and quality.

### 🛠️ 用户端操作流程 (User Guide):
1.  **找歌**：在剪映专业版左上角点击“音频”，在搜索框输入关键词（如“科技”、“Vlog”）。
2.  **缓存**：**点击播放**你心仪的音乐。这一步至关重要，它能将音乐下载到本地缓存。
3.  **同步**：告诉 AI “同步剪映音乐”，AI 会运行 `python scripts/sync_jy_assets.py`。
4.  **使用**：AI 现在可以通过 `identifier`（通常是歌名或 ID）在本地 `jy_cached_audio.csv` 中找到物理路径并添加。

### 🤖 AI 指引策略:
- **优先检索**：AI 应同时检索 `data/jy_cached_audio.csv` (本地资产) 和 `data/cloud_music_library.csv` (云端索引)。
- **引导逻辑**：
    1.  **命中云端索引 (`cloud_music_library.csv`)**：AI 应回复：“我在云端库中发现了这首歌！我会为你生成草稿，生成完毕之后你需要进入草稿中点击一次同步。”
    2.  **完全未命中**：AI 应回复：“我没找到这种风格。请在剪映里找到喜欢的音乐并**添加到任意草稿轨道**，然后告诉我‘扫描音乐’，我会将其录入库中供以后直接调用。”

## 3. 音乐库文件说明 (Data Context)
- `data/jy_cached_audio.csv`: **核心资产**。包含已同步到 Skill 目录的物理文件路径。
- `data/cloud_music_library.csv`: **增强索引**。包含从历史工程中扫描到的 `music_id` 和分类。用于在用户通过关键词搜索时提供候选建议。

### 云端音乐 API
当音乐仅在云端索引中（无本地缓存）时，使用 `add_cloud_music` 方法：
```python
project.add_cloud_music(
    music_id="7377843352954243081",
    name="商务宣传 科技 产品展示",
    duration_s=25,     # 裁剪到所需时长
    start_time="0s",
    track_name="BGM"
)
```
生成后用户需进入剪映草稿点击同步下载音乐文件。

## 4. Web Sourcing (Fallback)
If native assets are missing after sync, source royalty-free music from the web.

### Sourcing Strategy:
1.  **Search**: Use `search_web` to find direct MP3 links from royalty-free sites.
2.  **Download**: Use `curl.exe -L -o bgm.mp3 "{URL}"`.
3.  **Looping**: Specified in `add_audio_safe(duration=...)`.

## 5. Subtitle Syncing (TTS to Text)
When adding TTS, you MUST add corresponding subtitles.
- **Track**: Place subtitles on a track named "Subtitles".
- **Position**: Set `transform_y=-0.8`.
- **Timing**: The start time and duration of the text clip MUST match the TTS audio segment exactly.

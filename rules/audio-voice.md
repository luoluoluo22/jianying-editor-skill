---
name: audio-voice-generative
description: Rules for generating TTS voiceover and sourcing/downloading background music.
metadata:
  tags: tts, voiceover, bgm, audio, download, edge-tts
---

# Audio & Voice Generative Rules

Use these rules to provide a rich auditory experience, including AI narration and appropriate background music.

## 1. Text-to-Speech (TTS)
优先使用智配音接口 `project.add_tts_intelligent()`。它具备以下超能力：
- **剪映直连**：优先使用剪映 SAMI 引擎（高质量、丰富剪映独家音色）。
- **零配置**：自动嗅探本地剪映 `device_id` 和 `iid`，无需抓包。
- **自动兜底**：若剪映网络不通，自动回退到微软 `edge-tts`。
- **简化流程**：一行代码完成“生成、测量、导入”全过程。

### 推荐音色 (Speaker IDs):
- **阳光/活力**: `zh_male_huoli` (默认)
- **小孩**: `zh_female_xiaopengyou`
- **熊二**: `zh_male_xionger_stream_gpu`
- **成熟女性**: `zh_female_shunv`

### 使用方法:
```python
# 1. 简单生成
seg = project.add_tts_intelligent("你好，我是全自动剪辑助手。", speaker="zh_male_huoli")

# 2. 结合字幕 (音画同步)
text = "欢迎来到 AI 剪辑教程。"
duration = seg.target_timerange.duration / 1000000 # 获取精准音频时长
project.add_subtitles_auto_split(text, start_time=seg.target_timerange.start, duration=duration)
```

---

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
- `data/cloud_music_library.csv`: **云端音乐索引**。
- `data/cloud_sound_effects.csv`: **云端音效索引 (SFX)**。

### 音频云端 API
| 素材类型       | 检索文件                  | 使用方法                                |
| :------------- | :------------------------ | :-------------------------------------- |
| 背景音乐 (BGM) | `cloud_music_library.csv` | `project.add_cloud_music(music_id=...)` |
| 音乐音效 (SFX) | `cloud_sound_effects.csv` | `project.add_cloud_sfx(effect_id=...)`  |

### 背景音乐音量规范
> **[强制规则]** 当项目中同时存在 TTS 旁白和背景音乐时，**必须**将背景音乐的音量设置为 `volume=0.6`（即 60%），以确保人声清晰可辨。
> 在 `add_cloud_music` / `add_audio_safe` 返回的 segment 上设置：`seg.volume = 0.6`

#### 示例：添加云端音效
```python
project.add_cloud_sfx(
    effect_id="7135753343380606242",
    name="Windows 开机",
    duration_s=3.87,
    start_time="5s"
)
```
生成后用户需进入剪映草稿点击同步下载资源。

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

### 字幕内容规范 (Subtitle Content Rules)
> **[强制规则]** 为了保证移动端可读性：
> 1. **切分逻辑**：单段文案必须以中文符号（`，` 或 `。`）为界限进行物理切分，形成多条字幕。
> 2. **长度控制**：单条字幕字数**严禁超过 27 个视觉字符**（计分规则：中文字符 = 1, 英文字符/数字/半角符号 = 0.5）。
> 3. **默认样式**：字号默认为 `5`。
> 4. **禁止符号**：字幕内容中禁止出现中文句号 `。`，应以空格或切分替代。

### 时长估算参考 (Duration Estimation)
若使用剪映内部 TTS 且无法预先获取准确长度，建议参考以下“词频/停顿”模型进行预测，以防字幕重叠：
- **中文字符**：平均 `0.2s - 0.25s` / 字。
- **英文单词**：平均 `0.3s - 0.5s` / 词。
- **句末停顿**：逗号约 `0.3s`，句号/换行约 `0.6s - 1.0s`。
- **安全准则**：字幕总时长应略小于或等于配音时长，通过 `get_track_duration` 强制衔接以消除 Overlap。

---

---

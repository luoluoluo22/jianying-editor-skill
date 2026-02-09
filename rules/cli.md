---
name: cli-tools
description: Command line interface for diagnostics, draft management, and recording tools.
metadata:
  tags: cli, diagnostic, list_drafts, srt, recording
---

# CLI Tools & Diagnostics

The wrapper script `jy_wrapper.py` doubles as a powerful CLI tool for draft management, asset listing, and bulk operations.

## Wrapper CLI (jy_wrapper.py)

**Path Note**: The examples below use `<SKILL_ROOT>` as a placeholder. You must adjust this path based on your current environment/IDE:
- **Antigravity**: `.agent/skills/jianying-editor`
- **Trae**: `.trae/skills/jianying-editor`
- **Claude**: `.claude/skills/jianying-editor`
- **Global**: `~/.gemini/skills/jianying-editor`

### 1. Diagnostics & Info
```bash
# Check Jianying installation path and dependencies
python <SKILL_ROOT>/scripts/jy_wrapper.py check

# List all local Jianying drafts (sorted by modification time)
python <SKILL_ROOT>/scripts/jy_wrapper.py list-drafts

# List available Enum-based assets (animations, effects, transitions)
python <SKILL_ROOT>/scripts/jy_wrapper.py list-assets --type anim
```

### 2. Draft Management
```bash
# Quick Create a draft with one command
python <SKILL_ROOT>/scripts/jy_wrapper.py create --name "Test" --media "C:/video.mp4" --text "Demo"
```

### 3. SRT Subtitle Operations
```bash
# Export subtitles from a draft to an SRT file
# (Default output is to project root, preserving timeline)
python <SKILL_ROOT>/scripts/jy_wrapper.py export-srt --name "MyProject"

# Import SRT subtitles into a draft
# Matches Jianying's default subtitle style.
python <SKILL_ROOT>/scripts/jy_wrapper.py import-srt --name "MyProject" --srt "subs.srt"

# Optional arguments for import:
# --track "TrackName" : Specify a specific track
# --clear            : Remove existing text track before importing
```

## Recording Tool

The skill includes a GUI-based screen recorder for capturing user actions or tutorials.

```bash
# Launch the Recorder GUI
# Auto-names files by timestamp and captures audio + events.
python <SKILL_ROOT>/tools/recording/recorder.py
```
## AI 自动化全流程工具 (Transcribe & Match)

该工具支持从主视频/音频自动识别字幕，或直接利用已有 SRT 字幕，进行多源素材智能打标、语义对齐并组装剪映草稿。

```bash
# 场景 1：默认全流程 (视频输入)
python <SKILL_ROOT>/examples/video_transcribe_and_match.py \
    --video "主视频.mp4" \
    --materials "./素材文件夹"

# 场景 2：音频输入 (将音频作为主轨道)
# 脚本将自动填充 1080P 黑色背景
python <SKILL_ROOT>/examples/video_transcribe_and_match.py \
    --video "配音文件.mp3" \
    --materials "./素材库"

# 场景 3：纯字幕匹配 (不需要视频/音频，直接根据 SRT 给素材对齐)
python <SKILL_ROOT>/examples/video_transcribe_and_match.py \
    --srt "mysubs.srt" \
    --materials "./素材库" \
    --bg_image black
```

### 参数说明：
- `--video`: 主视频或主音频路径。提供此项时 AI 将自动完成语音转字幕。
- `--srt`: 直接提供现有的字幕文件。若提供此参数，将跳过字幕识别步骤。
- `--materials`: **(必填)** 素材来源，可传入多个文件夹或具体视频路径。
- `--project`: 导出的剪映工程名称。
- `--bg_image`: **(可选)** 指定背景。支持 `white`, `black` 或具体图片路径。
- `--clear_cache`: `True/False`。强制刷新 AI 处理缓存。
- `--limit`: 限制处理素材的数量。

### 智能背景逻辑：
当主轨道没有传入视频文件时，脚本将自动识别并执行以下逻辑：
1. 若指定了 `--bg_image`，使用指定颜色或图片。
2. 若未指定，则**默认添加黑色背景色块**，确保生成的工程在剪映中打开时不是空白。

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

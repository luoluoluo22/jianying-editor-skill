# API Reference

This document is the canonical API index for this skill.

## Python Wrapper (`JyProject`)

Bootstrap:

```python
import os
import sys
skill_root = os.getenv("JY_SKILL_ROOT", r"<SKILL_ROOT>")
sys.path.insert(0, os.path.join(skill_root, "scripts"))
from jy_wrapper import JyProject
```

### Constructor

```python
JyProject(project_name: str, width: int = 1920, height: int = 1080, drafts_root: str | None = None, overwrite: bool = True)
```

### Core Lifecycle

- `save()`: persist and patch draft content.
- `get_track_duration(track_name: str) -> int`: timeline end in microseconds.

### Media APIs

- `add_media_safe(media_path, start_time=None, duration=None, track_name=None, source_start=0, **kwargs)`
- `add_audio_safe(media_path, start_time=None, duration=None, track_name="AudioTrack", **kwargs)`
- `add_clip(media_path, source_start, duration, target_start=None, track_name="VideoTrack", **kwargs)`
- `add_cloud_media(query, start_time=None, duration=None, track_name=None)`
- `add_cloud_music(query, start_time=None, duration=None, name=None, duration_s=None)`

### Text / Voice APIs

- `add_text_simple(text, start_time=None, duration="3s", track_name="Subtitles", **kwargs)`
- `add_tts_intelligent(text, speaker="zh_male_huoli", start_time=None, track_name="AudioTrack")`
- `add_narrated_subtitles(text, speaker="zh_female_xiaopengyou", start_time=None, track_name="Subtitles")`

### VFX / Transition APIs

- `add_effect_simple(effect_name, start_time=None, duration="3s", track_name="EffectTrack")`
- `add_transition_simple(transition_name, video_segment=None, duration="1s", track_name=None)`
- `add_web_asset_safe(html_path, start_time=None, duration="5s", track_name="WebVfxTrack", output_dir=None)`

## Minimal End-to-End Example

```python
import os
import sys

skill_root = r"<SKILL_ROOT>"
sys.path.insert(0, os.path.join(skill_root, "scripts"))
from jy_wrapper import JyProject

project = JyProject("API_Demo", overwrite=True)
project.add_media_safe(os.path.join(skill_root, "assets", "video.mp4"), "0s", "5s", "VideoTrack")
bgm = project.add_cloud_media("7546546694282676275", "0s", "8s", "BGM_Track")
if bgm:
    bgm.volume = 0.6
project.add_narrated_subtitles("这是一个 API 文档示例。", start_time="0.5s")
project.save()
```

## CLI Contract

Common `--json` output:

```json
{
  "ok": true,
  "code": "ok",
  "reason": "",
  "data": {}
}
```

Exit codes:

- `0`: success
- `1`: runtime/infra failure
- `2`: invalid input or strict precondition failure

Key scripts:

- `scripts/api_validator.py`
- `scripts/asset_search.py`
- `scripts/build_cloud_music_library.py`
- `scripts/auto_exporter.py`
- `scripts/draft_inspector.py`

### Draft Inspector CLI

```bash
python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20
python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"
python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind content --json
```

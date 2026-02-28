---
name: media
description: Rules for importing video, audio, and image assets.
metadata:
  tags: media, video, audio, image, import
---

# Media Import

Use `project.add_media_safe()` to import assets. This method automatically detects asset type (Video/Image/Audio).

## API Signature

```python
def add_media_safe(self, file_path, start_time=None, duration=None, track_name=None):
    """
    Args:
        file_path (str): Absolute path to the asset file.
        start_time (str, optional): Timeline position (e.g., "0s"). 
                                   If None, appends to the end of the track (Smart Append).
        duration (str, optional): Duration override (recommended: "5s").
        track_name (str, optional): Logical name of the track.
    
    Returns:
        SegmentObject: The created segment instance.
    """
```

## Rules & Best Practices

1.  **Absolute Paths**: ALWAYS use absolute paths for `file_path`.
2.  **Audio**: You can also use `project.add_audio_safe(...)` which is an alias specifically for audio, ensuring it goes to an audio track.
3.  **Track Names**: Providing a `track_name` (e.g. "OverlapTrack") helps forcing media onto specific or new tracks, useful for Picture-in-Picture (PIP).
4.  **Return Value**: Capture the return value if you plan to add animations (Keyframes) to this clip.

## AI 视频分析优化 (AI Analysis Optimization)

在进行 AI 视频理解或分析（如 Gemini 视频模型）前，请遵循以下建议以提高效率和模型理解力：
- **最大时长**: 建议控制在 **30 分钟** 以内。
- **目标分辨率**: 建议压缩至 **360p**。这是 AI 理解的最佳平衡点（文件小且关键信息保留完整）。
- **预处理**: 若原始视频体积过大，必须先进行 **压缩** 后再传给 AI 分析，以避免上传超时或模型截断。

## 分辨率与比例 (Resolution & Ratio)

为了保证剪辑效果，**项目分辨率必须与主素材比例一致**：
- **横屏 (16:9)**: 创建项目时使用默认参数或显式指定 `width=1920, height=1080`。
- **竖屏 (9:16)**: 如果主视频是竖屏，创建项目时 **必须** 指定 `width=1080, height=1920`。
  ```python
  # 创建竖屏项目示例
  project = JyProject("竖屏短视频项目", width=1080, height=1920)
  ```
- **自动检测**: 建议在创建项目前，先用脚本或 AI 判断视频的原始比例，确保输出不带有黑边。


## Examples

```python
# Import main video
video_seg = project.add_media_safe(r"C:\assets\video.mp4", start_time="0s")

# Import BGM (Audio)
project.add_audio_safe(r"C:\assets\bgm.mp3", start_time="0s", track_name="BGM")

# Import PIP (Picture in Picture)
pip_seg = project.add_media_safe(r"C:\assets\facecam.mp4", start_time="5s", track_name="PipLayer")
```

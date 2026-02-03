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

## Examples

```python
# Import main video
video_seg = project.add_media_safe(r"C:\assets\video.mp4", start_time="0s")

# Import BGM (Audio)
project.add_audio_safe(r"C:\assets\bgm.mp3", start_time="0s", track_name="BGM")

# Import PIP (Picture in Picture)
pip_seg = project.add_media_safe(r"C:\assets\facecam.mp4", start_time="5s", track_name="PipLayer")
```

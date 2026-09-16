---
name: keyframes
description: Adding keyframe animations (Zoom, Position, Opacity) to media segments.
metadata:
  tags: keyframes, animation, pip, zoom, pan
---

# Keyframes & Animation

You can add keyframe animations to video or image segments (e.g., for Picture-in-Picture, Ken Burns effects, or custom zooms).

## Prerequisites

To use keyframes, you need to import `KeyframeProperty` from the underlying library:

```python
from pyJianYingDraft import KeyframeProperty as KP, Keyframe
```

## How to Add Keyframes

1.  **Capture the Segment**: The `add_media_safe` method returns the created segment object.
2.  **Add Keyframes**: Use the `.add_keyframe(property, timestamp, value)` method on the segment.

```python
# 1. Add media and capture the segment instance
start_time = 1000000  # 片段在时间线上的位置：1s (微秒)
segment = project.add_media_safe(
    os.path.expanduser("~/assets/image.png"), 
    start_time=start_time, 
    duration="4s"
)

if segment:
    # 2. 关键帧时间是【片段内的相对偏移】，不是时间线上的绝对时间。
    #    片段放在时间线 1s 处不影响这里的取值：片段开头永远是 0。
    t_start = 0
    t_end = 4000000  # 片段时长 4s 的末尾
    
    # 3. Add Keyframes
    
    # Example: Zoom In (Scale from 1.0 to 1.5)
    segment.add_keyframe(KP.uniform_scale, t_start, 1.0)
    segment.add_keyframe(KP.uniform_scale, t_end, 1.5)
    
    # Example: Fade Out (Opacity from 1.0 to 0.0)
    # segment.add_keyframe(KP.alpha, t_start, 1.0) # Check actual property name support
    
    # Example: Move X (Position)
    # Coordinates: 0.0 is center? (Verify with trial, usually normalized)
    segment.add_keyframe(KP.position_x, t_start, -0.5) # Left
    segment.add_keyframe(KP.position_x, t_end, 0.5)    # Right
    
    # Example: Smooth Zoom with Bezier (Easing)
    # Using presets: Keyframe.EASE_IN, Keyframe.EASE_OUT, Keyframe.EASE_IN_OUT
    segment.add_keyframe(KP.uniform_scale, t_start, 1.0, **Keyframe.EASE_IN_OUT)
    segment.add_keyframe(KP.uniform_scale, t_end, 2.0, **Keyframe.EASE_IN_OUT)
```

## Picture Fade (Cross-Dissolve)

画面淡入淡出**不能**用 `VideoSegment.add_fade()` —— 那个方法只写音频淡化（落入
`materials.audio_fades`），画面完全不受影响且不报错。用 wrapper 提供的 `add_picture_fade()`，
它内部写 `KP.alpha` 关键帧：

```python
seg = project.add_media_safe(clip, start_time, duration, track_name="B")
project.add_picture_fade(seg, "0.6s", "0.6s")   # 画面淡入 0.6s、淡出 0.6s
seg.add_fade("0.6s", "0.6s")                    # 如需声音也淡化，另外调这个
```

交叉溶解的做法：用两条视频轨交替承载片段（`script.add_track(..., relative_index=k)` 指定层级），
让相邻片段在时间上重叠，对**上层**片段调用 `add_picture_fade()`，下层靠遮挡与露出完成过渡。

注意 `add_picture_fade()` 的 `in/out_duration` 与 `add_keyframe()` 的 `time_offset` 都是
**片段内的相对偏移**，不是时间线绝对时间。

## Supported Properties (`KeyframeProperty`)

Common properties (verify via `dir(KP)` if unsure):
- `KP.uniform_scale` (Scaling)
- `KP.position_x` / `KP.position_y` (Position)
- `KP.rotation` (Rotation in degrees)
- `KP.alpha` (Opacity, if supported by version)

## Constraints
- **Time Origin**: `add_keyframe()` 的 `time_offset` 是**片段内的相对偏移**（片段开头 = 0），
  不是时间线绝对时间。按绝对时间传会让关键帧落到片段之外而静默失效。
- **Time Units**: 微秒整数（1 秒 = 1,000,000），也接受 `"1.5s"` 这类字符串（内部走 `tim()` 解析）。

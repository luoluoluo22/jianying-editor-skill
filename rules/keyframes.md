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
from pyJianYingDraft import KeyframeProperty as KP
```

## How to Add Keyframes

1.  **Capture the Segment**: The `add_media_safe` method returns the created segment object.
2.  **Add Keyframes**: Use the `.add_keyframe(property, timestamp, value)` method on the segment.

```python
# 1. Add media and capture the segment instance
# Note: start_time and duration must be known to calculate absolute keyframe times
start_time = 1000000  # 1s (in microseconds)
segment = project.add_media_safe(
    r"C:\assets\image.png", 
    start_time=start_time, 
    duration="4s"
)

if segment:
    # 2. Define keyframe times (Absolute Timeline Time in microseconds)
    t_start = start_time
    t_end = start_time + 4000000 # 1s + 4s = 5s
    
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
```

## Supported Properties (`KeyframeProperty`)

Common properties (verify via `dir(KP)` if unsure):
- `KP.uniform_scale` (Scaling)
- `KP.position_x` / `KP.position_y` (Position)
- `KP.rotation` (Rotation in degrees)
- `KP.alpha` (Opacity, if supported by version)

## Constraints
- **Time Units**: Keyframe timestamps MUST be in **microseconds** (1 second = 1,000,000 us). This differs from the "3s" string format used in high-level APIs. You currently must convert manually.

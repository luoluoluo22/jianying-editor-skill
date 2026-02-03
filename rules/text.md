---
name: text-subtitles
description: Rules for adding text, subtitles, and captions.
metadata:
  tags: text, subtitles, captions, font
---

# Text & Subtitles

Use `add_text_simple()` or `import_srt()` for text operations.

## Adding Simple Text

```python
project.add_text_simple(
    text_content="Hello World",
    start_time="0s",
    duration="3s",
    transform_y=-0.8,       # Vertical position: -1.0 (bottom) to 1.0 (top)
    font_size=12.0,         # Scale factor (approximate)
    color_rgb=(1, 1, 1),    # RGB tuple (0-1)
    style="default",        # Optional style preset
    bubble_id=None,         # Optional bubble asset ID
    anim_in=None            # Optional animation ID
)
```

### Constraints
- **Vertical Position (`transform_y`)**: 
    - `-0.8` is standard for subtitles.
    - `0.0` is centered.
    - `0.8` is for titles/headers.
- **Duration**: MUST be specified explicitly (e.g., `"3s"`).

## Auto-Layering (Anti-Collision)

If you add multiple text clips that overlap in time on the same logical track (e.g., all named "Subtitle"), the wrapper will **automatically** create new layers/tracks to prevent collision crashes. 
You do not need to manually calculate tracks for overlapping text.

## Importing SRT Subtitles

You can import a standard `.srt` file into the timeline.

```bash
# Verify using CLI first if needed
python .../jy_wrapper.py import-srt --name "Project" --srt "subs.srt"
```

Or in Python:
```python
# (Detailed API usage depends on implementation, typically handled via CLI wrapper or custom logic)
# If using jy_wrapper internal method:
project.import_srt(r"C:\path\to\subs.srt", track_name="Subtitles")
```

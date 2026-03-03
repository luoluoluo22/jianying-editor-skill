---
name: text-subtitles
description: Rules for adding text, subtitles, captions, and styled text (花字/Flower Text).
metadata:
  tags: text, subtitles, captions, font, styled-text, flower-text
---

# Text & Subtitles

Use `add_text_simple()` for plain text, `add_styled_text()` for styled flower text (花字), or `import_srt()` for SRT subtitles.

## 1. Plain Text (普通文字)

```python
project.add_text_simple(
    text="Hello World",
    start_time="0s",
    duration="3s",
    transform_y=-0.8,       # Vertical position: -1.0 (bottom) to 1.0 (top)
    font_size=12.0,         # Scale factor (approximate)
    color_rgb=(1, 1, 1),    # RGB tuple (0-1)
    anim_in=None            # Optional animation identifier (e.g. "打字机_I")
)
```

### Constraints
- **Vertical Position (`transform_y`)**:
    - `-0.8` is standard for subtitles.
    - `0.0` is centered.
    - `0.8` is for titles/headers.
- **Duration**: MUST be specified explicitly (e.g., `"3s"`).

## 2. Styled Text / Flower Text (花字)

When the user asks for **decorative text, styled text, flower text, or 花字**, use `add_styled_text()`.
This method applies a pre-cached visual effect style to the text, making it look like a professional title card with gradients, outlines, shadows, or animated appearances.

### Available Styles

Refer to `data/cloud_text_styles.csv` for the full list. Currently available local styles:

| style_id              | name_hint | Description                    |
| --------------------- | --------- | ------------------------------ |
| `7351316503771368713` | 红色花字1 | Red decorative style           |
| `7187739440347958589` | 红色花字2 | Red decorative style (variant) |
| `7127669365423508767` | 红色花字3 | Red decorative style (variant) |

### Usage

```python
project.add_styled_text(
    text="This is styled!",
    style_id="7351316503771368713",   # Pick from cloud_text_styles.csv
    start_time="5s",
    duration="3s",
    transform_y=-0.8                  # Position
)
```

### How It Works (Internal)
1. A plain `TextSegment` is created (same as `add_text_simple`).
2. On `project.save()`, the patching system injects the `effectStyle` (ID + local cache path) into the `draft_content.json`.
3. The local `artistEffect` resources are stored in `assets/artistEffect/<style_id>/`.
4. Jianying reads the effect prefab and renders the styled appearance.

### AI Decision Guide
- **User says "add subtitle / 字幕"** -> Use `add_text_simple()`.
- **User says "add flower text / 花字 / styled text / decorative title"** -> Use `add_styled_text()`.
- **User says "add text with effect"** -> Ask if they mean animation (use `anim_in` in `add_text_simple`) or visual style (use `add_styled_text`).

### Adding New Flower Text Styles
To add more styles:
1. In Jianying, add the desired 花字 to any draft project.
2. Run `python scripts/build_cloud_text_styles_library.py` to scan and index new style IDs.
3. Copy the `artistEffect/<style_id>` folder from Jianying cache to `assets/artistEffect/`.
4. Update `data/cloud_text_styles.csv` with the new ID and a descriptive name.

## 3. Auto-Layering (Anti-Collision)

If you add multiple text clips that overlap in time on the same logical track (e.g., all named "Subtitle"), the wrapper will **automatically** create new layers/tracks to prevent collision crashes.
You do not need to manually calculate tracks for overlapping text.

## 4. Importing SRT Subtitles

```python
project.import_srt(r"C:\path\to\subs.srt", track_name="Subtitles")
```

## Data Context
- `data/cloud_text_styles.csv`: Index of available flower text style IDs.
- `data/text_animations.csv`: Index of available text intro/outro animations.
- `assets/artistEffect/`: Local cache of flower text effect resources (prefab, shader, textures).

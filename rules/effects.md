---
name: effects`
description: Searching for and applying effects, filters, and transitions.
metadata:
  tags: effects, filters, transitions, search, asset_id
---

# Effects, Filters & Transitions

Jianying uses unique string IDs (e.g., `734521...`) for local assets. These IDs change or vary by version.
**You MUST NOT guess IDs.** You MUST search for them first.

## 1. Search for Asset IDs

Use the `asset_search.py` script to find the correct ID for a request.

```bash
# Syntax
python <SKILL_ROOT>/scripts/asset_search.py "<Keyword>" -c <Category>

# Categories (-c):
# - filters (滤镜)
# - video_scene_effects (画面特效)
# - transitions (转场)
# - text_animations (文字动画)

# Example: Search for "Glitch" effects
python <SKILL_ROOT>/scripts/asset_search.py "故障" -c video_scene_effects
# Output: [Found] Name: 故障_I, ID: 1234567...
```

## 2. Apply in Code

Once you have the ID, apply it using the wrapper.

*Note: The current `JyProject` wrapper exposes specific methods for effects. If a direct method like `add_effect(id)` is not explicitly documented in the wrapper, you may need to use `add_media_safe` if the effect is treated as a track item, or use advanced internal methods.*

**(Common Pattern for Transitions)**
Transitions are usually applied between clips. Current wrapper support for specific transition transitions on clips may vary. Check `jy_wrapper.py` for `add_transition` capability.

**(Common Pattern for Global Effects)**
Effects often sit on their own track above the main video.
```python
# Conceptual example - verify against jy_wrapper.py actual code if method exists
# project.add_effect("1234567", start_time="0s", duration="5s")
```

*Self-Correction*: If the `jy_wrapper.py` only supports basic media/text, use `asset_search` primarily to inform the user or configuration files. If `add_effect` is not present, request the user to add it manually or extend the wrapper.
*(Assuming `add_effect` or similar capability exists or is planned as part of the "Generative Editing" vision described in original SKILL.md)*

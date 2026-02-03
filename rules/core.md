---
name: core
description: Core JyProject operations including saving and exporting.
metadata:
  tags: core, save, export, save_project
---

# Core Operations

All operations are performed through the `JyProject` instance.

## Saving

You **MUST** call `project.save()` at the end of your script. 
This operation not only saves the JSON changes but also triggers a refresh in the Jianying UI (if applicable) or ensures the filesystem is synced.

```python
# Save changes and refresh draft state
project.save()
```

## Template Replacement (Mass Creation)

For scenarios where you have a "Template Draft" in Jianying and want to bulk-generate videos by swapping text content:

```python
# Use the internal script via JyProject or CLI
from scripts.template_replacer import replace_draft_text
replace_draft_text("MyTemplate", {"TITLE": "New Dynamic Title"})
```

## Automated Exporting

You can trigger a headless export (using `uiautomation`) without manual clicking:

```bash
# Using the CLI tool
python <SKILL_ROOT>/scripts/auto_exporter.py "ProjectName" "custom_output.mp4" --res 1080 --fps 60
```

## Constraints

- **Draft Recognition**: The wrapper automatically handles `DraftFolder` structure. Do not manually manipulate `draft_content.json` unless you know exactly what you are doing.
- **Exporting Requirements**: Auto-exporting only works on **Windows** with **Jianying v5.9 or lower**. It relies on `uiautomation` to interact with the UI.
- **UI Refresh**: After the script runs, if Jianying is open, the user may need to exit and re-enter the draft to see changes.

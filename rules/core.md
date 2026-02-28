---
name: core
description: Core JyProject operations including saving and exporting.
metadata:
  tags: core, save, export, save_project
---

# Core Operations

All operations are performed through the `JyProject` instance.

## 创建项目 (Project Creation)

在初始化 `JyProject` 时，请务必根据主视频素材的比例设置分辨率。**默认值为横屏 (1920x1080)**。

```python
# 默认：横屏 (16:9)
project = JyProject("Horizontal_Project") 

# 竖屏 (9:16)：必须在初始时指定，否则会有黑边
project = JyProject("Portrait_Project", width=1080, height=1920)
```


## Saving

You **MUST** call `project.save()` at the end of your script. 
This operation not only saves the JSON changes but also triggers a refresh in the Jianying UI (if applicable) or ensures the filesystem is synced.

```python
# Save changes and refresh draft state
project.save()
```

## Template-Based Production (Mass Creation)

For heavy-duty automation scenarios (e.g., creating 100 personalized ads from 1 template), follow the **Clone-First** strategy:

### 1. Secure Cloning
**CRITICAL**: Never modify the shared "Template Draft" directly. Always create a volatile copy.

```python
# Create a new draft copy based on an existing template
project = JyProject.from_template("Master_Template", "Target_Customer_A")
```

### 2. Semantic Slot Replacement
Use `replace_material_by_name` or `replace_material_by_path` to fill designated slots without breaking timberanges.

```python
# Swaps an asset by its name or original placeholder filename
project.replace_material_by_name("Intro_Slot", "C:/user/video.mp4")

# Useful for fixing broken links globally
project.reconnect_all_assets("D:/local_media_root")
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

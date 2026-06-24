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

### 2. Semantic Slot Replacement (Planned)
> **注意**：以下方法尚未实现，计划中。目前请手动编辑 `draft_content.json` 或使用 `JyProject.from_template()` 后重新添加素材。

```python
# [TODO] 这些 API 尚在开发中
# project.replace_material_by_name("Intro_Slot", "/path/to/video.mp4")
# project.reconnect_all_assets("/path/to/local_media_root")
```

## Automated Exporting

You can trigger a headless export (using `uiautomation`) without manual clicking:

```bash
# Using the CLI tool
python <SKILL_ROOT>/scripts/auto_exporter.py "ProjectName" "custom_output.mp4" --res 1080 --fps 60
```

## Constraints

- **Draft Recognition**: The wrapper automatically handles `DraftFolder` structure. Do not manually manipulate `draft_content.json` unless you know exactly what you are doing.
- **Exporting Requirements**: Auto-exporting via `uiautomation` 仅支持 **Windows**，剪映 5.9 或更低版本最稳。macOS 上请生成草稿后在剪映里手动导出。
- **UI Refresh**: After the script runs, if Jianying is open, the user may need to exit and re-enter the draft to see changes.

## Quick Edit Execution Template (Standard)

For generic requests like "来个剪辑", execute in this order:

1. Minimal environment checks (python + drafts root)
2. Resolve required assets (local first, cloud second)
3. Generate one deterministic edit script
4. Run script once and collect output
5. Perform acceptance checks and report concrete results

## Acceptance Checks (Standard)

After execution, verify:

- Draft directory exists
- Save completed (`project.save()` success)
- At least one segment exists on a video track
- BGM (if used) is on audio track
- Narration/subtitle pairing exists when TTS was requested

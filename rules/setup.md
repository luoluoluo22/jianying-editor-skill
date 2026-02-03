---
name: setup
description: Python script initialization and environment setup rules.
metadata:
  tags: setup, python, import, sys.path
---

# Environment Initialization

## 推荐方式：使用 `jy.py` 入口 (Recommended)

如果你的脚本在**项目根目录**或其子目录运行，只需一行代码：

```python
from jy import JyProject

project = JyProject("MyDraft")
project.add_media_safe(r"C:\video.mp4", "0s")
project.save()
```

**前提**：确保项目根目录有 `jy.py` 文件（已由 Skill 提供）。

### 额外导出

`jy.py` 还导出了以下常用变量：
- `SKILL_ROOT`: Skill 根目录路径
- `ASSETS_PATH`: 内置测试素材路径
- `get_skill_root()`: 获取 Skill 根目录的函数

---

## 备选方式：完整 Boilerplate

如果你的脚本不在项目根目录，或者 `jy.py` 不可用，请使用以下完整代码：

```python
import os
import sys

# Standard Boilerplate to load the skill wrapper
# -------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_candidates = [
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.join(current_dir, ".trae", "skills", "jianying-editor"),
    os.path.join(current_dir, ".claude", "skills", "jianying-editor"),
    os.path.join(current_dir, "skills", "jianying-editor"),
    os.path.join(current_dir, "jianying-editor-skill", ".agent", "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
    os.path.join(os.path.dirname(current_dir))  # For examples/ folder
]
wrapper_path = None
for p in skill_candidates:
    if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
        wrapper_path = os.path.join(p, "scripts")
        break

if wrapper_path and wrapper_path not in sys.path:
    sys.path.insert(0, wrapper_path)

try:
    from jy_wrapper import JyProject
except ImportError:
    print("❌ Critical Error: Could not load 'jy_wrapper'. Check skill paths.")
    sys.exit(1)
# -------------------------------------------------------------
```

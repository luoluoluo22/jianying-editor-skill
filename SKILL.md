---
name: jianying-editor
description: 使用 pyJianYingDraft 库自动化创建、编辑和管理剪映 (JianYing) 视频草稿。支持多轨道、动画、特效、关键帧、模板替换、自动导出以及启动录屏工具。
---

# JianYing Editor Skill

## 目标
将 `pyJianYingDraft` 库的所有能力封装为可直接调用的执行单元，实现从素材输入到视频导出的全链路自动化。

## 核心架构
本 Skill 包含完整的项目参考手册和核心逻辑脚本：
- **`references/`**: 包含项目的 `README.md` 和核心模块（`script_file.py`, `draft_folder.py`）的接口定义，供代理随时查阅 API。
- **`scripts/`**: 封装了常用的批处理任务（模板替换、自动导出）。
- **`tools/recording/`**: 专业录屏工具集，核心为 `recorder.py`，支持中文 GUI、音视频同步录制及用户操作轨迹采集（events.json）。
- **`assets/`**: 包含演示用的测试素材（assets/readme_assets/tutorial/ 下有 video.mp4, audio.mp3 等），Agent 在创建 Demo 时**必须**优先使用这些素材，而非生成纯文本草稿。

## 操作指南 (推荐使用 Wrapper)
在执行任务时，强烈推荐使用封装好的 `jy_wrapper` 来简化操作：

### 1. 引入 Wrapper
```python
import sys
import os
# 自动定位 Skill 路径并注入
skill_root = os.path.abspath(".agent/skills/jianying-editor")
sys.path.append(os.path.join(skill_root, "scripts"))
from jy_wrapper import JyProject
```

### 2. 标准工作流
```python
# 初始化 (自动探测路径 + 自动处理同名覆盖)
project = JyProject("MyAutoVideo")

# 添加媒体 (自动容错时长，自动创建轨道)
project.add_media_safe(r"C:\path\to\video.mp4", start_time="0s", duration="5s")

# 添加文本 (扁平化参数，自动映射动画)
project.add_text_simple("Hello Antigravity", start_time="1s", duration="3s", 
                        font_size=20.0, color_rgb=(1.0, 0.0, 0.0), anim_in="复古打字机")

# 保存
project.save()
```

## 关联手册说明
- **`references/AVAILABLE_ASSETS.md`**: 包含所有可用的动画、特效、转场的枚举名称列表 (供 AI 查阅)。
- `references/README.md`:  项目详细功能清单。
- `references/api_summary.txt`: 核心类参考。

## CLI 诊断与快速使用
Skill 的 Wrapper 脚本支持通过命令行进行诊断和草稿管理：
```bash
# 检查剪映路径和依赖 (会输出当前探测到的草稿目录)
python .agent/skills/jianying-editor/scripts/jy_wrapper.py check

# 列出用户当前的所有剪映草稿 (按时间排序)
python .agent/skills/jianying-editor/scripts/jy_wrapper.py list-drafts

# 列出可用的枚举资产 (动画、特效、转场)
python .agent/skills/jianying-editor/scripts/jy_wrapper.py list-assets --type anim

# 快速创建草稿
python .agent/skills/jianying-editor/scripts/jy_wrapper.py create --name "Test" --media "C:/video.mp4" --text "Demo"

# 导出字幕为 SRT (保留时间轴)
python .agent/skills/jianying-editor/scripts/jy_wrapper.py export-srt --name "MyProject" --output "subs.srt"

# 使用 GUI 录屏助手 (自动按时间戳命名，含声音和行为采集)
python .agent/skills/jianying-editor/tools/recording/recorder.py
```

## 约束提示
- **必须**使用 `DraftFolder` 以保证剪映能识别草稿。
- **UI 刷新**：生成后需提醒用户重启剪映或进出草稿以强制刷新。
- **导出限制**：自动导出功能仅支持剪映 V6 及以下版本。

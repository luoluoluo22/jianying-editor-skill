# JianYing Editor Skill for Antigravity
![封面图](assets/readme_assets/cover.png)

这是一个为 Google Antigravity 设计的专业级 Skill，旨在通过 AI 代理全自动生成、编辑和导出剪映（JianYing/CapCut 中国版）视频草稿。

## 🚀 Quick Start / 快速入门

### 1. Install skills
```bash
git clone https://github.com/luoluoluo22/jianying-editor-skill.git .agent/skills/jianying-editor
```

### 2. Use a skill in your AI assistant
```text
@jianying-editor 帮我用 assets 里的视频创建一个自动剪辑项目
```

---

## 🌟 核心特性

- **多轨管理**：支持视频、音频、文本、特效、滤镜等无限轨道叠加。
- **高级剪辑**：支持关键帧动画（透明度、坐标等）、倍速播放、蒙版（圆形、矩形等）。
- **自动化导出**：集成 `uiautomation` 逻辑，支持 1080P/4K 视频一键自动导出。
- **自带知识库**：封装了 `pyJianYingDraft` 全量源码参考，代理可直接通过查阅内部代码提供精准的 API 调用。
- **真实素材包**：Skill 内部携带演示专用的视频和音频资源。

## 📦 详细安装与配置

### 1. 依赖准备 (在本地 Python 环境中执行)
此 Skill 依赖于 `pyJianYingDraft` 及其核心组件：

```bash
pip install uiautomation
```

### 2. 配置剪映草稿路径
Skill 默认会在 **`SKILL.md`** 和脚本中使用标准路径：
`C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft`

如果您的剪映安装在其他位置，请在 Antigravity 提示配置时告知其正确的“草稿位置”。

## 📂 目录结构

- `SKILL.md`: 代理的“操作手册”和核心规约。
- `references/`: 包含 `pyJianYingDraft` 库的全量源代码副本，作为代理的离线查询文档。
- `scripts/`: 包含 `auto_exporter.py`（自动化导出）和 `template_replacer.py`（模板替换工具）。
- `tools/`: 包含录屏与行为记录工具集，支持音视频同步录制。
- `assets/`: 官方视频教程配套的各种演示素材。

## ⚠️ 注意事项

1. **刷新机制**：由于剪映不会实时监控文件系统变化，在生成草稿后，**请重启剪映或“进出一个旧草稿”**以刷新草稿列表。
2. **自动化导出**：目前自动导出脚本仅支持剪映 V6 及以下版本。运行导出时，请勿操作鼠标和键盘。推荐安装 **剪映 5.9 版本** 以获得最佳稳定性，详细理由及安装包获取可见此文：[剪映专业版 5.9.0 稳定版推荐](https://zhuanlan.zhihu.com/p/1951439646178402444)。

## � Update / 更新

当项目有新版本发布时（参考下方的更新日志），您可以使用以下命令更新 Skill：

```bash
# 进入 skill 目录并拉取最新代码
cd .agent/skills/jianying-editor
git pull
```

## �📅 更新日志 (Changelog)

### v1.2 (2026-01-27)
- **Smart Zoom 智能变焦**: 新增 `smart_zoomer.py`，支持基于操作录制的自动镜头推拉。
  - **动态跟随**: 当鼠标移出当前视野时，镜头会自动平滑跟随。
  - **交互反馈**: 自动在点击位置添加红圈标记。
  - **智能倒计时**: 鼠标移动会自动重置缩放停留时间，操作更流畅。
- **Recorder V3**: 录屏工具升级为 `recorder.py`。
  - 支持录制后一键调用 Wrapper 生成剪映草稿。
  - 自动管理录制文件到 `recordings/` 目录。
  - 修复了连续录制无需重启的问题。

---
Developed by Antigravity Agent Lab.

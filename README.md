# JianYing Editor Skill for Antigravity
![封面图](assets/cover.png)

### 📺 [点击观看 B 站保姆级安装教程](https://www.bilibili.com/video/BV1hLzCBzEDS/?vd_source=0eaa8407ec8edd1e9f2a0abf6e126bf6)

这是一个为 **AI Agent (Trae, Antigravity, Claude Code, Cursor)** 设计的通用专业级 Skill。它旨在赋予 AI“手眼”，使其能通过 Python 代码全自动生成、编辑和导出剪映（JianYing/CapCut 中国版）视频草稿。

不仅支持基础剪辑，更支持**网页动效生成 (Web-to-Video)** 和 **生成式 VFX**。

---

## 🚀 快速开始 (Quick Start)

### 1. 安装 Skill (Install)

请根据您使用的 AI 编辑器 (IDE)，选择对应的安装命令，以确保 Skill 能被自动识别：

**🤖 Antigravity / Gemini Code Assist:**
```bash
git clone https://github.com/luoluoluo22/jianying-editor-skill.git .agent/skills/jianying-editor
```

**🚀 Trae IDE:**
```bash
git clone https://github.com/luoluoluo22/jianying-editor-skill.git .trae/skills/jianying-editor
```

**🧠 Claude Code:**
```bash
git clone https://github.com/luoluoluo22/jianying-editor-skill.git .claude/skills/jianying-editor
```

**💻 Cursor / VSCode / 通用:**
```bash
# 通用方式：安装到根目录 include 列表
git clone https://github.com/luoluoluo22/jianying-editor-skill.git skills/jianying-editor
```

### 3. 🛠️ 资源下载与版本准备 (Essential Resources)
⚠️ **重要提示**：本 Skill 的自动导出功能深度依赖 **剪映 5.9** (或更低版本)。
新版本 (6.0+) 存在大量弹窗干扰，会导致自动化脚本失效。

⬇️ **[点击下载 剪映专业版 5.9 (夸克网盘)](https://pan.quark.cn/s/81566e9c6e08)**
*(下载后请覆盖安装或卸载旧版后安装)*

### 4. 🗣️ 试试这样问 AI (示例)

**🟢 基础：极简剪辑 (利用智能追加能力)**
> "来一个简单的剪辑"

**🟡 进阶：精准搜索与特效应用**
> "帮我把 `assets/` 里的视频导入剪映，配上背景音乐，最后加一个带打字机动画的标题‘我的第一支 Vlog’。"

**🟠 专业：软件教程录制 (录屏 + 智能缩放)**
> "我想录一段代码运行教程。请帮我启动录屏工具。"

**🔴 骨灰：影视解说全自动流水线（需安装antigravity-api-skill）**
> "分析视频 `assets/video.mp4` 制作 60 秒影视解说。"

**✨ 创意：网页动效合成 (Web-to-Video)**
> "帮我用网页写一个‘红心粒子爆炸’的动效，并导入到剪映。"

---

## 📦 环境准备 (必读)

为了让 Skill 正常工作，您需要在本地电脑上做一点点准备：

### 1. 安装 Python 依赖
此 Skill 的自动导出功能需要一个自动化库。请在终端运行：
```bash
pip install uiautomation
```

### 2. 确认剪映安装位置
Skill 默认认为您的剪映安装在 C 盘默认位置：
`C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft`

**如果您的剪映安装在 D 盘或其他位置**，请在使用时直接告诉 AI：
> "我的剪映草稿目录在 D:\JianyingPro\..."

## 📂 文件夹说明

- `SKILL.md`: 给 AI 看的说明书。
- `references/`: 剪映代码库的参考文档。
- `tools/recording/`: **录屏神器**，都在这里面。
- `assets/`: 演示用的测试视频和音乐。

## ⚠️ 常见问题 (FAQ)

1. **看不到新生成的草稿？**
   剪映软件不会实时刷新文件列表。生成草稿后，请**重启剪映**，或者随便点进一个旧草稿再退出来，就能看到新的了。

2. **自动导出失败？**
   自动导出脚本模拟了鼠标键盘操作。
   - 运行导出时，请**不要**动鼠标和键盘。
   - 目前仅支持 **剪映 5.9 或更早版本** (新版本弹窗太多容易干扰脚本)。

## 🔄 如何更新 (Update)

当有新功能发布时，您可以输入以下命令一键更新：

```bash
cd .agent/skills/jianying-editor
git pull
```

## 📅 更新日志 (Changelog)

### v1.3 (2026-02-03) - 突破二次元壁！
- **✨ 网页转视频 (Web-to-Video)**:
  - 核心突破！现在支持直接将 **HTML/Javascript/Canvas/SVG** 编写的网页动效实时录制并无缝导入剪映主轨道。
  - 集成 **Playwright 智能录屏引擎**，支持自动等待动画结束信号 (`window.animationFinished`)，产出高清无损素材。
  - 真正实现“代码即特效”，让前端动效库（如 Three.js, GSAP, Lottie）成为你的剪接素材库。

## 🌟 核心特性 (V3 进化版)

- **顶级素材接入**:
  - **banana (Imagen 3)**: 正式接入，支持一行指令生成 4K 电影级神兽/场景贴纸。
  - **Grok 3 (Media)**: 视觉天花板级图生视频，让你的静态素材瞬间化身史诗大片。
- **多轨管理**：支持视频、音频、字幕、贴纸、特效无限叠加，像专业剪辑师一样操作。
- **全自动闭环**: 从 Claude 4.5 剧本创作到素材生成，再到剪映草稿合成，一键全自动。
- **智能变焦**: 独家的 Smart Zoom 功能，能把普通的录屏自动变成“带镜头感”的演示视频。
- **网页转视频 (Web-to-Video)**: 完美支持 Canvas/JS 动效实时捕捉，让 Web 的无限创意瞬间化身视频 VFX 素材。
- **自动导出**：内置自动化脚本，支持一键导出 1080P/4K 视频，彻底解放双手。

### v1.2 (2026-01-27) - 像变魔术一样！
- **✨ 智能变焦 (Smart Zoom)**:
  - 录制的教程视频太平淡？现在，它会自动帮你把镜头**推进特写**到鼠标点击的地方，就像电影镜头一样酷！
  - **自动红圈**：鼠标点哪里，那里就自动出现小红圈，观众一眼就能看到重点。
  - **丝滑跟随**：鼠标移动时，画面会像摄像机云台一样平滑跟随，再也不怕画面太小看不清了。
- **🎥 录屏神器大升级**:
  - 录完就能**一键生成草稿**！不用手动打开剪映，不用导入素材，点一下按钮，草稿就躺在你的剪映里了。
  - 终于支持连续录制了，一口气录十段素材也不用重启软件。
  - 录像文件会自动整理好，不再乱丢在桌面。

---

# 剪映（jianying） Skill | AI 全自动用你的剪映替你剪辑
![封面图](assets/cover.png)

### [B 站介绍](https://www.bilibili.com/video/BV1hLzCBzEDS/?vd_source=0eaa8407ec8edd1e9f2a0abf6e126bf6)

这是一个能实现自动剪辑的 skill 项目。剪辑师只需用自然语言告诉 AI 你想做什么视频，它就能帮你完成从**写文案、配音、加字幕、选音乐、上特效到最终导出**的整套流程。


支持主流 AI 编辑器：Antigravity / Trae / Claude Code / Cursor。

## 平台支持状态（请先阅读）

草稿生成支持 Windows 和 macOS 的桌面版剪映专业版。自动导出属于额外 UI 自动化能力，目前仍以 Windows 老版本剪映为主。

| 平台 | 当前状态 | 说明 |
| --- | --- | --- |
| Windows | 推荐使用 | 支持草稿生成、素材导入、字幕、配音、云端素材下载、录屏和自动导出。自动导出依赖 Windows UI Automation，在剪映 5.9 或更低版本上最稳。 |
| macOS | 支持草稿生成 | 支持新版草稿目录探测、`draft_info.json` 草稿生成、FFmpeg 媒体解析兜底和录屏相关适配；自动导出不支持 macOS，需要在剪映里手动导出。 |
| CapCut 国际版 | 不支持 | 当前只适配国内版剪映专业版（JianyingPro），不要按本项目流程尝试 CapCut 国际版。 |
| 手机端剪映 | 不支持 | 仅面向桌面版草稿工程。 |

如果你是 Mac 用户，请把本项目用于自动搭建剪映时间轴；最终渲染导出在剪映内手动完成。

### 能做什么

| 功能                | 说明                                                   |
| ------------------- | ------------------------------------------------------ |
| **素材导入**        | 视频、音频、图片一句话丢进时间轴，自动排列             |
| **AI 配音**         | 输入文案自动生成语音，支持剪映原生音色和微软语音       |
| **字幕生成**        | 根据配音自动拆句、逐句对齐字幕，支持打字机等动画效果   |
| **自动配乐**        | 本地音乐或剪映素材库的云端音乐曲                       |
| **特效/转场/滤镜**  | 按名字搜索剪映自带的特效库，一句话应用                 |
| **网页动效转视频**  | 用 HTML/JS/Canvas 写动画，自动录屏变成视频素材导入剪映 |
| **录屏 + 智能变焦** | 录制屏幕操作，自动给鼠标点击位置加缩放和红圈标记       |
| **影视解说**        | AI 分析视频内容，自动生成分镜脚本并合成解说视频        |
| **自动导出**        | Windows UI 自动化导出 MP4，macOS 生成草稿后手动导出    |
| **关键帧动画**      | 缩放、位移、透明度等关键帧，做出运镜效果               |
| **复合片段**        | 像嵌套工程一样，把多个子项目组合成一个完整视频         |

### 做不到什么

- **不是剪映的替代品** -- 最终的视频渲染、预览回放还是靠剪映本身完成的，这个工具负责的是"自动帮你把时间轴搭好"，帮你点击导出
- **不能用剪映的实时特效** -- 像智能抠图、美颜、语音识别字幕这些需要剪映 GPU 实时处理的功能，目前无法通过代码调用
- **不能操作剪映的全部 UI 按钮** -- "一键成片""图文成片"这类剪映内置的 AI 功能暂时没法自动触发
- **自动导出依赖 Windows UI 自动化** -- 自动导出功能目前只支持 Windows；剪映 5.9 及以下版本最稳，新版本可能受弹窗或控件变化影响
- **Mac 端需要手动导出** -- macOS 支持生成草稿和导入素材，但不支持自动点击剪映导出
- **不支持手机端剪映 / CapCut 国际版** -- 只能配合国内版桌面剪映专业版使用

## 🚀 快速开始 (Quick Start)

### 1. 安装 Skill (Install)
建议优先使用 Windows 一键脚本，它会自动处理代码下载、目录结构和所有 Python 库。

**🔥 Windows 用户一键安装:**
在 PowerShell 中运行：
```powershell
irm is.gd/rpb65M | iex
```

**手动安装 (Git Clone):**

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

### 3. 🛠️ 版本准备 (Essential Resources)
草稿生成优先适配新版剪映的 `draft_info.json` 草稿结构。只有需要无人值守自动导出时，才建议准备 Windows + 剪映 5.9 或更低版本。

### 4. 试试这样跟 AI 说 (Use Cases)

详细的自然语言使用案例请参考：[**使用指南 (usage.md)**](usage.md)

**随便剪一个试试**
> "帮我随便剪一个视频看看效果"

**做个 Vlog**
> "把 D:\旅行素材 这个文件夹里的视频和照片帮我剪成一个 Vlog，配个轻快的音乐，加上标题'周末露营记'"

**写文案 + 配音 + 出片**
> "帮我写一段关于'秋天的第一杯奶茶'的短视频文案，配上温柔女声旁白和字幕，再找个温馨的 BGM"

**影视解说**
> "这个视频 D:\电影片段.mp4 ，帮我做一个 60 秒的影视解说"

**录个软件教程**
> "我要录一段操作教程，帮我启动录屏，录完自动导入剪映"


**做个炫酷的片头动画**
> "帮我用网页写一个星空粒子的片头动画，5 秒钟，然后导入到剪映里"

**字幕配画面**
> "我有一段旁白录音 旁白.mp3，帮我识别出字幕，然后从 F:\素材库 里自动挑画面配上去"

**用剪映曲库的音乐**
> "我想用剪映里那首'阳光旅途'当背景音乐"（可以通过脚本从历史工程中自动挖掘音乐 ID）

**多角色对话剪辑**
> "帮我剪一段两个人的对话，A 角色用成熟男声，B 角色用甜美女声，自动配上各自的字幕"

## 📦 环境准备 (必读)

为了让 Skill 正常工作，您还需要告知 AI 再做一点工作：

### 1. 安装 Python 依赖
请在终端运行以下命令以确保所有自动化功能正常工作：
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 初始化网页捕获环境 (Web-to-Video 功能必填)
playwright install chromium
```


Skill 默认会自动探测您的剪映安装位置，如果探测失败，请在使用时直接告诉 AI：

- **Windows**: `C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft`
- **macOS**: `/Users/你的用户名/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`

> "我的剪映草稿目录在 D:\JianyingPro\..."

> Mac 用户注意：如果你的剪映实际草稿目录不是上面的路径，请优先手动确认草稿目录。导出需要打开剪映手动完成。

## 📂 文件夹说明

- `SKILL.md`: 给 AI 看的说明书。
- `references/`: 参考文档与示例资料（非运行时依赖）。
- `scripts/vendor/`: 运行时内置依赖（如 `pyJianYingDraft`）。
- `tools/recording/`: **录屏神器**，都在这里面。
- `assets/`: 演示用的测试视频和音乐。

## ⚠️ 常见问题 (FAQ)

1. **看不到新生成的草稿？**
   剪映软件不会实时刷新文件列表。生成草稿后，请**重启剪映**，或者随便点进一个旧草稿再退出来，就能看到新的了。

2. **自动导出失败？**
   自动导出脚本模拟了鼠标键盘操作。
   - 运行导出时，请**不要**动鼠标和键盘。
   - 目前仅支持 **Windows**，剪映 5.9 或更早版本最稳。
   - macOS 不支持自动导出，请在剪映中手动导出。

## 🔄 如何更新 (Update)

当有新功能发布时，您可以输入以下命令一键更新：

```bash
cd .agent/skills/jianying-editor
git pull
```

## 📅 更新日志 (Changelog)

最新版本请直接查看 [CHANGELOG.md](CHANGELOG.md) 与 [VERSION](VERSION)。

### v1.6 (2026-06-24) - macOS 新版剪映草稿适配
- **macOS 草稿生成适配**:
  - 优先探测 `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft`。
  - 支持 `.agents/skills/jianying-editor` 安装路径。
  - `pymediainfo` 不可用时自动使用 `ffprobe` 解析视频/音频素材。
  - 自动导出入口在 macOS 上返回明确提示，避免误跑 Windows UI 自动化。

### v1.5 (2026-04-19) - macOS 初步适配与安全加固
- **macOS 初步适配**:
  - 优化了 macOS 下的路径探测逻辑，兼顾 Apple Silicon 和 Intel Mac。
  - 录屏与智能变焦功能接入 `avfoundation`。
- **🛡️ 安全与健壮性 (Security & Robustness)**:
  - **工程自修复 (Auto-healing)**：自动检测并修复损坏的或旧版的剪映工程文件。
  - **路径加固**：防止非法路径穿越，保护本地文件安全。
- **🎙️ 智能配音旁白 (Narrated Subtitles)**:
  - 核心接口 `add_narrated_subtitles`：一键完成“文案解析 -> 语音合成 -> 轨道对齐 -> 字幕生成”的全流程。
- **📚 云端素材库挖掘**:
  - 新增 `build_cloud_music_library.py`：自动挖掘您在剪映中曾经用过的所有云端音乐 ID，让 AI 也能调用剪映曲库。

### v1.4 (2026-02-09) - 全自动 AI 导演系统上线！
- **🧠 AI 语义素材匹配 (Semantic Footage Match)**:
  - **核心里程碑**：现在支持根据“视频画面内容、旁白音频、SRT 字幕”三位一体进行语义分析。AI 会自动理解每一句台词的含义，并从素材库中精准挑选最契合的画面进行剪辑（如说到“爆汁”自动对位流油特写）。


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
- **工程自修复**: 强大的 `Auto-healing` 机制，自动识别并修复由于版本冲突或异常关闭导致的损坏草稿。
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

## 打赏支持

如果这个项目对你有帮助，欢迎打赏支持。你的支持会直接转化为继续开发和维护的动力。
打赏后有问题请直接联系我微信：wxluoluoluo222

<table>
  <tr>
    <td align="center">
      <strong>支付宝</strong><br>
      <img src="docs/images/donate/alipay.jpg" alt="支付宝收款码" width="280">
    </td>
    <td align="center">
      <strong>微信</strong><br>
      <img src="docs/images/donate/wechat.png" alt="微信收款码" width="280">
    </td>
  </tr>
</table>

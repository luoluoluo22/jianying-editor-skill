---
name: generative-workflow
description: Thinking process for Generative Editing and AI Prompts.
metadata:
  tags: chain_of_thought, generative, logic, prompt
---

# Generative Editing Workflow

Do not just use templates. Think like an editor.

## Chain of Thought (CoT)

When a user gives a vague request (e.g., "Make it Cyberpunk"):

1.  **Deconstruct (拆解)**:
    *   Cyberpunk -> Neon Colors, Glitch effects, Fast Paced, Tech overlays.
2.  **Semantic Search (检索)**:
    *   Search for assets matching keywords using `asset_search.py`.
    *   e.g., `asset_search.py "glitch" -c video_scene_effects` -> ID: `88392...`
3.  **Compose (组合)**:
    *   Write the Python script using the found IDs and logic.

## 时间与精度 (Time & Precision)

在编写 AI 提示词（Prompt）要求模型输出时间轴时，请遵循以下规则：
- **首选单位**: **秒 (Seconds)**，使用浮点数格式（如 `12.5`）。
- **精度建议**: 建议保留 **2-3 位小数**（对应毫秒级）。这能确保 API 在将其转换为微秒时，能精准对齐到剪辑所需的帧刻度。
- **避免单位**: 不要让 AI 输出 HH:MM:SS 或帧数，这会增加解析错误的风险。

## AI Prompts

Use the specialized prompts located in the `prompts/` directory to generate content for the video.

### Movie Commentary / Viral Short Video
When the user wants to generate a "Movie Commentary" (影视解说) or a fast-paced viral summary from a long video file:

1.  **Read the Prompt**: Load `prompts/movie_commentary.md`.
2.  **媒体优化 (Optimize - CRITICAL)**: 确保视频针对 AI 进行优化：
    *   **最大时长**: 30 分钟。
    *   **目标分辨率**: 压缩至 360p（AI 理解的最佳平衡点）。
    *   **预处理**: 若视频过大，必须先进行压缩再传给 AI 分析。
3.  **Feed the LLM**: 将此提示词连同视频文件（如果支持多模态）或转录文本发送给视频理解模型（如 Gemini 1.5 Pro, GPT-4o）。

3.  **Parse JSON**: The output will be a JSON timeline.
4.  **Execute Script**: Use the logic in `references/movie_commentary_template.py` to:
    *   Cut the video according to `start` and `duration`.
    *   Add subtitles if `text` is present.
    *   **Auto-Masking**: Add a black mask at bottom for text segments to cover original hardsubs.
    *   **Highlight Track**: If `text` is empty (original audio), duplicate the clip to a "Highlight" track to preserve audio.

*Reference: `references/movie_commentary_template.py` contains the implementation.*

---
description: Prompt for generating a step-by-step video tutorial based on a project's README.md file.
variables:
  - README_CONTENT
  - PROJECT_NAME
  - PROJECT_REPO_URL
---

# Tutorial Video Generation (README to Video)

Your goal is to create a compelling, high-quality installation or usage tutorial video for a software project, based on its `README.md`.

## 1. Analyze the Context
Read the provided `README_CONTENT` carefully. Identify:
*   **Project Name**: The title of the tool.
*   **Target Audience**: Developers, designers, or general users?
*   **Key Value Proposition**: What problem does it solve?
*   **Installation Steps**: Extract the exact shell commands needed (e.g., `git clone`, `pip install`).
*   **Usage Examples**: Identify the "Hello World" or "Quick Start" code snippet.

## 2. Design the Storyboard (Visual & Audio)
Structure the video into 4 phases. DO NOT create a boring slideshow. Use the `Web-to-Video` technique (HTML/CSS animation) for a premium look.

*   **Phase 1: The Hook (0s - 3s)**
    *   **Visual**: Large, animated project title + slogan. Dynamic background (Aurora/Gradient).
    *   **Audio (TTS)**: "Welcome to [Project Name]. [Slogan/One-liner]."
*   **Phase 2: The Core Steps (3s - 20s)**
    *   **Visual**: A split-screen or card-based layout showing commands.
        *   Step 1: Get Code (`git clone ...`)
        *   Step 2: Dependencies (`pip install ...` or `npm install ...`)
        *   Step 3: Configuration (if any)
    *   **Audio (TTS)**: "Installation is simple. First, clone the repo... Next, install dependencies..."
*   **Phase 3: The Demo (Optional)**
    *   *If applicable, show a quick code snippet or usage example.*
*   **Phase 4: Call to Action (End)**
    *   **Visual**: Huge GitHub Link + "Star Us" text.
    *   **Audio (TTS)**: "Open source on GitHub. Start your journey today!"

## 3. Generate the Python Script
Write a Python script using `jianying-editor` skill (`jy_wrapper`) to build this video.
*   **Required Imports**: `from jy_wrapper import JyProject`, `edge_tts`.
*   **TTS Generation**: Use `edge_tts` to generate `intro.mp3`, `steps.mp3`, `outro.mp3` locally.
*   **Visual Generation**:
    *   Create a temporary HTML file with CSS animations (`@keyframes`) matching the storyboard.
    *   Use `project.add_web_asset_safe(html_path=..., ...)` to record it.
*   **Assembly**:
    *   Add BGM (use `sync_jy_assets.py` to check for local music first, or fall back to `tech_bgm.mp3`).
    *   layer TTS audio on `VoiceOver` track.
    *   layer HTML recording on `MainVideo` track.
    *   Add **Subtitles** using `add_text_simple` synchronized with the TTS audio duration.

## 4. Execution Rules
*   **Robustness**: Always assume the user doesn't have the BGM. Check `os.path.exists`.
*   **Style**: Use a Dark Mode aesthetic (Cyberpunk/Glassmorphism) for tech projects.
*   **Accuracy**: The commands shown in the video MUST match the README exactly.

---

**Input README**:
<README_CONTENT>
{{README_CONTENT}}
</README_CONTENT>

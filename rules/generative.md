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

## AI Prompts

Use the specialized prompts located in the `prompts/` directory to generate content for the video.

### Movie Commentary / Viral Short Video
When the user wants to generate a "Movie Commentary" (影视解说) or a fast-paced viral summary from a long video file:

1.  **Read the Prompt**: Load `prompts/movie_commentary.md`.
2.  **Feed the LLM**: Send this prompt along with the video file (if multimodal) or transcript to a Video Understanding Model (e.g., Gemini 1.5 Pro, GPT-4o).
3.  **Parse JSON**: The output will be a JSON timeline.
4.  **Execute Script**: Use the logic in `references/movie_commentary_template.py` to:
    *   Cut the video according to `start` and `duration`.
    *   Add subtitles if `text` is present.
    *   **Auto-Masking**: Add a black mask at bottom for text segments to cover original hardsubs.
    *   **Highlight Track**: If `text` is empty (original audio), duplicate the clip to a "Highlight" track to preserve audio.

*Reference: `references/movie_commentary_template.py` contains the implementation.*

---
name: web-vfx
description: Generating complex visual effects using Web technologies (HTML/JS/Canvas).
metadata:
  tags: web, vfx, html, javascript, playwright
---

# Web-to-Video VFX Engine

When Jianying's built-in effects are insufficient (e.g., for data viz, complex 3D, specific algorithms), use the Web VFX engine. This records a browser rendering into a transparent video.

## Usage

Use `project.add_web_asset_safe()` with a local HTML file path.

```python
html_code = """
<!DOCTYPE html>
<html>
<body>
<div class="box"></div>
<script src="https://cdn.../gsap.min.js"></script>
<script>
    // 1. Setup your animation
    gsap.to(".box", {
        x: 500, 
        duration: 2, 
        // 2. CRITICAL: Signal completion
        onComplete: () => window.animationFinished = true
    });
</script>
</body>
</html>
"""

html_path = os.path.join(temp_dir, "vfx_scene.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_code)

project.add_web_asset_safe(html_path=html_path, start_time="0s", duration="5s")
```

## The Animation Contract (IMPORTANT)

1.  **Signal Completion**: You **MUST** set `window.animationFinished = true;` when your animation is done. The recorder waits for this signal (timeout is usually 30s).
2.  **Transparency**: The recorder captures with a transparent background. Do not set a solid `body` background color unless intended.
3.  **Resolution**: Default is 1920x1080.
4.  **External Libs**: You can use CDNs (GSAP, Three.js, etc.).

## Recommended Libraries (CDNs)

Specifically tested and recommended for high-quality video generation:
- **GSAP**: The gold standard for web animations.
- **Three.js**: For complex 3D scenes and object rendering.
- **Chart.js / ECharts / D3.js**: Best for dynamic data visualization and animated charts.
- **Canvas API**: For custom particle systems and procedural effects.
- **Anime.js**: Lightweight alternative for CSS/SVG animations.

## When to use (User Intent Mapping)

Instead of just "vfx", think about these specific user scenarios:
- **Data Stories**: "Show a growing bar chart of the top 10 movies." (Chart.js/D3)
- **Tech Intros**: "Create a Matrix-style code rain intro for my coding channel." (Canvas)
- **UI Walkthroughs**: "Record a realistic macOS notification slide-in." (HTML/CSS)
- **Social Overlays**: "Add a glassmorphic 'Like & Subscribe' popup with a floating heart effect." (GSAP)
- **3D Product Showcases**: "Show a rotating 3D model of a GPU." (Three.js)

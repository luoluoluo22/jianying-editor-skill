---
name: web-vfx
description: Generating complex visual effects using Web technologies (HTML/JS/Canvas).
metadata:
  tags: web, vfx, html, javascript, playwright
---

# Web-to-Video VFX Engine

When Jianying's built-in effects are insufficient (e.g., for data viz, complex 3D, specific algorithms), use the Web VFX engine. This records a browser rendering into a transparent video.

## Usage

Use `project.add_web_code_vfx()` to inject HTML code that renders the effect.

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

project.add_web_code_vfx(html_code, start_time="0s", duration="5s")
```

## The Animation Contract (IMPORTANT)

1.  **Signal Completion**: You **MUST** set `window.animationFinished = true;` when your animation is done. The recorder waits for this signal (timeout is usually 30s).
2.  **Transparency**: The recorder captures with a transparent background. Do not set a solid `body` background color unless intended.
3.  **Resolution**: Default is 1920x1080.
4.  **External Libs**: You can use CDNs (GSAP, Three.js, etc.).

## When to use
- Dynamic charts (Chart.js, D3)
- Particle systems (Canvas confetti)
- 3D models (Three.js)
- Programmable typography

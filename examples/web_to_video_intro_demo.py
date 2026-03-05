import os

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Web VFX Intro</title>
  <style>
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #030915; }
    canvas { width: 100%; height: 100%; display: block; }
  </style>
</head>
<body>
  <canvas id="c"></canvas>
  <script>
    const canvas = document.getElementById("c");
    const ctx = canvas.getContext("2d");
    const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
    function resize() {
      canvas.width = Math.floor(window.innerWidth * dpr);
      canvas.height = Math.floor(window.innerHeight * dpr);
    }
    resize();
    window.addEventListener("resize", resize);

    const stars = Array.from({ length: 260 }, () => ({
      x: Math.random(), y: Math.random(), z: 0.2 + Math.random() * 0.8
    }));

    const start = performance.now();
    const durationMs = 5000;
    function draw(now) {
      const t = now - start;
      const w = canvas.width, h = canvas.height;
      ctx.fillStyle = "rgba(3,9,21,0.22)";
      ctx.fillRect(0, 0, w, h);
      for (const s of stars) {
        s.y += 0.0007 * s.z;
        if (s.y > 1.05) { s.y = -0.05; s.x = Math.random(); }
        const x = s.x * w;
        const y = s.y * h;
        const r = (1 + s.z * 2.4) * dpr;
        ctx.beginPath();
        ctx.fillStyle = "rgba(170,220,255,0.85)";
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      }
      const alpha = Math.max(0, 1 - t / durationMs);
      ctx.fillStyle = `rgba(220,240,255,${0.75 * alpha})`;
      ctx.font = `${Math.floor(46 * dpr)}px sans-serif`;
      ctx.textAlign = "center";
      ctx.fillText("STAR INTRO", w / 2, h * 0.52);
      if (t >= durationMs) {
        window.animationFinished = true;
        return;
      }
      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
  </script>
</body>
</html>
"""


def main() -> None:
    project = JyProject(project_name="Web_To_Video_Intro_Demo", overwrite=True)
    html_path = os.path.join(CURRENT_DIR, "__web_intro_demo.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)

    print("Recording web animation and importing to timeline...")
    seg = project.add_web_asset_safe(
        html_path=html_path,
        start_time="0s",
        duration="5s",
        track_name="VideoTrack",
    )
    if seg is None:
        raise RuntimeError("Web-to-Video import failed.")

    audio_path = os.path.join(SKILL_ROOT, "assets", "audio.mp3")
    if os.path.exists(audio_path):
        project.add_audio_safe(audio_path, start_time="0s", duration="5s", track_name="BGM_Track")

    project.add_text_simple(
        "Web to Video Intro",
        start_time="0.4s",
        duration="2.4s",
        track_name="TitleTrack",
        anim_in="复古打字机",
    )
    result = project.save()
    print(f"Draft generated: {result.get('draft_path')}")


if __name__ == "__main__":
    main()

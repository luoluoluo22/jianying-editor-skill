import os
import sys

# Standard Boilerplate to load the skill wrapper
# -------------------------------------------------------------
# 必选：这段代码负责自动定位 Skill 路径，请原样复制到你的脚本开头
current_dir = os.path.dirname(os.path.abspath(__file__))
# 扩展探测逻辑：覆盖 Antigravity(.agent), Trae(.trae), Claude(.claude), 以及通用(skills)
skill_candidates = [
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.join(current_dir, ".trae", "skills", "jianying-editor"),
    os.path.join(current_dir, ".claude", "skills", "jianying-editor"),
    os.path.join(current_dir, "skills", "jianying-editor"),
    os.path.join(current_dir, "jianying-editor-skill", ".agent", "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
    # Special case for examples folder (up one level)
    os.path.join(os.path.dirname(current_dir)) 
]
wrapper_path = None
for p in skill_candidates:
    if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
        wrapper_path = os.path.join(p, "scripts")
        skill_root = p
        break

if wrapper_path and wrapper_path not in sys.path:
    sys.path.insert(0, wrapper_path)

try:
    from jy_wrapper import JyProject
except ImportError:
    # 这一步是为了在找不到路径时给出明确提示，方便调试
    print("❌ Critical Error: Could not load 'jy_wrapper'. Check skill paths.")
    sys.exit(1)
# -------------------------------------------------------------

def main():
    # 1. 定义资源路径
    assets_dir = os.path.join(skill_root, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    audio_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path):
        print(f"⚠️ Video not found: {video_path}")
        return

    # 2. 初始化项目
    # 我们将项目命名为 "My_First_Vlog"
    print("🎬 初始化剪映项目: My_First_Vlog")
    project = JyProject(project_name="My_First_Vlog", overwrite=True)

    # 4. 添加背景音乐
    if audio_path and os.path.exists(audio_path):
        print("🎵 添加背景音乐...")
        project.add_media_safe(audio_path, start_time=0, track_name="Audio")

    # 5. 添加标题
    print("📝 添加复古打字机标题...")
    project.add_text_simple(
        text="我的第一支 Vlog",
        start_time=0,
        duration="3s",
        font_size=15.0,
        color_rgb=(1, 1, 1),
        transform_y=-0.5,
        anim_in="复古打字机"
    )

    # 6. 保存
    print("💾 保存项目...")
    project.save()
    print("\n✅ 成功！请打开剪映查看 'My_First_Vlog' 草稿。")

if __name__ == "__main__":
    main()

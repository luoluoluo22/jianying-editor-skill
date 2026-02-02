
import os
import sys

# --- 环境自适应 Boilerplate (Start) ---
# 自动寻找 jy_wrapper.py 所在目录并加入 path
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(current_dir) # 假设在 examples/
script_dir = os.path.join(skill_root, "scripts")

# 如果不在 examples 里，尝试更广泛的搜索
if not os.path.exists(os.path.join(script_dir, "jy_wrapper.py")):
    # 尝试常见的 skill 安装路径
    candidates = [
        os.path.join(current_dir, "scripts"),
        os.path.join(current_dir, "..", "scripts"),
        os.path.join(current_dir, ".agent", "skills", "jianying-editor", "scripts"),
        r"F:\Desktop\kaifa\jianying-editor-skill\.agent\skills\jianying-editor\scripts"
    ]
    for p in candidates:
        if os.path.exists(os.path.join(p, "jy_wrapper.py")):
            script_dir = p
            break

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from jy_wrapper import JyProject
except ImportError:
    print("❌ Critical Error: Could not import JyProject.")
    sys.exit(1)
# --- 环境自适应 Boilerplate (End) ---

def main():
    # 1. 定义资源路径
    # 注意：在实际运行中，请确保这些路径存在
    assets_dir = os.path.join(skill_root, "assets", "readme_assets", "tutorial")
    video_path = os.path.join(assets_dir, "video.mp4")
    audio_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path):
        print(f"⚠️ Video not found: {video_path}")
        return

    # 2. 初始化项目
    # 我们将项目命名为 "My_First_Vlog"
    print("🎬 初始化剪映项目: My_First_Vlog")
    project = JyProject(project_name="My_First_Vlog", overwrite=True)

    # 3. 导入视频
    print("📥 导入主视频...")
    project.add_media_safe(video_path, start_time=0)

    # 4. 导入背景音乐
    # track_name="Audio" 会将其放入音频轨道
    print("🎵 添加背景音乐...")
    project.add_media_safe(audio_path, start_time=0, track_name="Audio")

    # 5. 添加带特效的标题
    # anim_in="复古打字机": 利用 jy_wrapper 的增强查找功能，直接使用中文名
    print("📝 添加复古打字机标题...")
    project.add_text_simple(
        text="我的第一支 Vlog",
        start_time=0,          # 从视频开始
        duration="3s",         # 持续3秒
        font_size=15.0,        # 字体稍微大一点
        color_rgb=(1, 1, 1),   # 白色
        transform_y=-0.5,      # 稍微靠下一点
        anim_in="复古打字机"     # ✨ 关键点：直接传中文特效名
    )

    # 6. 保存
    print("💾 保存项目...")
    project.save()
    print("\n✅ 成功！请打开剪映查看 'My_First_Vlog' 草稿。")

if __name__ == "__main__":
    main()

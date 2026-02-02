
import os
import sys

# ==============================================================================
# 🚀 JianYing Skill Boilerplate (环境初始化标准代码)
# ==============================================================================
# 这一段代码负责让 Python 脚本能找到 jianying-editor skill 的核心库
# 请在你的所有脚本中保留这段代码
current_dir = os.path.dirname(os.path.abspath(__file__))
# 向上寻找 skill 根目录，直到找到 scripts 文件夹
skill_root = os.path.dirname(current_dir) # 假设本文件在 examples/ 下
jy_script_path = os.path.join(skill_root, "scripts")

# 如果找不到，尝试更广泛的探测（兼容直接运行的情况）
if not os.path.exists(os.path.join(jy_script_path, "jy_wrapper.py")):
    candidates = [
        os.path.abspath(os.path.join(current_dir, "..", ".agent", "skills", "jianying-editor", "scripts")),
        os.path.abspath(os.path.join(current_dir, "..", "scripts")),
        r"F:\Desktop\kaifa\jianying-editor-skill\.agent\skills\jianying-editor\scripts" # 本地开发绝对路径兜底
    ]
    for p in candidates:
        if os.path.exists(os.path.join(p, "jy_wrapper.py")):
            jy_script_path = p
            break

if jy_script_path not in sys.path:
    sys.path.insert(0, jy_script_path)

try:
    from jy_wrapper import JyProject
    print(f"✅ Successfully loaded JyProject from: {jy_script_path}")
except ImportError as e:
    print(f"❌ Critical Error: Failed to import JyProject. Path: {jy_script_path}")
    print(f"Error details: {e}")
    sys.exit(1)

# ==============================================================================
# 🎬 简单剪辑示例 (Simple Clip Demo)
# ==============================================================================

def main():
    # 1. 初始化项目
    # project_name: 剪映草稿的名字
    # overwrite=True: 如果项目已存在，允许覆盖（谨慎使用）
    project = JyProject(project_name="Hello_JianYing_V3", overwrite=True)
    
    # 2. 准备素材路径 (这里使用 Skill 自带的测试素材)
    assets_dir = os.path.join(skill_root, "assets", "readme_assets", "tutorial")
    video_path = os.path.join(assets_dir, "video.mp4")
    bgm_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path):
        print(f"⚠️ Demo assets not found at {assets_dir}, using placeholders.")
        # 如果你运行此脚本时没有这些文件，请替换为你本地的真实路径
        return

    # 3. 添加主视频轨道
    # add_media_safe 会自动识别文件类型
    print("📥 Importing Video...")
    project.add_media_safe(video_path, start_time=0, duration="5s")

    # 4. 添加背景音乐
    # track_name="Audio": 指定放入音频轨道
    print("🎵 Adding Music...")
    project.add_media_safe(bgm_path, start_time=0, duration="5s", track_name="Audio")

    # 5. 添加字幕
    # transform_y: 垂直位置，-1.0 是底部，1.0 是顶部，0 是中间
    print("📝 Adding Text...")
    project.add_text_simple("Hello JianYing API!", start_time="1s", duration="3s", 
                           transform_y=-0.7, color_rgb=(1, 1, 0)) # 黄色字幕

    # 6. 保存项目
    # 这会生成草稿文件并自动刷新剪映首页列表
    print("💾 Saving Project...")
    project.save()
    
    print("\n✨ Done! Open JianYing (剪映) and look for 'Hello_JianYing_V3'.")

if __name__ == "__main__":
    main()

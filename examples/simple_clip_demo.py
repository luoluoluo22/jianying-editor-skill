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
        break

if wrapper_path and wrapper_path not in sys.path:
    sys.path.insert(0, wrapper_path)

try:
    from jy_wrapper import JyProject
    print(f"✅ Successfully loaded JyProject from: {wrapper_path}") # Added print for success
except ImportError:
    # 这一步是为了在找不到路径时给出明确提示，方便调试
    print("❌ Critical Error: Could not load 'jy_wrapper'. Check skill paths.")
    sys.exit(1)
# -------------------------------------------------------------

# ==============================================================================
# 🎬 简单剪辑示例 (Simple Clip Demo)
# ==============================================================================

def main():
    # 1. 初始化项目
    # project_name: 剪映草稿的名字
    # overwrite=True: 如果项目已存在，允许覆盖（谨慎使用）
    project = JyProject(project_name="Hello_JianYing_V3", overwrite=True)
    
    # 2. 准备素材路径 (这里使用 Skill 自带的测试素材)
    # wrapper_path是指向 scripts 目录的，它的上一级通常是 skill root
    if 'wrapper_path' in globals() and wrapper_path:
        skill_root = os.path.dirname(wrapper_path)
    else:
        # Fallback if wrapper_path somehow isn't set (shouldn't happen with new boilerplate)
        skill_root = os.path.abspath(os.path.join(current_dir, ".."))
    assets_dir = os.path.join(skill_root, "assets")
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

    # 5. 添加字幕 (带入场动画)
    # transform_y: 垂直位置，-1.0 是底部，1.0 是顶部，0 是中间
    # anim_in: 入场动画。支持直接使用中文名称 (如 "复古打字机", "弹入", "向右滑动")
    # 提示: 你可以使用 `python scripts/asset_search.py "打字"` 来查找可用的动画名
    print("📝 Adding Text with Animation...")
    project.add_text_simple("Hello JianYing API!", start_time="1s", duration="3s", 
                           transform_y=-0.7, color_rgb=(1, 1, 0), # 黄色字幕
                           anim_in="复古打字机") 


    # 6. 保存项目
    # 这会生成草稿文件并自动刷新剪映首页列表
    print("💾 Saving Project...")
    project.save()
    
    print("\n✨ Done! Open JianYing (剪映) and look for 'Hello_JianYing_V3'.")

if __name__ == "__main__":
    main()

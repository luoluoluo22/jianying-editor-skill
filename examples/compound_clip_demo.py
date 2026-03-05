import os
import sys

# 1. 环境初始化 (必须同步到脚本开头)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 探测 Skill 路径 (支持 Antigravity, Trae, Claude 等)
skill_root = next((p for p in [
    os.path.join(current_dir, ".."),
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
] if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py"))), None)

if not skill_root: raise ImportError("Could not find jianying-editor skill root.")
sys.path.insert(0, os.path.join(skill_root, "scripts"))
from jy_wrapper import JyProject

def create_compound_demo():
    """
    演示如何使用复合片段 (Compound Clips) 接口实现工程级嵌套。
    这允许你将复杂的动画或剪辑模组化。
    """
    # 路径配置
    assets_dir = os.path.join(skill_root, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    
    if not os.path.exists(video_path):
        print(f"❌ 找不到演示视频: {video_path}")
        return

    # 1. 创建子工程 (将被打包成复合片段)
    # 子工程内部可以包含多轨道、特效、文字等
    print("🎬 创建子工程 (复合片段内容)...")
    sub_project = JyProject("Sub_Project_Nested")
    sub_project.add_media_safe(video_path, "0s", duration="3s", track_name="SubVideo")
    sub_project.add_text_simple("子工程内部文本", start_time="0.5s", duration="2s", font_size=10)
    
    # 2. 创建主工程
    print("🏗️ 创建主工程...")
    main_project = JyProject("Main_Project_With_Compound")
    
    # 在主工程背景轨道加一段长视频
    main_project.add_media_safe(video_path, "0s", duration="8s", track_name="Background")
    
    # 3. 注入复合片段 (核心接口: add_compound_project)
    # 当前精简版 wrapper 若未暴露该接口，则降级为覆盖层片段，保证示例可跑通。
    print("📦 正在将子工程注入为主视图的复合片段...")
    if hasattr(main_project, "add_compound_project"):
        main_project.add_compound_project(
            sub_project,
            clip_name="我的嵌套模块",
            start_time="2s",
            track_name="Overlay",
        )
    else:
        print("⚠️ 当前 JyProject 未实现 add_compound_project，使用视频覆盖层降级演示。")
        main_project.add_media_safe(video_path, "2s", duration="3s", track_name="Overlay")
        main_project.add_text_simple("复合片段接口未启用，已降级为 Overlay", "2s", "2s", transform_y=0.2)
    
    # 在主工程加个顶部提示
    main_project.add_text_simple(
        "主工程：中间这段是复合片段",
        start_time="0s",
        duration="8s",
        transform_y=0.8,
        track_name="MainTitle",
    )
    
    # 4. 保存主工程
    print("💾 保存主工程...")
    main_project.save()
    print("\n✅ 复合片段示例项目已生成！")
    print("👉 请打开剪映主界面，找到项目: Main_Project_With_Compound")

if __name__ == "__main__":
    create_compound_demo()

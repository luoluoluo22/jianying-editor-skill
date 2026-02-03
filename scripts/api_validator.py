import os
import sys

"""
API Validator for JianYing Editor Skill
用于验证当前环境和 JyProject API 是否能够正常运行。
"""

# 环境初始化
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from jy_wrapper import JyProject
except ImportError:
    print("❌ Failed to load jy_wrapper.")
    sys.exit(1)

def run_diagnostic():
    print("🔍 启动 JianYing Skill 内部诊断...")
    
    skill_root = os.path.dirname(current_dir)
    assets_dir = os.path.join(skill_root, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")

    if not os.path.exists(video_path):
        print(f"⚠️ Warning: Test asset missing at {video_path}")

    try:
        project = JyProject("Diagnostic_Test", overwrite=True)
        # 测试 API V2 的自动追加能力 (不用传时间参数)
        project.add_media_safe(video_path)
        project.add_text_simple("诊断测试: 自动追加正常")
        project.save()
        print("\n✅ API 诊断通过！")
    except Exception as e:
        print(f"\n❌ API 诊断失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_diagnostic()

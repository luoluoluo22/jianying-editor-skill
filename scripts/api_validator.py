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

def check_ffprobe():
    import subprocess
    try:
        res = subprocess.run(["ffprobe", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            print("✅ FFprobe is installed and available in PATH.")
            return True
    except FileNotFoundError:
        print("⚠️ Warning: FFprobe not found in PATH. TS files or missing metadata might fail to resolve duration.")
    return False

def run_diagnostic():
    print("🔍 启动 JianYing Skill 内部综合诊断...")
    
    check_ffprobe()

    skill_root = os.path.dirname(current_dir)
    assets_dir = os.path.join(skill_root, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")

    if not os.path.exists(video_path):
        print(f"⚠️ Warning: Test asset missing at {video_path}")

    try:
        project = JyProject("Diagnostic_Test", overwrite=True)
        # 测试 API V2 的自动追加能力
        seg1 = project.add_media_safe(video_path)
        
        # 测试防呆设计: 重复引用并设置异常长度
        project.add_text_simple("诊断测试: 检查溢出警告")
        if seg1 and hasattr(seg1, 'material_instance') and hasattr(seg1.material_instance, 'duration'):
            dur_us = seg1.material_instance.duration
            print(f"[*] Base video duration is: {dur_us/1000000:.2f}s")
            # 故意传入一个超过上限的时长
            project.add_media_safe(video_path, source_start=0, duration=f"{(dur_us/1000000) + 10}s")
            
        # 测试审计(连续添加5个会导致高频复发警告)
        print("[*] Testing Timeline Audit (should produce warning)...")
        for i in range(6):
            project.add_media_safe(video_path, source_start="0s", duration="1s")
            
        project.save()
        print("\n✅ API 诊断并输出报告通过（请检查上方是否正确输出了 Overflow 和 Audit 警告）！")
    except Exception as e:
        print(f"\n❌ API 诊断失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_diagnostic()



import os
import sys
import cv2
import numpy as np

# 自动定位路径 (Ensure we can find scripts and references)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(os.path.join(project_root, "scripts"))
sys.path.append(os.path.join(project_root, "references"))

from jy_wrapper import JyProject
from pyJianYingDraft import KeyframeProperty as KP

def calculate_video_brightness(video_path):
    """使用 OpenCV 获取视频的平均亮度 (Value in HSV)"""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return 128

    # 转换为 HSV 空间，并计算 V (Value/Brightness) 通道的平均值
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    avg_v = np.mean(hsv[:, :, 2])
    cap.release()
    return avg_v

def run_exposure_alignment_example():
    """
    演示如何自动对齐多段曝光不一的视频素材。
    """
    print("🎬 Starting Auto Exposure Alignment Example...")

    # 1. 准备项目
    project_name = "Auto_Exposure_Alignment_Demo"
    project = JyProject(project_name, overwrite=True)

    # 2. 模拟素材列表 (你可以替换为真实的素材路径)
    # 这里我们演示同一段素材，通过算法计算并“标准化”它的曝光
    video_path = r"F:\Desktop\AI生产-陈桑桑-交付版.mp4"
    if not os.path.exists(video_path):
        print(f"⚠️ Warning: Example video not found at {video_path}")
        return

    # 设定我们的目标“标准亮度”值 (0-255)
    # 128 是中灰，140 左右通常看起来更明快
    TARGET_BRIGHTNESS = 140

    print(f"📂 Processing: {os.path.basename(video_path)}")

    # --- A. 视觉分析 ---
    current_b = calculate_video_brightness(video_path)
    print(f"   -> Current Avg Brightness: {current_b:.2f}")

    # --- B. 计算补偿偏移 ---
    # 剪映 Brightness 范围通常映射为 -1.0 (最暗) 到 1.0 (最亮)
    # 简单的线性映射：(目标 - 当前) / 128
    offset = (TARGET_BRIGHTNESS - current_b) / 128.0
    offset = max(-0.8, min(0.8, offset)) # 限制范围防止过度曝光

    print(f"   -> Target: {TARGET_BRIGHTNESS}, Calculated Offset: {offset:.2f}")

    # --- C. 轨道注入 ---
    seg = project.add_media_safe(video_path, start_time=0)
    if seg:
        # 使用关键帧注入亮度补偿
        # 修改后的 JyProject 会在 save() 时自动补全影子材质和激活链
        seg.add_keyframe(KP.brightness, 0, offset)
        print(f"   -> Exposure keyframe injected.")

    # 3. 保存并自动激活渲染
    # 内部集成了 _force_activate_adjustments，确保在剪映打开时效果立现
    project.save()

    print(f"\n✅ Demo Complete! Open '{project_name}' in JianYing to see the result.")
    print("----------------------------------------------------------------")
    print("Technical Highlights:")
    print(" [x] OpenCV based luminance analysis")
    print(" [x] Automatic Brightness mapping (-1.0 to 1.0)")
    print(" [x] Integrated auto-activation (No manual clicks needed in UI)")

if __name__ == "__main__":
    run_exposure_alignment_example()

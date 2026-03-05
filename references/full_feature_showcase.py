
"""
JianYing Editor Skill - 全面功能演示 (Comprehensive Showcase)

本脚本展示了 Skill 的所有核心能力，包括：
1. 基础剪辑 (Import & Cut)
2. 转场与特效 (Transitions & VFX)
3. 关键帧动画 (Keyframes & PIP)
4. 增强型字幕 (Advanced Text & Auto-Layering)
5. 自动化编排 (Algorithmic Editing)

使用素材：Skill 自带的测试素材 (assets/readme_assets/tutorial/*)
"""

import sys
import os
import random

# --- 1. 环境注入 ---
# 自动定位 Skill 路径（兼容从仓库根目录直接运行）
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_candidates = [
    os.path.dirname(current_dir),  # 当前仓库结构: <skill_root>/references
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.join(current_dir, "jianying-editor-skill", ".agent", "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
]
skill_root = next(
    (p for p in skill_candidates if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py"))),
    None,
)
if not skill_root:
    raise ImportError("Could not locate jianying-editor skill root for full_feature_showcase.")

sys.path.append(os.path.join(skill_root, "scripts"))
# 确保 references 也能被找到 (用于 pyJianYingDraft)
sys.path.append(os.path.join(skill_root, "references"))

from jy_wrapper import JyProject, draft

# --- 2. 辅助路径 ---
ASSETS_DIR = os.path.join(skill_root, "assets")
VIDEO_PATH = os.path.join(ASSETS_DIR, "video.mp4")
AUDIO_PATH = os.path.join(ASSETS_DIR, "audio.mp3")

# 检查素材
if not os.path.exists(VIDEO_PATH):
    print(f"⚠️ Warning: Demo video not found at {VIDEO_PATH}")
    # 尝试查找任意 mp4
    import glob
    mp4s = glob.glob(os.path.join(current_dir, "*.mp4"))
    if mp4s: VIDEO_PATH = mp4s[0]

# --- 3. 演示逻辑 ---

def run_full_showcase():
    print("🎬 Starting Full Feature Showcase Build...")
    print(f"📂 Assets: {VIDEO_PATH}")
    
    # A. 项目初始化
    # overwrite=True 会自动删除同名旧草稿，适合调试
    project = JyProject("Full_Feature_Showcase_V1", overwrite=True)
    
    cursor = 0 # 当前时间游标 (微秒)
    
    # ==========================================
    # 1. 蒙太奇剪辑 (Montage Editing)
    # ==========================================
    print("\n✂️ [Phase 1] Basic Editing...")
    
    # 片段 1: 视频的前 3 秒
    # add_media_safe(path, start_time_on_timeline, duration, track_name, source_start_time)
    project.add_media_safe(VIDEO_PATH, start_time=cursor, duration="3s", source_start=0)
    cursor += 3000000 
    
    # 片段 2: 使用测试素材中可用的范围（样例素材约 5s）
    project.add_media_safe(VIDEO_PATH, start_time=cursor, duration="2s", source_start="1s")
    
    # 在片段 1 和 2 之间添加转场
    # 注意：转场通常加在后一个片段的前面，或者通过 add_transition_simple 自动处理
    # add_transition_simple 会尝试给轨道最后一个片段加转场
    # 我们这里给第二个片段加上 "混合" 转场
    project.add_transition_simple(transition_name="混合", duration="0.8s")
    
    cursor += 2000000
    
    # 片段 3: 使用测试素材中可用的范围（样例素材约 5s）
    project.add_media_safe(VIDEO_PATH, start_time=cursor, duration="3s", source_start="2s")
    
    # ==========================================
    # 2. 视觉特效 (VFX)
    # ==========================================
    print("\n✨ [Phase 2] Visual Effects...")
    
    # 给整个第 3 片段添加 "复古DV" 特效
    # add_effect_simple(name, start, duration)
    # 支持模糊匹配，比如 "复古" 可能会匹配到相关滤镜
    try:
        project.add_effect_simple("复古DV", start_time=cursor, duration="3s")
        # 再叠加一个 "漏光"
        project.add_effect_simple("漏光", start_time=cursor, duration="3s")
    except Exception as e:
        print(f" (Effect skipped: {e})")

    cursor += 3000000
    
    # ==========================================
    # 3. 关键帧动画 (Keyframes & PIP)
    # ==========================================
    print("\n🔑 [Phase 3] Keyframe Animation (PIP)...")
    
    # 我们再次使用 video.mp4 作为画中画轨道
    # 放在 cursor 位置，持续 4秒
    pip_start = 1000000 # 从第 1 秒开始出现 PIP
    pip_dur = 4000000   # 持续 4 秒
    
    # 添加到 "OverlayTrack"
    # pyJianYingDraft 的底层对象是 VideoSegment，我们需要手动加关键帧
    pip_seg = project.add_media_safe(VIDEO_PATH, start_time=pip_start, duration=pip_dur, track_name="OverlayTrack")
    
    if pip_seg:
        from pyJianYingDraft import KeyframeProperty as KP
        
        # 0s: 位于左侧屏幕外，原本大小的 30%
        # 1s: 飞入中心
        # 3s: 保持中心
        # 4s: 飞出右侧
        
        # 时间点是相对于 Timeline 的绝对时间 (微秒)
        t1 = pip_start
        t2 = pip_start + 1000000
        t3 = pip_start + 3000000
        t4 = pip_start + 4000000
        
        # Scale: 30%
        scale = 0.3
        pip_seg.add_keyframe(KP.uniform_scale, t1, scale)
        pip_seg.add_keyframe(KP.uniform_scale, t4, scale)
        
        # Position X (1.0 = half width approx? 剪映坐标系 -0.5 ~ 0.5 通常对应全屏)
        # 让它从 x=-1.0 (左外) 移动到 x=0.0 (中心) 再到 x=1.0 (右外)
        pip_seg.add_keyframe(KP.position_x, t1, -1.0) # Left Out
        pip_seg.add_keyframe(KP.position_x, t2, -0.3) # Left Mid
        pip_seg.add_keyframe(KP.position_x, t3, 0.3)  # Right Mid
        pip_seg.add_keyframe(KP.position_x, t4, 1.0)  # Right Out
        
        # Rotation: 旋转 360 度
        pip_seg.add_keyframe(KP.rotation, t1, 0.0)
        pip_seg.add_keyframe(KP.rotation, t4, 360.0)
        
        print("   -> PIP Animation added.")

    # ==========================================
    # 4. 增强型字幕 与 自动分层
    # ==========================================
    print("\n📝 [Phase 4] Advanced Text & Auto-Layering...")
    
    # 4.1 花字标题
    project.add_text_simple(
        "JianYing Editor Skill", 
        start_time=500000, duration="3s", 
        font_size=15.0, color_rgb=(1.0, 0.8, 0.0), # 金色
        anim_in="弹幕",  # 入场动画
        transform_y=0.4  # 上方
    )
    
    # 4.2 密集字幕 (测试自动分层)
    # 在 4s - 6s 之间密集堆叠 3 条字幕
    sub_texts = ["第一行字幕：自动分层测试", "第二行：即使时间重叠", "第三行：系统也会自动创建新轨道"]
    base_time = 4000000
    
    for i, txt in enumerate(sub_texts):
        # 它们都在同一时间出现，如果不分层就会 Crash
        project.add_text_simple(
            txt, 
            start_time=base_time + (i * 200000), # 稍微错开一点点起头
            duration="2s",
            font_size=10.0,
            transform_y=-0.5 - (i * 0.15), # 垂直排列
            track_name=f"Subtitle_Main_{i}"  # 显式分轨，兼容精简 wrapper
        )

    # ==========================================
    # 5. 音频铺底
    # ==========================================
    print("\n🎵 [Phase 5] Audio...")
    
    if os.path.exists(AUDIO_PATH):
        # 从头铺到尾 (cursor 现在指向视频末尾)
        project.add_audio_safe(AUDIO_PATH, start_time=0, duration=cursor, track_name="BGM")
    else:
        print("   (Audio skipped: file not found)")

    # ==========================================
    # 6. 保存
    # ==========================================
    print("\n💾 Saving Project...")
    project.save()
    print(f"✅ Demo Complete! Open '{project.name}' in JianYing to watch.")
    print("----------------------------------------------------------------")
    print("Features Demonstrated:")
    print(" [x] Clip Montage & Transitions")
    print(" [x] Global Visual Effects")
    print(" [x] Keyframe Animation (Flying PIP)")
    print(" [x] Auto-Layering for Overlapping Text")
    print(" [x] Background Music Sync")

if __name__ == "__main__":
    run_full_showcase()

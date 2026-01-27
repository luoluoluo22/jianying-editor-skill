
import json
import os
import sys
from .jy_wrapper import JyProject
import pyJianYingDraft as draft

def apply_smart_zoom(project: JyProject, video_segment, events_json_path: str, zoom_scale=150, zoom_duration_us=500000):
    """
    根据记录的 events.json 自动为视频片段添加缩放关键帧 (类似产品演示效果)
    
    Args:
        project: JyProject 实例
        video_segment: 要应用缩放的视频片段对象
        events_json_path: 录制时生成的 _events.json 路径
        zoom_scale: 缩放比例 (%)
        zoom_duration_us: 缩放动画持续时间 (微秒), 默认 0.5s
    """
    if not os.path.exists(events_json_path):
        print(f"❌ Events file not found: {events_json_path}")
        return

    with open(events_json_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    # 提取点击事件
    click_events = [e for e in events if e['type'] == 'click']
    if not click_events:
        print("ℹ️ No click events found in JSON.")
        return

    print(f"🎯 Found {len(click_events)} click events. Applying smart zoom keyframes...")
    
    # 提取所有移动事件供后续查询
    move_events = [e for e in events if e.get('type') == 'move']
    
    # 将点击事件分组 (Session-based)
    grouped_events = []
    if click_events:
        current_group = [click_events[0]]
        for i in range(1, len(click_events)):
            prev_time = click_events[i-1]['time']
            curr_time = click_events[i]['time']
            if (curr_time - prev_time) <= 3.0:
                current_group.append(click_events[i])
            else:
                grouped_events.append(current_group)
                current_group = [click_events[i]]
        grouped_events.append(current_group)

    print(f"🔄 Grouped into {len(grouped_events)} zoom sessions.")

    from pyJianYingDraft.keyframe import KeyframeProperty as KP
    import os

    # 准备红点素材路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(current_dir)
    marker_path = os.path.join(skill_root, "assets", "click_marker.png")
    
    # 缩放参数
    scale_val = float(zoom_scale) / 100.0
    ZOOM_IN_US = 300000    # 0.3s
    HOLD_US = 3000000      # 3.0s
    ZOOM_OUT_US = 600000   # 0.6s
    
    # 视口边界 (相对于归一化坐标中心 0.5, 0.5)
    # 实际可视宽度 = 1.0 / scale
    viewport_half_w = (1.0 / scale_val) / 2.0
    viewport_half_h = (1.0 / scale_val) / 2.0

    for group in grouped_events:
        # --- 1. Start Phase (整体进场) ---
        first_event = group[0]
        t0_us = int(first_event['time'] * 1000000)
        t_start = max(0, t0_us - ZOOM_IN_US)
        
        video_segment.add_keyframe(KP.uniform_scale, t_start, 1.0)
        video_segment.add_keyframe(KP.position_x, t_start, 0.0)
        video_segment.add_keyframe(KP.position_y, t_start, 0.0)
        
        # 记录当前的摄像机中心 (归一化坐标)
        current_cam_x = first_event['x']
        current_cam_y = first_event['y']

        # 遍历组内每个点击事件，以及点击之间的 Move 事件
        for i, event in enumerate(group):
            t_curr_us = int(event['time'] * 1000000)
            
            # --- A. 添加红点标记 (Sticker) ---
            if os.path.exists(marker_path):
                try:
                    # 添加贴纸到新轨道，时长 0.5s
                    # 位置永远在屏幕中心 (0,0)，因为点击时刻画面会对焦到鼠标
                    # 注意：贴纸不需要缩放，保持默认大小即可
                    project.add_sticker_at(marker_path, t_curr_us, 500000) 
                except AttributeError:
                    # 如果 project 没实现 add_sticker_at，尝试 generic add_media
                     pass

            # --- B. 处理点击本身的关键帧 ---
            # 目标：将本次点击位置置于中心
            target_x = (event['x'] - 0.5) * 2
            target_y = (0.5 - event['y']) * 2
            pos_x = -target_x * scale_val
            pos_y = -target_y * scale_val
            
            # 更新摄像机中心
            current_cam_x = event['x']
            current_cam_y = event['y']

            if i == 0:
                # 第一帧：直接变焦
                video_segment.add_keyframe(KP.uniform_scale, t_curr_us, scale_val)
                video_segment.add_keyframe(KP.position_x, t_curr_us, pos_x)
                video_segment.add_keyframe(KP.position_y, t_curr_us, pos_y)
            else:
                # 后续帧：处理与上一次点击之间的 Move 事件 (Smart Follow)
                prev_event = group[i-1]
                t_prev_us = int(prev_event['time'] * 1000000)
                
                # 找出夹在 t_prev 和 t_curr 之间的 move events
                interval_moves = [m for m in move_events if prev_event['time'] < m['time'] < event['time']]
                
                # 遍历中间的 move，检查是否移出视口
                for m in interval_moves:
                    t_m_us = int(m['time'] * 1000000)
                    
                    # 检查 m 点是否在当前 cam 视口内
                    is_out_x = abs(m['x'] - current_cam_x) > (viewport_half_w * 0.9) # 留10%余量
                    is_out_y = abs(m['y'] - current_cam_y) > (viewport_half_h * 0.9)
                    
                    if is_out_x or is_out_y:
                        # 触发跟随：将摄像机移动到该 move 点
                        m_tx = (m['x'] - 0.5) * 2
                        m_ty = (0.5 - m['y']) * 2
                        m_pos_x = -m_tx * scale_val
                        m_pos_y = -m_ty * scale_val
                        
                        video_segment.add_keyframe(KP.position_x, t_m_us, m_pos_x)
                        video_segment.add_keyframe(KP.position_y, t_m_us, m_pos_y)
                        
                        # 更新当前 cam
                        current_cam_x = m['x']
                        current_cam_y = m['y']

                # 最后确保在该 click 时刻对齐
                video_segment.add_keyframe(KP.uniform_scale, t_curr_us, scale_val)
                video_segment.add_keyframe(KP.position_x, t_curr_us, pos_x)
                video_segment.add_keyframe(KP.position_y, t_curr_us, pos_y)

        # --- 3. End Phase (动态延长停留期) ---
        last_event = group[-1]
        
        # 初始截止时间 = 最后一次点击 + 3s
        last_activity_time = last_event['time']
        
        # 筛选出最后一次点击之后的所有移动事件
        potential_moves = [m for m in move_events if m['time'] > last_activity_time]
        
        valid_post_moves = []
        for m in potential_moves:
            # 如果该移动发生在当前倒计时窗口内 (距离上一次活动 <= 3s)
            # 则“续费” 3s，更新最后活动时间
            if m['time'] - last_activity_time <= 3.0:
                last_activity_time = m['time']
                valid_post_moves.append(m)
            else:
                # 一旦断档超过 3s，则认为操作结束
                break
        
        # 处理这些延长期的移动跟随
        for m in valid_post_moves:
             t_m_us = int(m['time'] * 1000000)
             
             is_out_x = abs(m['x'] - current_cam_x) > (viewport_half_w * 0.9)
             is_out_y = abs(m['y'] - current_cam_y) > (viewport_half_h * 0.9)
             
             if is_out_x or is_out_y:
                # 触发跟随
                m_tx = (m['x'] - 0.5) * 2
                m_ty = (0.5 - m['y']) * 2
                m_pos_x = -m_tx * scale_val
                m_pos_y = -m_ty * scale_val
                
                video_segment.add_keyframe(KP.position_x, t_m_us, m_pos_x)
                video_segment.add_keyframe(KP.position_y, t_m_us, m_pos_y)
                
                current_cam_x = m['x']
                current_cam_y = m['y']

        # 最终结束时间 = (最后一个有效活动的时刻) + 3s
        # 或者是: last_activity_time 已经是最后一个活动了，那么倒计时是不是指“静止 3s 后退出”？
        # "默认3s不缩放，期间...再次倒计时" -> 意味着 Zoom Out 发生在 last_activity_time + 3s
        
        t_hold_end = int((last_activity_time + 3.0) * 1000000)
        
        # 获取最后时刻的各种变量用于保持状态
        # 注意: 这里的 current_cam_x 已经被上面的循环更新到最新了
        final_pos_x = -((current_cam_x - 0.5) * 2) * scale_val
        final_pos_y = -((current_cam_y - 0.5) * 2) * scale_val

        # 添加 Hold 结束帧
        video_segment.add_keyframe(KP.uniform_scale, t_hold_end, scale_val)
        video_segment.add_keyframe(KP.position_x, t_hold_end, final_pos_x)
        video_segment.add_keyframe(KP.position_y, t_hold_end, final_pos_y)

        # 恢复全景
        t_restore = t_hold_end + ZOOM_OUT_US
        video_segment.add_keyframe(KP.uniform_scale, t_restore, 1.0)
        video_segment.add_keyframe(KP.position_x, t_restore, 0.0)
        video_segment.add_keyframe(KP.position_y, t_restore, 0.0)

    print("✅ Smart zoom keyframes applied successfully.")

if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) < 3:
        print("Usage: python smart_zoomer.py <project_name> <video_path> <events_json>")
        sys.exit(1)
        
    proj_name = sys.argv[1]
    video_path = sys.argv[2]
    json_path = sys.argv[3]
    
    p = JyProject(proj_name)
    seg = p.add_media_safe(video_path, "0s")
    apply_smart_zoom(p, seg, json_path)
    p.save()

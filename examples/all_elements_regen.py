import os
import sys


def _locate_skill_root() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.dirname(current_dir),  # repo root
        os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
        os.path.abspath(".agent/skills/jianying-editor"),
    ]
    for p in candidates:
        if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
            return p
    raise RuntimeError("Could not locate skill root.")


def main() -> None:
    skill_root = _locate_skill_root()
    scripts_dir = os.path.join(skill_root, "scripts")
    refs_dir = os.path.join(skill_root, "references")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if refs_dir not in sys.path:
        sys.path.insert(0, refs_dir)

    from jy_wrapper import JyProject
    from pyJianYingDraft import KeyframeProperty as KP

    assets_dir = os.path.join(skill_root, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    audio_path = os.path.join(assets_dir, "audio.mp3")
    html_path = os.path.join(skill_root, "index.html")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Missing demo video: {video_path}")

    project = JyProject("All_Elements_Regen_V1", overwrite=True)

    # 1) Video montage
    seg1 = project.add_media_safe(video_path, start_time="0s", duration="2s", track_name="VideoMain", source_start="0s")
    seg2 = project.add_media_safe(video_path, start_time="2s", duration="2s", track_name="VideoMain", source_start="1s")
    seg3 = project.add_media_safe(video_path, start_time="4s", duration="1s", track_name="VideoMain", source_start="3s")

    # 2) Transition
    if seg2 is not None:
        project.add_transition_simple("混合", video_segment=seg2, duration="0.5s")
    if seg3 is not None:
        project.add_transition_simple("黑场", video_segment=seg3, duration="0.3s")

    # 3) Optional effect (some pyJianYingDraft builds may not support EffectMaterial)
    try:
        project.add_effect_simple("复古", start_time="1s", duration="2s", track_name="FxTrack")
    except Exception as e:
        print(f"[skip] add_effect_simple unavailable: {e}")

    # 4) Keyframe PIP
    pip_seg = project.add_media_safe(video_path, start_time="0.5s", duration="3s", track_name="OverlayPIP", source_start="0.5s")
    if pip_seg is not None:
        pip_seg.add_keyframe(KP.uniform_scale, 500000, 0.35)
        pip_seg.add_keyframe(KP.uniform_scale, 2500000, 0.45)
        pip_seg.add_keyframe(KP.position_x, 500000, -0.8)
        pip_seg.add_keyframe(KP.position_x, 2500000, 0.8)
        pip_seg.add_keyframe(KP.rotation, 500000, 0.0)
        pip_seg.add_keyframe(KP.rotation, 2500000, 30.0)

    # 5) Text layers / animations
    project.add_text_simple(
        "全元素测试草稿",
        start_time="0.2s",
        duration="2.2s",
        track_name="TitleTrack",
        anim_in="复古打字机",
        anim_out="淡出",
    )
    project.add_text_simple(
        "视频+转场+关键帧+音频",
        start_time="2.6s",
        duration="2s",
        track_name="SubTrackA",
        anim_in="向右滑动",
    )
    project.add_text_simple(
        "可选能力: 网页动效/TTS/云素材",
        start_time="4.1s",
        duration="0.8s",
        track_name="SubTrackB",
    )

    # 6) Audio bed aligned with timeline (avoid long tail)
    if os.path.exists(audio_path):
        project.add_media_safe(audio_path, start_time="0s", duration="5s", track_name="BGM")

    # 7) Optional Web asset
    if os.path.exists(html_path):
        try:
            project.add_web_asset_safe(html_path, start_time="1s", duration="2s", track_name="WebTrack")
        except Exception as e:
            print(f"[skip] add_web_asset_safe failed: {e}")

    # 8) Optional TTS + subtitles
    try:
        project.add_narrated_subtitles("这是一次重新生成的全元素测试。", start_time="0.2s", track_name="NarrationSub")
    except Exception as e:
        print(f"[skip] add_narrated_subtitles failed: {e}")

    # 9) Optional cloud asset
    try:
        project.add_cloud_media("科技", start_time="3s", duration="1s", track_name="CloudTrack")
    except Exception as e:
        print(f"[skip] add_cloud_media failed: {e}")

    result = project.save()
    print(f"Draft generated: {result.get('draft_path')}")


if __name__ == "__main__":
    main()


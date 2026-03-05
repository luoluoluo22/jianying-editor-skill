import os

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject
from pyJianYingDraft import KeyframeProperty as KP


def main() -> None:
    assets_dir = os.path.join(SKILL_ROOT, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    audio_path = os.path.join(assets_dir, "audio.mp3")
    html_path = os.path.join(SKILL_ROOT, "index.html")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Missing demo video: {video_path}")

    project = JyProject("All_Elements_Regen_V1", overwrite=True)

    seg2 = project.add_media_safe(
        video_path, start_time="2s", duration="2s", track_name="VideoMain", source_start="1s"
    )
    seg3 = project.add_media_safe(
        video_path, start_time="4s", duration="1s", track_name="VideoMain", source_start="3s"
    )
    project.add_media_safe(video_path, start_time="0s", duration="2s", track_name="VideoMain", source_start="0s")

    if seg2 is not None:
        project.add_transition_simple("混合", video_segment=seg2, duration="0.5s")
    if seg3 is not None:
        project.add_transition_simple("黑场", video_segment=seg3, duration="0.3s")

    pip_seg = project.add_media_safe(
        video_path, start_time="0.5s", duration="3s", track_name="OverlayPIP", source_start="0.5s"
    )
    if pip_seg is not None:
        pip_seg.add_keyframe(KP.uniform_scale, 500000, 0.35)
        pip_seg.add_keyframe(KP.uniform_scale, 2500000, 0.45)
        pip_seg.add_keyframe(KP.position_x, 500000, -0.8)
        pip_seg.add_keyframe(KP.position_x, 2500000, 0.8)

    project.add_text_simple(
        "All Elements Demo",
        start_time="0.2s",
        duration="2.2s",
        track_name="TitleTrack",
        anim_in="复古打字机",
        anim_out="淡出",
    )

    if os.path.exists(audio_path):
        project.add_audio_safe(audio_path, start_time="0s", duration="5s", track_name="BGM")

    if os.path.exists(html_path):
        try:
            project.add_web_asset_safe(html_path, start_time="1s", duration="2s", track_name="WebTrack")
        except Exception as exc:
            print(f"[skip] add_web_asset_safe failed: {exc}")

    result = project.save()
    print(f"Draft generated: {result.get('draft_path')}")


if __name__ == "__main__":
    main()

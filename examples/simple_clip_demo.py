import os
import sys

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, WRAPPER_PATH = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


def main() -> None:
    project = JyProject(project_name="Hello_JianYing_V3", overwrite=True)

    assets_dir = os.path.join(SKILL_ROOT, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    bgm_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path) or not os.path.exists(bgm_path):
        print(f"Demo assets not found: {assets_dir}")
        return

    print("Importing video...")
    project.add_media_safe(video_path, start_time="0s", duration="5s", track_name="VideoTrack")

    print("Adding bgm...")
    project.add_media_safe(bgm_path, start_time="0s", duration="5s", track_name="AudioTrack")

    print("Adding text...")
    # Keep text clips non-overlapping on the same text track to avoid SegmentOverlap.
    project.add_text_simple("Hello JianYing API!", start_time="1s", duration="1.6s", anim_in="复古打字机")
    project.add_text_simple("Simple Clip Demo", start_time="2.7s", duration="1.6s", anim_in="向右滑动")

    print("Saving project...")
    project.save()
    print("Done. Open JianYing and find draft: Hello_JianYing_V3")


if __name__ == "__main__":
    main()

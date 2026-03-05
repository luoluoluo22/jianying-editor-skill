import os

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


def main() -> None:
    assets_dir = os.path.join(SKILL_ROOT, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    audio_path = os.path.join(assets_dir, "audio.mp3")

    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return

    print("Creating project: My_First_Vlog")
    project = JyProject(project_name="My_First_Vlog", overwrite=True)

    project.add_media_safe(video_path, start_time="0s", duration="5s", track_name="VideoTrack")

    if os.path.exists(audio_path):
        print("Adding background music...")
        project.add_audio_safe(audio_path, start_time="0s", duration="5s", track_name="AudioTrack")

    print("Adding title text...")
    project.add_text_simple(
        text="My First Vlog",
        start_time="0.3s",
        duration="2.8s",
        font_size=15.0,
        color_rgb=(1, 1, 1),
        transform_y=-0.5,
        anim_in="复古打字机",
        track_name="TitleTrack",
    )

    print("Saving project...")
    project.save()
    print("Done. Open JianYing and find draft: My_First_Vlog")


if __name__ == "__main__":
    main()
